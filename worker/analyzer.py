import csv
import json
import logging
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.signal import find_peaks, peak_widths
import sys
from nmr_reader import NMRDataReader, is_nmrglue_available


# Añadir ruta al backend para imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from pfas_detector_enhanced import PFASDetectorEnhanced
from nmr_constants import (
    F19Config,
    calculate_nucleus_frequency,
    ppm_to_hz,
    hz_to_ppm,
    calculate_linewidth_tolerance
)


class SpectrumAnalyzer:
    """
    Analizador mejorado v2.3 de espectros RMN para detección de PFAS
    """
    
    def __init__(self, spectrometer_h1_freq_mhz: float = 500.0):
        """
        Inicializa el analizador.
        """
        self.nmr_reader = NMRDataReader()
        self.file_metadata = {}
        self.ppm_data = np.array([])
        self.intensity_data = np.array([])
        self.intensity_corrected = np.array([])
        self.baseline_value = None
        self.analysis_results = {}

        # Verificar disponibilidad de nmrglue
        if is_nmrglue_available():
            print("   ✅ nmrglue disponible - Soporte FID activado")
            print("      Formatos: Bruker, Varian, JEOL, NMRPipe, CSV")
        else:
            print("   ⚠️  nmrglue no disponible - Solo soporte CSV")
            print("      Instalar con: pip install nmrglue")
            
        # Configuración de frecuencias
        self.spectrometer_h1_freq = spectrometer_h1_freq_mhz
        self.f19_frequency = calculate_nucleus_frequency(spectrometer_h1_freq_mhz, '19F')
        
        self.pfas_detector = PFASDetectorEnhanced(
            nucleus_frequency_mhz=self.f19_frequency
        )
        
        print(f"   🧲 Espectrómetro configurado:")
        print(f"      1H: {self.spectrometer_h1_freq:.1f} MHz")
        print(f"      19F: {self.f19_frequency:.1f} MHz (calculado según Levitt Ec. 2.15)")

        # Mapa de regiones para etiquetado de picos (VERSIÓN CORREGIDA)
        self.PEAK_REGIONS_MAP = {
            'CF3': (-85, -78),
            'SO3H-alpha': (-117, -113),
            'COOH-alpha': (-120, -117),
            'Fluorotelomer-CH2': (-128, -125),
            'Ether-CF': (-150, -140),
            'Internal-CF2': (-180, -120.1), 
        }

    def _get_peak_region(self, ppm: float) -> str:
        """Helper para asignar una región a un pico basado en su PPM. (Lógica corregida)"""
        
        # 1. Buscar primero en los rangos específicos
        specific_regions = {
            'CF3': (-85, -78),
            'SO3H-alpha': (-117, -113),
            'COOH-alpha': (-120, -117),
            'Fluorotelomer-CH2': (-128, -125),
            'Ether-CF': (-150, -140),
        }
        
        for name, (start, end) in specific_regions.items():
            if start <= ppm <= end:
                return name
        
        # 2. Si no es específico, buscar en rangos generales
        if -180 <= ppm < -120:
             return "Internal-CF2"

        if ppm > -78:
            return "Other"
            
        return "Unknown"

    def analyze_file(self, file_path: Path, 
                     fluor_range: Dict = None,
                     pifas_range: Dict = None,
                     concentration: float = 1.0,
                     baseline_correction: bool = True,
                     baseline_method: str = 'polynomial') -> Dict:
        """
        Analiza un archivo de espectro RMN (Versión corregida para JSON y datos aplanados)
        """
        # Configuración por defecto
        if fluor_range is None:
            fluor_range = {"min": -150, "max": -50}
        if pifas_range is None:
            pifas_range = {"min": -130, "max": -60}
        
        print(f"\n{'='*70}")
        print(f"📊 ANALIZANDO: {file_path.name}")
        print(f"{'='*70}")
        print(f"   Rango Flúor Total: {fluor_range['min']} a {fluor_range['max']} ppm")
        print(f"   Rango PFAS/PIFAS:  {pifas_range['min']} a {pifas_range['max']} ppm")
        print(f"   Concentración:     {concentration} mM")
        
        self._read_spectrum(file_path)

        if len(self.ppm_data) < 2:
            return {"error": "No hay datos suficientes en el archivo"}
        
        print(f"\n   ✅ Datos cargados: {len(self.ppm_data)} puntos")
        print(f"   Rango ppm: {min(self.ppm_data):.2f} a {max(self.ppm_data):.2f}")
        
        if baseline_correction:
            if baseline_method == 'polynomial':
                self._correct_baseline_polynomial()
                print(f"   ✅ Baseline corregido (polynomial)")
            else:
                self._correct_baseline()
                print(f"   ✅ Baseline corregido (simple)")
        else:
            self.intensity_corrected = self.intensity_data.copy()
            self.baseline_value = 0.0
        
        # 1. Calcular métricas de calidad PRIMERO para obtener el noise_level
        quality_metrics = self._calculate_quality_metrics()
        
        # 2. Analizar regiones
        fluor_total_stats = self._analyze_region(
            fluor_range['min'], fluor_range['max']
        )
        pifas_stats = self._analyze_region(
            pifas_range['min'], pifas_range['max']
        )
        
        # 3. Detectar picos PASANDO el noise_level global
        peaks = self._detect_peaks_advanced(
            pifas_range['min'], pifas_range['max'],
            global_noise_level=quality_metrics.get('noise_level', 1e-9),
            max_signal_intensity=quality_metrics.get('max_signal', 1.0)
        )

        # --- Calcular concentraciones ---
        total_area = fluor_total_stats.get('total_area', 1)  # Evitar división por cero
        pifas_area = pifas_stats.get('total_area', 0)

        pifas_fraction = pifas_area / total_area if total_area != 0 else 0.0
        pifas_concentration = float(concentration * pifas_fraction)
        pfas_concentration = float(concentration * pifas_fraction)  # alias

        
        # Resultados (VERSIÓN APLANADA Y CON .tolist() PARA JSON)
        results = {
            # --- Datos del Espectro (PARA EL GRÁFICO) ---
            "spectrum": {
                "ppm": self.ppm_data.tolist(),  # <-- CONVERTIDO A LISTA
                "intensity": self.intensity_corrected.tolist()  # <-- CONVERTIDO A LISTA
            },
            
            # --- Info Básica ---
            "file_name": file_path.name,
            "filename": file_path.name, # Alias
            "concentration": float(concentration), # Convertido a float
            "sample_concentration": float(concentration), # Alias

            # --- Datos de Picos (ya son floats/ints/strings) ---
            "peaks": peaks,
            "peaks_count": len(peaks),

            # --- Métricas de Calidad (Aplanadas) ---
            "quality_metrics": quality_metrics,
            "signal_to_noise": quality_metrics.get('snr', 0),
            "snr": quality_metrics.get('snr', 0), # Alias

            # --- Región Flúor (Aplanada) ---
            "fluor_total": fluor_total_stats, 
            "fluor_percentage": fluor_total_stats.get('percentage', 0),
            "fluor_area": fluor_total_stats.get('total_area', 0),

            # --- Región PIFAS (Aplanada) ---
            "pifas": pifas_stats, 
            "pifas_percentage": pifas_stats.get('percentage', 0),
            "pfas_percentage": pifas_stats.get('percentage', 0), # Alias
            "pifas_area": pifas_stats.get('total_area', 0),
            "pfas_area": pifas_stats.get('total_area', 0), # Alias
            "pifas_concentration": pifas_concentration,   
            "pfas_concentration": pfas_concentration,     
            "total_integral": fluor_total_stats.get('total_area', 0), # Alias

            # --- Configuración ---
            "baseline_corrected": baseline_correction,
            "baseline_value": float(self.baseline_value) if self.baseline_value else 0.0,
            "spectrometer_config": {
                "h1_frequency_mhz": self.spectrometer_h1_freq,
                "f19_frequency_mhz": self.f19_frequency
            }
        }

        # Detección de PFAS
        try:
            print(f"\n   🔍 Iniciando detección de PFAS...")
            
            peak_ppms = [p['ppm'] for p in peaks]
            peak_intensities = [p['intensity'] for p in peaks]
            
            print(f"   Picos a analizar: {len(peak_ppms)}")
            if peak_ppms:
                print(f"   Rango de picos: {min(peak_ppms):.2f} a {max(peak_ppms):.2f} ppm")
            
            pfas_detection = self.pfas_detector.detect_pfas(
                chemical_shifts=peak_ppms,
                intensities=peak_intensities,
                confidence_threshold=0.60
            )
            
            results["pfas_detection"] = pfas_detection
            
            print(f"   ✅ Detección completada: {pfas_detection['total_detected']} PFAS detectados")
            
        except Exception as e:
            print(f"   ⚠️ Error en detección de PFAS: {e}")
            import traceback
            traceback.print_exc()
            results["pfas_detection"] = {
                "detected_pfas": [],
                "total_detected": 0,
                "error": str(e)
            }
            
        quality_score, quality_breakdown = self._calculate_quality_score_v2(quality_metrics, peaks) 
        results["quality_score"] = float(quality_score) # Convertir a float
        results["quality_breakdown"] = quality_breakdown

        self._print_summary(results)
            
        return results    
            
    def _find_best_column(self, all_rows, num_cols):
        """Encuentra la mejor columna de intensidad en archivos multi-columna."""
        column_stats = []
        
        for col_idx in range(1, num_cols):
            intensities = []
            for row in all_rows:
                if len(row) > col_idx and row[col_idx].strip():
                    
                    # --- ¡¡¡INICIO DE LA CORRECCIÓN!!! ---
                    try:
                        intensities.append(float(row[col_idx].strip()))
                    except ValueError:
                        pass # Ignora valores no numéricos (como 'Title', 'Class', etc.)
                    # --- ¡¡¡FIN DE LA CORRECCIÓN!!! ---
            
            if len(intensities) < 100:
                continue
            
            data = np.array(intensities)
            mean_val = np.mean(data)
            std_val = np.std(data)
            peak_count = len(find_peaks(data, height=mean_val + 2*std_val)[0])
            
            column_stats.append({
                'index': col_idx,
                'mean': mean_val,
                'std': std_val,
                'peak_count': peak_count,
                'score': peak_count * std_val
            })
        
        if not column_stats:
            return 1
        
        best_column = max(column_stats, key=lambda x: x['score'])
        return best_column['index']
    
    def _read_spectrum(self, file_path: Path):
        """
        Lee archivo de espectro en cualquier formato soportado
        Usa NMRDataReader para soporte multi-formato
        """
        try:
            # Detectar formato
            data_format = self.nmr_reader.detect_format(file_path)
            
            logging.info(f"   📂 Formato detectado: {data_format}")
            
            # Leer datos
            ppm_values, intensity_values, metadata = self.nmr_reader.read_data(file_path)
            
            # Guardar metadata
            self.file_metadata = metadata
            
            # Guardar datos
            self.ppm_data = ppm_values
            self.intensity_data = intensity_values
            
            logging.info(f"   ✅ Datos cargados: {len(ppm_values)} puntos")
            logging.info(f"   📊 Formato: {metadata.get('format', 'unknown')}")
            
            if 'spectrometer_freq' in metadata:
                logging.info(f"   🧲 Frecuencia: {metadata['spectrometer_freq']:.1f} MHz")
            
            if 'nucleus' in metadata:
                logging.info(f"   ⚛️  Núcleo: {metadata['nucleus']}")
            
        except Exception as e:
            logging.error(f"   ❌ Error leyendo datos: {e}")
            raise

    def _correct_baseline(self):
        """Corrección simple de baseline (percentil 5)"""
        self.baseline_value = np.percentile(self.intensity_data, 5)
        self.intensity_corrected = self.intensity_data - self.baseline_value
    
    def _correct_baseline_polynomial(self, degree: int = 2):
        """
        Corrección de baseline con ajuste polinomial.
        """
        intensity = self.intensity_data
        mean = np.mean(intensity)
        std = np.std(intensity)
        
        baseline_mask = intensity < (mean + std)
        baseline_points = np.where(baseline_mask)[0]
        
        if len(baseline_points) < 10:
            self._correct_baseline()
            return
        
        ppm_baseline = self.ppm_data[baseline_points]
        intensity_baseline = intensity[baseline_points]
        
        try:
            poly_coeffs = np.polyfit(ppm_baseline, intensity_baseline, degree)
            baseline_fit = np.polyval(poly_coeffs, self.ppm_data)
            
            self.intensity_corrected = self.intensity_data - baseline_fit
            self.baseline_value = np.mean(baseline_fit)
            
        except Exception as e:
            print(f"   ⚠️ Error en baseline polynomial: {e}, usando método simple")
            self._correct_baseline()
    
    def _analyze_region(self, min_ppm: float, max_ppm: float) -> Dict:
        """Analiza una región específica del espectro"""
        mask = (self.ppm_data >= min_ppm) & (self.ppm_data <= max_ppm)
        region_intensity = self.intensity_corrected[mask]
        region_ppm = self.ppm_data[mask]
        
        if len(region_intensity) == 0:
            return {
                "total_area": 0.0,
                "max_intensity": 0.0,
                "n_points": 0,
                "percentage": 0.0
            }
        
        if len(region_ppm) > 1:
            total_area = float(np.trapz(region_intensity, region_ppm))
        else:
            total_area = 0.0
        
        max_intensity = float(np.max(region_intensity))
        n_points = int(len(region_intensity))
        
        total_full_area = float(np.trapz(self.intensity_corrected, self.ppm_data))
        percentage = (total_area / total_full_area * 100) if total_full_area != 0 else 0.0
        
        return {
            "total_area": abs(total_area),
            "max_intensity": max_intensity,
            "n_points": n_points,
            "percentage": abs(percentage),
            "ppm_range": [float(min_ppm), float(max_ppm)]
        }
    
    def _detect_peaks_advanced(self, min_ppm: float, max_ppm: float, 
                               global_noise_level: float = 1.0, 
                               max_signal_intensity: float = 1.0) -> List[Dict]: # <-- Parámetro nuevo
        """
        Detección avanzada de picos (Corregida con filtro RELATIVO)
        """
        mask = (self.ppm_data >= min_ppm) & (self.ppm_data <= max_ppm)
        region_intensity = self.intensity_corrected[mask]
        region_ppm = self.ppm_data[mask]
        
        if len(region_intensity) < 10:
            return []
        
        # --- INICIO DE LA MEJORA (FILTRO RELATIVO) ---

        # Umbral de ruido (basado en StdDev, como antes)
        noise_threshold = global_noise_level * 3 

        # Umbral relativo (¡EL MÁS IMPORTANTE!)
        # Un pico real debe ser al menos 0.5% (0.005) de la señal más fuerte.
        # Puedes ajustar este valor (ej. 0.01 para 1%) si 2200 picos persisten.
        relative_threshold = max_signal_intensity * 0.03 

        # El umbral final es el MÁS GRANDE de los dos.
        # Esto evita que el ruido sea detectado en espectros de alta señal.
        signal_threshold = max(noise_threshold, relative_threshold)

        print(f"   [DETECTOR DE PICOS] Nivel de Ruido (StdDev): {global_noise_level:.2e}")
        print(f"   [DETECTOR DE PICOS] Umbral Relativo (0.5% max): {relative_threshold:.2e}")
        print(f"   [DETECTOR DE PICOS] Umbral FINAL a usar: {signal_threshold:.2e}")
        # --- FIN DE LA MEJORA ---

        # 🔧 CORRECCIÓN: Calcular resolución PPM con protección contra división por cero
        if len(region_ppm) > 1:
            ppm_resolution = abs(region_ppm[1] - region_ppm[0])
            # Si los primeros puntos son idénticos, calcular con más puntos
            if ppm_resolution == 0:
                # Buscar el primer punto diferente
                for i in range(2, min(len(region_ppm), 100)):
                    ppm_resolution = abs(region_ppm[i] - region_ppm[0]) / i
                    if ppm_resolution > 0:
                        break
                # Si aún es 0, usar valor por defecto
                if ppm_resolution == 0:
                    ppm_resolution = 0.001
        else:
            ppm_resolution = 0.001
        
        min_distance_ppm = 0.02
        min_distance_points = max(3, int(min_distance_ppm / ppm_resolution))
        
        peaks, properties = find_peaks(
            region_intensity,
            height=signal_threshold,      # 1. El pico debe ser más alto que el umbral final.
            distance=min_distance_points,
            prominence=signal_threshold   # 2. El pico debe "sobresalir" por encima del umbral final.
        )
        
        peak_list = []
        
        for i, peak_idx in enumerate(peaks):
            
            ppm = float(region_ppm[peak_idx])
            intensity = float(region_intensity[peak_idx])
            
            try:
                widths, width_heights, left_ips, right_ips = peak_widths(
                    region_intensity, 
                    [peak_idx], 
                    rel_height=0.5
                )
                width_ppm = float(widths[0]) * ppm_resolution
                width_hz = ppm_to_hz(width_ppm, self.f19_frequency)
            except:
                width_hz = 10.0
                width_ppm = hz_to_ppm(width_hz, self.f19_frequency)
            
            snr = float(intensity / global_noise_level) # Usar siempre el ruido global
            region = self._get_peak_region(ppm)
            area = float(intensity * width_ppm)

            # --- ¡INICIO DE LA CORRECCIÓN! ---
            # Calcular la intensidad relativa usando el max_signal_intensity de todo el espectro
            relative_intensity = (intensity / max_signal_intensity) * 100 if max_signal_intensity > 0 else 0.0
            # --- ¡FIN DE LA CORRECCIÓN! ---

            peak_list.append({
                "index": int(i),
                "ppm": ppm,
                "intensity": intensity,
                "relative_intensity": float(relative_intensity), # <-- NUEVA LÍNEA
                "width_hz": float(width_hz),
                "width_ppm": float(width_ppm),
                "snr": snr,
                "prominence": float(properties['prominences'][i]),
                "region": region,
                "area": area
            })
        
        return peak_list
    
    def _calculate_quality_metrics(self) -> Dict:
        """
        Calcula métricas de calidad del espectro.
        """
        # Región de referencia sin señal
        noise_region_mask = (self.ppm_data >= -200) & (self.ppm_data <= -180)
        
        if np.sum(noise_region_mask) > 10:
            noise_region = self.intensity_corrected[noise_region_mask]
            noise_level = np.std(noise_region)
        else:
            # Fallback
            noise_level = np.std(self.intensity_corrected[
                self.intensity_corrected < np.percentile(self.intensity_corrected, 10)
            ])
            
        if noise_level == 0: # Evitar división por cero
            noise_level = 1e-9

        max_signal = np.max(self.intensity_corrected)
        snr = max_signal / noise_level
        
        baseline_std = float(np.std(self.intensity_corrected[
            self.intensity_corrected < np.percentile(self.intensity_corrected, 20)
        ]))
        
        return {
            "snr": float(snr),
            "noise_level": float(noise_level),
            "max_signal": float(max_signal),
            "baseline_std": baseline_std,
            "n_points_total": int(len(self.ppm_data))
        }
    
    def _calculate_quality_score_v2(self, quality_metrics: Dict, peaks: List[Dict]) -> Tuple[float, Dict]:
        """Calcula score de calidad global basado en Levitt"""
        scores = {}
        
        snr = quality_metrics.get('snr', 0)
        if snr >= 50:
            snr_score = 100
        elif snr >= 10:
            snr_score = 50 + (snr - 10) * 50 / 40
        elif snr >= 3:
            snr_score = 20 + (snr - 3) * 30 / 7
        else:
            snr_score = snr * 20 / 3
        scores['snr'] = snr_score
        
        baseline_std = quality_metrics.get('baseline_std', 0)
        baseline_score = max(0, 100 - baseline_std * 10)
        scores['baseline'] = baseline_score
        
        n_peaks = len(peaks)
        if n_peaks >= 5:
            peaks_score = 100
        elif n_peaks >= 3:
            peaks_score = 70 + (n_peaks - 3) * 15
        elif n_peaks >= 1:
            peaks_score = 40 + (n_peaks - 1) * 15
        else:
            peaks_score = 0
        scores['peaks'] = peaks_score
        
        if peaks:
            avg_width_hz = np.mean([p['width_hz'] for p in peaks])
            if avg_width_hz <= 10:
                resolution_score = 100
            elif avg_width_hz <= 20:
                resolution_score = 80 - (avg_width_hz - 10) * 2
            else:
                resolution_score = max(0, 60 - (avg_width_hz - 20))
            scores['resolution'] = resolution_score
        else:
            scores['resolution'] = 50
        
        total_score = (
            scores['snr'] * 0.4 +
            scores['baseline'] * 0.2 +
            scores['peaks'] * 0.3 +
            scores['resolution'] * 0.1
        )
        
        return total_score, scores
    
    def _print_summary(self, results: Dict):
        """Imprime resumen de resultados"""
        print(f"\n{'='*70}")
        print(f"📈 RESUMEN DE ANÁLISIS")
        print(f"{'='*70}")
        
        print(f"\n🔬 CALIDAD DEL ESPECTRO:")
        qm = results['quality_metrics']
        print(f"   SNR: {qm['snr']:.1f}")
        print(f"   Ruido: {qm['noise_level']:.2e}")
        print(f"   Señal máxima: {qm['max_signal']:.2e}")
        print(f"   Score de calidad: {results['quality_score']:.1f}/100")
        
        print(f"\n📊 ANÁLISIS POR REGIONES:")
        print(f"   Flúor Total:")
        print(f"      Área: {results['fluor_total']['total_area']:.2e}")
        print(f"      Porcentaje: {results['fluor_total']['percentage']:.2f}%")
        
        print(f"   PFAS/PIFAS:")
        print(f"      Área: {results['pifas']['total_area']:.2e}")
        print(f"      Porcentaje: {results['pifas']['percentage']:.2f}%")
        
        print(f"\n🎯 PICOS DETECTADOS: {len(results['peaks'])}")
        for i, peak in enumerate(results['peaks'][:5], 1):  # Mostrar primeros 5
            print(f"   {i}. {peak['ppm']:.2f} ppm - Intensidad: {peak['intensity']:.2e} - "
                  f"Ancho: {peak['width_hz']:.1f} Hz - SNR: {peak['snr']:.1f} - Region: {peak['region']}")
        
        if len(results['peaks']) > 5:
            print(f"   ... y {len(results['peaks']) - 5} más")
        
        # Mostrar resultados de PFAS
        pfas = results.get('pfas_detection', {})
        if pfas.get('total_detected', 0) > 0:
            print(f"\n🧪 PFAS DETECTADOS: {pfas['total_detected']}")
            for detected in pfas.get('detected_pfas', []):
                print(f"   • {detected['name']}: {detected['confidence']:.1%} confianza")
                print(f"     Categoría: {detected.get('category', 'N/A')}")
                print(f"     Picos: {detected['peaks_matched']}/{detected['peaks_expected']}")
        else:
            # Comprobar si hubo un error en la detección
            if pfas.get('error'):
                print(f"\n⚠️  Error en la detección de PFAS: {pfas['error']}")
            else:
                print(f"\n⚠️  No se detectaron PFAS con confianza suficiente")
        
        print(f"\n{'='*70}\n")


def main():
    """Función principal para testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python analyzer.py <archivo.csv>")
        return
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: Archivo no encontrado: {file_path}")
        return
    
    analyzer = SpectrumAnalyzer(spectrometer_h1_freq_mhz=500.0)
    results = analyzer.analyze_file(
        file_path,
        baseline_correction=True,
        baseline_method='polynomial'
    )
    
    # Guardar resultados
    output_file = file_path.with_suffix('.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Resultados guardados en: {output_file}")


if __name__ == "__main__":
    main()