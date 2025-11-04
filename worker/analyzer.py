import csv
import json
import numpy as np
import re # ### NUEVO ### Importar regex para parsear límites
from pathlib import Path
from typing import Dict, List, Tuple
from scipy.signal import find_peaks, peak_widths
from pfas_detector_enhanced import PFASDetectorEnhanced as PFASDetector


class SpectrumAnalyzer:
    """
    Analizador mejorado v2.2 de espectros RMN para detección de PFAS
    
    Mejoras v2.2:
    - Cálculo de área de pico individual (integración trapezoidal).
    - Evaluación de límites en estadísticas detalladas.
    - Cálculo de ancho de pico con scipy.signal.peak_widths.
    - Exposición de datos de baseline y desglose de calidad.
    - Cálculo de SNR consistente.
    - Mejor manejo de datos insuficientes.
    """
    
    def __init__(self):
        self.ppm_data = np.array([]) # Usar arrays numpy internamente
        self.intensity_data = np.array([])
        self.intensity_corrected = np.array([])
        self.baseline_value = None # ### NUEVO ### Guardar baseline
        self.analysis_results = {}
    
    def analyze_file(self, file_path: Path, 
                     fluor_range: Dict = None,
                     pifas_range: Dict = None,
                     concentration: float = 1.0,
                     baseline_correction: bool = True) -> Dict:
        """
        Analiza un archivo de espectro RMN
        
        Args:
            file_path: Ruta al archivo CSV
            fluor_range: Rango de ppm para flúor total {"min": -150, "max": -50}
            pifas_range: Rango de ppm para PFAS/PIFAS {"min": -130, "max": -60}
            concentration: Concentración de la muestra en mM
            baseline_correction: Si True, corrige el baseline automáticamente
        
        Returns:
            Dict con resultados del análisis
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
        
        # Leer archivo
        self._read_spectrum(file_path)

        if len(self.ppm_data) < 2:
             print("   ❌ Error: No hay suficientes puntos de datos para analizar.")
             # Devolver un resultado indicando el error
             return {
                "filename": file_path.name, 
                "error": "No data points found or file read error.",
                # ... puedes añadir más campos por defecto o vacíos ...
             }

        
        # Corrección de baseline
        if baseline_correction:
            self._correct_baseline()
        else:
            print("\n   ℹ️  Corrección de baseline desactivada.")
            self.intensity_corrected = self.intensity_data.copy()
            self.baseline_value = 0.0 # ### NUEVO ###
        
        # Convertir arrays numpy a listas para JSON solo al final
        ppm_list = [round(float(x), 4) for x in self.ppm_data]
        intensity_corrected_list = [round(float(x), 4) for x in self.intensity_corrected]
        
        # Realizar análisis completo
        quality_metrics = self._calculate_quality_metrics()
        peaks = self._detect_peaks_advanced()
        analysis_data = self._calculate_analysis(fluor_range, pifas_range, concentration)
        region_data = self._analyze_regions()
        detailed_stats = self._detailed_statistics(fluor_range, pifas_range, quality_metrics["snr"])

        results = {
            "filename": file_path.name,
            "timestamp": Path(file_path).stat().st_mtime,
            "parameters": {
                "fluor_range": fluor_range,
                "pifas_range": pifas_range,
                "concentration": concentration,
                "baseline_correction": baseline_correction
            },
            "spectrum": {
                "ppm": ppm_list,
                "intensity": intensity_corrected_list,
                "ppm_min": round(float(np.min(self.ppm_data)), 2),
                "ppm_max": round(float(np.max(self.ppm_data)), 2),
                "data_points": len(self.ppm_data),
                "intensity_min_orig": round(float(np.min(self.intensity_data)), 2),
                "intensity_max_orig": round(float(np.max(self.intensity_data)), 2),
                "intensity_min_corr": round(float(np.min(self.intensity_corrected)), 2),
                "intensity_max_corr": round(float(np.max(self.intensity_corrected)), 2),
                "baseline_value": round(float(self.baseline_value), 2) if self.baseline_value is not None else None
            },
            "analysis": analysis_data,
            "peaks": peaks,
            "regions": region_data,
            "quality_metrics": quality_metrics,
            "detailed_analysis": detailed_stats,
            
            # ✅ AGREGAR ALIAS PARA COMPATIBILIDAD CON FRONTEND
            "signal_to_noise": quality_metrics.get("snr", 0),  # Alias
            "snr": quality_metrics.get("snr", 0)  # Alias adicional
            
        }

        try:
            
            detector = PFASDetector(confidence_threshold=0.55)
            pfas_detection = detector.detect_pfas(peaks, results)
            results["pfas_detection"] = pfas_detection

        except Exception as e:
            print(f"⚠️ Error en detección de PFAS: {e}")
            results["pfas_detection"] = {"detected": False, "error": str(e)}
            
        quality_score, quality_breakdown = self._calculate_quality_score_v2(quality_metrics, peaks) 
        results["quality_score"] = quality_score
        results["quality_breakdown"] = quality_breakdown

        self._print_summary(results)
            
        return results    
            
    def _read_spectrum(self, file_path: Path):
        """Lee archivo CSV y guarda como numpy arrays."""
        _ppm_data = []
        _intensity_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f: # Añadir encoding
                sample = f.read(2048)
                f.seek(0)
                
                dialect = csv.Sniffer().sniff(sample, delimiters=',\t')
                has_header = csv.Sniffer().has_header(sample)
                
                reader = csv.reader(f, dialect)
                
                if has_header:
                    print("   ℹ️  Detectado encabezado, saltando primera línea")
                    next(reader)
                
                row_count = 0
                for row in reader:
                    row_count += 1
                    if len(row) >= 2:
                        try:
                            ppm = float(row[0].strip())
                            intensity = float(row[1].strip())
                            _ppm_data.append(ppm)
                            _intensity_data.append(intensity)
                        except (ValueError, IndexError):
                             print(f"   ⚠️  Advertencia: Ignorando fila {row_count} inválida: {row}")
                             continue # Ignorar filas no numéricas o incompletas
            
            # Convertir a numpy arrays al final
            self.ppm_data = np.array(_ppm_data)
            self.intensity_data = np.array(_intensity_data)

            if len(self.ppm_data) == 0:
                 print("   ❌ Error: No se pudieron leer datos numéricos del archivo.")
                 return # Salir si no hay datos

            print(f"   ✅ Leídos {len(self.ppm_data):,} puntos de datos")
            print(f"   ℹ️  Delimitador detectado: '{dialect.delimiter}'")
            print(f"   ℹ️  Rango PPM: {np.min(self.ppm_data):.2f} a {np.max(self.ppm_data):.2f}")
            print(f"   ℹ️  Rango Intensidad original: {np.min(self.intensity_data):.2f} a {np.max(self.intensity_data):.2f}")

        except csv.Error as e:
             print(f"   ❌ Error de CSV Sniffer: {e}. Asegúrate que el archivo usa comas o tabs.")
             # Dejar arrays vacíos para indicar fallo
             self.ppm_data = np.array([])
             self.intensity_data = np.array([])
        except Exception as e:
            print(f"   ❌ Error inesperado al leer el archivo: {e}")
            self.ppm_data = np.array([])
            self.intensity_data = np.array([])
            # raise # Opcional: relanzar para detener ejecución si es crítico

    def _correct_baseline(self):
        """Corrección de baseline simple restando el percentil 5."""
        print("\n   🔧 Aplicando corrección de baseline...")
        
        if len(self.intensity_data) < 10: # Necesita suficientes puntos
             print("   ⚠️  Advertencia: No hay suficientes puntos para corrección de baseline fiable.")
             self.intensity_corrected = self.intensity_data.copy()
             self.baseline_value = 0.0
             return

        intensity = self.intensity_data # Ya es numpy array
        
        # Usar el percentil 5 como estimación robusta del baseline
        baseline = np.percentile(intensity, 5)
        self.baseline_value = baseline # ### NUEVO ### Guardar valor
        
        # Corregir: restar el baseline
        self.intensity_corrected = intensity - baseline
        
        # Opcional: Forzar que el mínimo sea 0 (si se asume que no hay señal negativa real)
        # self.intensity_corrected = np.maximum(self.intensity_corrected, 0)
        
        print(f"   ✅ Baseline estimado: {baseline:.2f} a.u.")
        print(f"   ✅ Rango corregido: {np.min(self.intensity_corrected):.2f} a {np.max(self.intensity_corrected):.2f} a.u.")
        print(f"   ✅ Intensidad media corregida: {np.mean(self.intensity_corrected):.2f} a.u.")
    
    def _calculate_analysis(self, fluor_range: Dict, pifas_range: Dict, 
                        concentration: float) -> Dict:
        """Calcula áreas y concentraciones."""
        
        print("\n   📈 Calculando composición química...")
        
        ppm = self.ppm_data 
        intensity = self.intensity_corrected
        
        if len(ppm) < 2:
            return {
                "fluor_percentage": 0.0, "pifas_percentage": 0.0,
                "pifas_concentration": 0.0, "concentration": concentration,
                "total_area": 0.0, 
                "total_integral": 0.0,  # ✅ ALIAS PARA FRONTEND
                "fluor_area": 0.0, "pifas_area": 0.0,
                "fluor_atoms_estimate": 0.0
            }

        total_area = np.trapz(intensity, ppm)
        
        fluor_mask = (ppm >= fluor_range["min"]) & (ppm <= fluor_range["max"])
        fluor_area = np.trapz(intensity[fluor_mask], ppm[fluor_mask]) if np.sum(fluor_mask) > 1 else 0
        
        pifas_mask = (ppm >= pifas_range["min"]) & (ppm <= pifas_range["max"])
        pifas_area = np.trapz(intensity[pifas_mask], ppm[pifas_mask]) if np.sum(pifas_mask) > 1 else 0
        
        epsilon = 1e-12
        fluor_percentage = (abs(fluor_area) / (abs(total_area) + epsilon) * 100)
        pifas_percentage = (abs(pifas_area) / (abs(fluor_area) + epsilon) * 100)
        pifas_concentration = concentration * (pifas_percentage / 100)
        
        fluor_atoms_estimate = abs(fluor_area) / (np.max(intensity) + epsilon) if np.max(intensity) > 0 else 0
        
        print(f"   ✅ Área total:           {total_area:,.2f}")
        print(f"   ✅ Área flúor:           {fluor_area:,.2f} ({fluor_percentage:.1f}%)")
        print(f"   ✅ Área PFAS:            {pifas_area:,.2f} ({pifas_percentage:.1f}% del flúor)")
        print(f"   ✅ Concentración PFAS:   {pifas_concentration:.4f} mM")
        
        return {
            "fluor_percentage": round(float(fluor_percentage), 2),
            "pifas_percentage": round(float(pifas_percentage), 2),
            "pifas_concentration": round(float(pifas_concentration), 4),
            "concentration": float(concentration),
            "total_area": round(float(total_area), 2),
            "total_integral": round(float(total_area), 2),  # ✅ ALIAS PARA FRONTEND
            "fluor_area": round(float(fluor_area), 2),
            "pifas_area": round(float(pifas_area), 2),
            "fluor_atoms_estimate": round(float(fluor_atoms_estimate), 1)
        }
        
    def _detect_peaks_advanced(self, prominence_factor=0.5, height_factor=0.3, 
                            spectrometer_freq_mhz=470.0) -> List[Dict]:  # ✅ AÑADIR PARÁMETRO
        """Detecta picos usando scipy.signal.find_peaks, calcula anchos y áreas."""
        print("\n   🔍 Detectando picos significativos...")
        
        intensity = self.intensity_corrected
        ppm = self.ppm_data
        
        if len(intensity) < 5:
            print("   ⚠️  Advertencia: No hay suficientes puntos para detectar picos.")
            return []
        
        # --- Estimación de ruido y umbrales ---
        noise_region = intensity[intensity < np.percentile(intensity, 15)]
        noise_std = np.std(noise_region) if len(noise_region) > 1 else np.std(intensity) / 3
        noise_std = max(noise_std, 1e-9)
        
        signal_mean = np.mean(intensity)
        signal_max = np.max(intensity)
        
        min_prominence = max(prominence_factor * noise_std, signal_max * 0.01)
        min_height = max(height_factor * noise_std, signal_mean * 0.1)
        min_distance = max(len(intensity) // 500, 3)

        print(f"   ℹ️  Señal: Max={signal_max:.2f}, Media={signal_mean:.2f}, Ruido Std={noise_std:.2f}")
        print(f"   ℹ️  Criterios picos: Prominencia > {min_prominence:.2f}, Altura > {min_height:.2f}, Distancia > {min_distance} pts")

        # --- Encontrar Picos ---
        try:
            peak_indices, properties = find_peaks(
                intensity,
                height=min_height,
                prominence=min_prominence,
                distance=min_distance
            )
        except Exception as e:
            print(f"   ❌ Error detectando picos: {e}")
            return []

        print(f"   ℹ️  Picos candidatos encontrados: {len(peak_indices)}")

        if len(peak_indices) == 0:
            print("   ⚠️  No se detectaron picos. Intentando con criterios más relajados...")
            try:
                peak_indices, properties = find_peaks(
                    intensity,
                    height=signal_mean * 0.05,
                    prominence=signal_max * 0.005,
                    distance=3
                )
                print(f"   ℹ️  Segundo intento: {len(peak_indices)} picos encontrados")
            except Exception as e:
                print(f"   ❌ Error en segundo intento: {e}")
                return []
            
            if len(peak_indices) == 0:
                print("   ℹ️  No se detectaron picos incluso con criterios relajados.")
                return []

        # --- Calcular Ancho de Picos ---
        
        try:
            widths, width_heights, left_ips, right_ips = peak_widths(
                intensity, peak_indices, rel_height=0.5
            )
            
            indices = np.arange(len(ppm))
            widths_ppm = abs(np.interp(right_ips, indices, ppm) - np.interp(left_ips, indices, ppm))
            
            left_indices = np.floor(left_ips).astype(int)
            right_indices = np.ceil(right_ips).astype(int)
            
            left_indices = np.clip(left_indices, 0, len(ppm) - 1)
            right_indices = np.clip(right_indices, 0, len(ppm) - 1)
            
        except Exception as e:
            print(f"   ⚠️  Error calculando anchos de pico: {e}. Usando valores por defecto.")
            widths_ppm = np.ones(len(peak_indices)) * 0.1
            left_indices = np.maximum(peak_indices - 5, 0)
            right_indices = np.minimum(peak_indices + 5, len(ppm) - 1)

        peaks = []
        max_intensity_overall = signal_max if signal_max > 0 else 1.0

        for i, idx in enumerate(peak_indices):
            peak_ppm = float(ppm[idx])
            peak_intensity = float(intensity[idx])
            region = self._classify_chemical_region(peak_ppm)
            
            # Calcular área del pico
            left_idx = int(left_indices[i])
            right_idx = int(right_indices[i])
            
            if right_idx > left_idx:
                peak_ppm_range = ppm[left_idx:right_idx+1]
                peak_intensity_range = intensity[left_idx:right_idx+1]
                peak_area = np.trapz(peak_intensity_range, peak_ppm_range)
            else:
                peak_area = 0.0
            
            # ✅ CALCULAR ANCHO EN Hz
            width_ppm_value = float(widths_ppm[i])
            width_hz = abs(width_ppm_value * spectrometer_freq_mhz)  # Convertir ppm a Hz
            
            # ✅ CALCULAR SNR INDIVIDUAL DEL PICO
            peak_snr = peak_intensity / noise_std if noise_std > 0 else 0.0
            
            peaks.append({
                "ppm": round(peak_ppm, 3),
                "intensity": round(peak_intensity, 2),
                "relative_intensity": round((peak_intensity / max_intensity_overall * 100), 1),
                "width_ppm": round(width_ppm_value, 3),
                "width_hz": round(width_hz, 2),  # ✅ NUEVO
                "area": round(float(abs(peak_area)), 2),
                "region": region,
                "prominence": round(float(properties["prominences"][i]), 2),
                "snr": round(peak_snr, 2)  # ✅ NUEVO
            })
        
        # Guardar total antes de limitar
        total_peaks_detected = len(peaks)
        
        # Ordenar y limitar
        peaks.sort(key=lambda x: x["intensity"], reverse=True)
        peaks = peaks[:20]
        peaks.sort(key=lambda x: x["ppm"])
        
        # Mensaje corregido
        if total_peaks_detected <= 20:
            print(f"   ✅ Detectados {total_peaks_detected} picos significativos")
        else:
            print(f"   ✅ Detectados {total_peaks_detected} picos significativos (mostrando top 20 por intensidad)")
        
        if len(peaks) > 0:
            main_peak = max(peaks, key=lambda p: p["intensity"])
            print(f"   ✅ Pico principal: {main_peak['ppm']:.3f} ppm (Int: {main_peak['intensity']:.1f}, Área: {main_peak['area']:.2f}, SNR: {main_peak['snr']:.2f})")
        
        return peaks
        
    def _classify_chemical_region(self, ppm: float) -> str:
        """Clasifica la región química basada en rangos típicos de PFAS."""
        # Rangos ajustados según literatura de 19F-NMR para PFAS
        if -90 <= ppm <= -75:
            return "CF₃ Terminal (ej. PFOA, PFOS)"
        elif -100 <= ppm <= -90:
            return "CF₂ Interno (Lejano del grupo polar)"
        elif -115 <= ppm <= -100:
            return "CF₂ Interno (Central)"
        elif -130 <= ppm <= -115:
            return "CF₂ Próximo a grupo polar (ej. -CF₂-COO⁻)"
        elif ppm < -130:
            return "CF₂ Otros / Fluoruros especiales"
        elif -75 <= ppm <= -55:
            return "CF Ramificado / CFH"
        else:
            return "Fuera de rango PFAS típico (-130 a -55 ppm)"
            
    def _analyze_regions(self) -> Dict:
        """Analiza la contribución de área en regiones químicas predefinidas."""
        print("\n   🗺️  Analizando contribución por regiones químicas...")
        ppm = self.ppm_data
        intensity = self.intensity_corrected
        
        # Regiones definidas con nombres más descriptivos
        regions = {
            "CF₃_terminal_PFOA_like": {"range": (-85, -75), "name": "CF₃ Terminal (Tipo PFOA)"},
            "CF₂_internal_far": {"range": (-110, -100), "name": "CF₂ Interno (Lejano)"},
            "CF₂_internal": {"range": (-120, -110), "name": "CF₂ Interno"},
            "CF₂_near_polar_PFOA_like": {"range": (-128, -120), "name": "CF₂ Próximo Polar (Tipo PFOA)"},
            "CF₂_other_long_chain": {"range": (-150, -128), "name": "CF₂ Otros / Cadena Larga"}
            # Añadir más si es necesario
        }
        
        results = {}
        # Usar área total calculada previamente para consistencia
        total_area = self.analysis_results.get("analysis", {}).get("total_area", None)
        if total_area is None or abs(total_area) < 1e-12:
             # Si no se pudo calcular antes, recalcular o poner 0
             total_area = np.trapz(intensity, ppm) if len(ppm) > 1 else 0
             total_area = total_area if abs(total_area) > 1e-12 else 1e-12 # Evitar división por cero

        
        for key, region_info in regions.items():
            min_ppm, max_ppm = region_info["range"]
            mask = (ppm >= min_ppm) & (ppm <= max_ppm)
            num_points = int(np.sum(mask))
            
            area = 0.0
            percentage = 0.0
            max_int = 0.0
            
            if num_points > 1: # Necesita al menos 2 puntos para integrar
                region_intensity = intensity[mask]
                region_ppm = ppm[mask]
                area = np.trapz(region_intensity, region_ppm)
                percentage = abs(area / total_area * 100)
                max_int = np.max(region_intensity) if len(region_intensity) > 0 else 0.0
                print(f"   - {region_info['name']} ({min_ppm} a {max_ppm} ppm): Área={area:.2f} ({percentage:.1f}%)")

            
            results[key] = {
                "name": region_info["name"],
                "range_ppm": f"{min_ppm} to {max_ppm}",
                "area": round(float(area), 2),
                "percentage_total": round(float(percentage), 2), # % del área total
                "max_intensity": round(float(max_int), 2),
                "points": num_points
            }
        
        return results
    
    def _calculate_quality_metrics(self) -> Dict:
        """Calcula métricas de calidad clave."""
        print("\n   ⭐ Calculando métricas de calidad...")
        intensity_orig = self.intensity_data
        intensity = self.intensity_corrected
        ppm = self.ppm_data

        if len(intensity) < 10: # Pocos datos, métricas no fiables
             print("   ⚠️  Advertencia: Datos insuficientes para métricas de calidad.")
             return { "snr": 0.0, "dynamic_range": 0.0, "baseline_stability": 0.0, 
                      "data_density": 0.0, "spectral_resolution": 0.0, "total_points": len(ppm) }
        
        # --- SNR (Signal-to-Noise Ratio) ---
        # Señal: Amplitud máxima corregida
        signal_max = np.max(intensity) if len(intensity) > 0 else 0
        # Ruido: Desviación estándar en una región supuestamente sin señal (percentil < 10)
        noise_region_mask = intensity < np.percentile(intensity, 10)
        # Asegurar que la región de ruido no esté vacía y tenga > 1 punto
        if np.sum(noise_region_mask) > 1:
            noise_std = np.std(intensity[noise_region_mask])
        else: # Fallback si no hay región de ruido clara
            noise_std = np.std(intensity) / 3 # Estimación muy grosera
        
        noise_std = max(noise_std, 1e-9) # Evitar división por cero
        snr = signal_max / noise_std
        print(f"   ℹ️  SNR estimado: {snr:.2f} (Signal={signal_max:.2f}, Noise Std={noise_std:.2f})")
        
        # --- Dynamic Range (on corrected data) ---
        dynamic_range = np.max(intensity) - np.min(intensity)
        
        # --- Baseline Stability / Noise Level ---
        # Usamos la misma std del ruido calculada para SNR
        baseline_stability_std = noise_std 
        
        # --- Data Density (points per ppm) ---
        ppm_range_val = abs(np.max(ppm) - np.min(ppm)) if len(ppm) > 1 else 1.0
        data_density = len(ppm) / max(ppm_range_val, 1e-9)
        
        # --- Spectral Resolution (ppm per point) ---
        # Promedio del espaciado entre puntos
        spectral_resolution = np.mean(np.diff(ppm)) if len(ppm) > 1 else 0.0
        
        return {
            "snr": round(float(snr), 2),
            "dynamic_range": round(float(dynamic_range), 2),
            "baseline_stability_std": round(float(baseline_stability_std), 3), # ### NUEVO ### Renombrado
            "data_density_pts_ppm": round(float(data_density), 1), # ### NUEVO ### Renombrado
            "spectral_resolution_ppm_pt": round(float(abs(spectral_resolution)), 4), # ### NUEVO ### Renombrado
            "total_points": int(len(ppm))
        }
    
    # ### MODIFICADO ### Ahora devuelve score y desglose
    def _calculate_quality_score_v2(self, metrics: Dict, peaks: List) -> Tuple[float, Dict]:
        """Calcula score de calidad (0-10) y devuelve desglose de penalizaciones."""
        score = 10.0
        penalties = {} # ### NUEVO ### Para guardar el desglose

        # --- SNR ---
        snr = metrics.get("snr", 0)
        snr_penalty = 0
        if snr < 5: snr_penalty = 3.0
        elif snr < 10: snr_penalty = 2.0
        elif snr < 20: snr_penalty = 1.0
        if snr_penalty > 0:
            score -= snr_penalty
            penalties["snr"] = f"-{snr_penalty:.1f} (Valor: {snr:.1f}, Umbrales: <5, <10, <20)"

        # --- Puntos de datos ---
        total_points = metrics.get("total_points", 0)
        points_penalty = 0
        if total_points < 1000: points_penalty = 1.5 # Menos penalización que antes
        elif total_points < 5000: points_penalty = 0.5
        if points_penalty > 0:
            score -= points_penalty
            penalties["total_points"] = f"-{points_penalty:.1f} (Valor: {total_points}, Umbrales: <1k, <5k)"
        
        # --- Dynamic Range ---
        dynamic_range = metrics.get("dynamic_range", 0)
        dr_penalty = 0
        if dynamic_range < 50: dr_penalty = 1.5
        elif dynamic_range < 100: dr_penalty = 0.5
        if dr_penalty > 0:
            score -= dr_penalty
            penalties["dynamic_range"] = f"-{dr_penalty:.1f} (Valor: {dynamic_range:.1f}, Umbrales: <50, <100)"
        
        # --- Baseline Stability ---
        baseline_std = metrics.get("baseline_stability_std", 100)
        bs_penalty = 0
        signal_max = np.max(self.intensity_corrected) if len(self.intensity_corrected)>0 else 1
        relative_noise = (baseline_std / max(signal_max, 1e-9)) * 100 # Ruido como % de señal max
        
        if relative_noise > 10: bs_penalty = 2.0 # Si el ruido es >10% de la señal
        elif relative_noise > 5: bs_penalty = 1.0 # Si es >5%
        if bs_penalty > 0:
             score -= bs_penalty
             penalties["baseline_stability"] = f"-{bs_penalty:.1f} (Ruido relativo: {relative_noise:.1f}%, Umbrales: >10%, >5%)"

        # --- Detección de Picos ---
        peaks_penalty = 0
        if peaks is None or len(peaks) == 0:
             peaks_penalty = 1.0 # Penalización si no se detecta ningún pico
        elif len(peaks) < 3:
             peaks_penalty = 0.5 # Penalización menor si hay muy pocos
        if peaks_penalty > 0:
            score -= peaks_penalty
            peak_count = len(peaks) if peaks else 0
            penalties["peak_detection"] = f"-{peaks_penalty:.1f} (Picos: {peak_count}, Umbrales: <1, <3)"

        final_score = round(max(0.0, min(10.0, score)), 1)
        print(f"\n   💯 Score de Calidad Final: {final_score}/10")
        if penalties:
             print("      Penalizaciones aplicadas:")
             for key, reason in penalties.items():
                  print(f"       - {key}: {reason}")

        return final_score, penalties # Devolver score y desglose
    
    # ### MODIFICADO ### Renombrado y con evaluación de límites
    def _detailed_statistics(self, fluor_range: Dict, pifas_range: Dict, calculated_snr: float) -> Dict:
        """Estadísticas detalladas con evaluación de límites."""
        print("\n   📋 Generando estadísticas detalladas...")
        ppm = self.ppm_data
        intensity_orig = self.intensity_data
        intensity = self.intensity_corrected
        
        if len(ppm) < 2: # No se pueden calcular estadísticas
             return {"error": {"parameter": "Error", "value": "Datos insuficientes", "unit":"", "limits":""}}

        # --- Valores Calculados ---
        min_ppm, max_ppm = np.min(ppm), np.max(ppm)
        min_intensity_orig, max_intensity_orig = np.min(intensity_orig), np.max(intensity_orig)
        min_intensity_corr, max_intensity_corr = np.min(intensity), np.max(intensity)
        mean_intensity_corr = np.mean(intensity)
        std_intensity_corr = np.std(intensity)
        snr = calculated_snr # Usar el SNR calculado consistentemente
        max_signal_corr = max_intensity_corr

        # --- Evaluación de Límites ---
        ppm_status = "OK" if min_ppm >= fluor_range["min"] - 1 and max_ppm <= fluor_range["max"] + 1 else "WARN" # Margen de 1ppm
        # Extraer límite numérico de SNR (> 10)
        snr_limit_str = "> 10"
        snr_limit_match = re.search(r'>\s*(\d+\.?\d*)', snr_limit_str)
        snr_limit = float(snr_limit_match.group(1)) if snr_limit_match else 10.0
        snr_status = "OK" if snr >= snr_limit else ("WARN" if snr >= snr_limit / 2 else "FAIL") # OK, WARN, FAIL

        # Formato de salida consistente para la tabla del frontend
        stats = {
            "ppm_range": {
                "parameter": "Rango PPM", # Nombre legible
                "value": f"{min_ppm:.2f} a {max_ppm:.2f}",
                "unit": "ppm",
                "limits": f"{fluor_range['min']} a {fluor_range['max']}",
                "status": ppm_status # ### NUEVO ###
            },
            "intensity_range_original": {
                "parameter": "Rango Intensidad (Original)",
                "value": f"{min_intensity_orig:.2f} a {max_intensity_orig:.2f}",
                "unit": "a.u.",
                "limits": "—",
                "status": "INFO" # ### NUEVO ###
            },
            "intensity_range_corrected": {
                "parameter": "Rango Intensidad (Corregido)",
                "value": f"{min_intensity_corr:.2f} a {max_intensity_corr:.2f}",
                "unit": "a.u.",
                "limits": "—",
                "status": "INFO" # ### NUEVO ###
            },
             "mean_intensity_corr": { # ### NUEVO ### Nombre corregido
                "parameter": "Intensidad Media (Corregida)",
                "value": round(float(mean_intensity_corr), 2),
                "unit": "a.u.",
                "limits": "—",
                "status": "INFO" # ### NUEVO ###
            },
            "std_intensity_corr": { # ### NUEVO ### Nombre corregido
                 "parameter": "Desv. Estándar (Corregida)",
                 "value": round(float(std_intensity_corr), 2),
                 "unit": "a.u.",
                 "limits": "—",
                 "status": "INFO" # ### NUEVO ###
            },
            "signal_to_noise": {
                "parameter": "Relación Señal/Ruido (SNR)",
                "value": round(float(snr), 2) if np.isfinite(snr) else "Inf",
                "unit": "ratio",
                "limits": snr_limit_str,
                "status": snr_status # ### NUEVO ###
            },
            "max_signal_corr": { # ### NUEVO ### Nombre corregido
                "parameter": "Señal Máxima (Corregida)",
                "value": round(float(max_signal_corr), 2),
                "unit": "a.u.",
                "limits": "—",
                "status": "INFO" # ### NUEVO ###
            }
        }
        print(f"   ✅ Estadísticas detalladas generadas. SNR={stats['signal_to_noise']['value']} ({stats['signal_to_noise']['status']})")
        return stats
    
    def _print_summary(self, results: Dict):
        """Imprime resumen formateado en consola."""
        print(f"\n{'='*70}")
        print("📊 RESUMEN DEL ANÁLISIS")
        print(f"{'='*70}")
        
        analysis = results.get("analysis", {})
        quality_metrics = results.get("quality_metrics", {})
        peaks = results.get("peaks", [])
        
        print(f"\n🧪 COMPOSICIÓN:")
        print(f"   Flúor Total (% Área):  {analysis.get('fluor_percentage', 'N/A'):>6.2f} %")
        print(f"   PFAS (% Flúor):        {analysis.get('pifas_percentage', 'N/A'):>6.2f} %")
        print(f"   Concentración PFAS:    {analysis.get('pifas_concentration', 'N/A'):>6.4f} mM")
        
        print(f"\n📈 ÁREAS INTEGRADAS:")
        print(f"   Área Total:            {analysis.get('total_area', 'N/A'):>10,.2f}")
        print(f"   Área Flúor:            {analysis.get('fluor_area', 'N/A'):>10,.2f}")
        print(f"   Área PFAS:             {analysis.get('pifas_area', 'N/A'):>10,.2f}")
        
        print(f"\n⭐ CALIDAD:")
        print(f"   Score Final:           {results.get('quality_score', 'N/A'):>6.1f} / 10")
        print(f"   SNR:                   {quality_metrics.get('snr', 'N/A'):>6.2f}")
        print(f"   Estabilidad Baseline:  {quality_metrics.get('baseline_stability_std', 'N/A'):>6.3f} (std)")
        
        print(f"\n🔍 PICOS DETECTADOS: {len(peaks)}")
        # Mostrar los 5 picos más intensos
        peaks_sorted_intensity = sorted(peaks, key=lambda x: x["intensity"], reverse=True)
        for i, peak in enumerate(peaks_sorted_intensity[:5], 1):
            print(f"   {i}. {peak.get('ppm', ''):>8.3f} ppm | Int: {peak.get('intensity', ''):>7.1f} | Área: {peak.get('area', 'N/A'):>7.2f} | Ancho: {peak.get('width_ppm', ''):>5.3f} ppm")
        
        print(f"\n{'='*70}\n")

# ============================================================================
# Modo standalone (sin cambios significativos, se mantiene como estaba)
# ============================================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("🔬 ANALIZADOR DE ESPECTROS RMN - DETECCIÓN DE PFAS (v2.2)")
        print("="*70)
        print("\nUso: python analyzer.py <archivo.csv> [opciones]")
        print("\nEjemplo:")
        print("   python analyzer.py spectrum_001.csv")
        print("   python analyzer.py data.csv --concentration 2.5 --no-baseline")
        print("\nOpciones:")
        print("   --concentration <value>   : Concentración en mM (default: 1.0)")
        print("   --no-baseline             : Desactivar corrección de baseline")
        print("="*70 + "\n")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Parsear argumentos opcionales
    concentration = 1.0
    baseline_correction = True
    
    args = sys.argv[2:] # Empezar desde el tercer argumento
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--concentration":
            if i + 1 < len(args):
                try:
                    concentration = float(args[i + 1])
                    i += 1 # Saltar el valor
                except ValueError:
                    print(f"❌ Error: Valor inválido para --concentration: {args[i+1]}")
                    sys.exit(1)
            else:
                 print("❌ Error: Falta el valor para --concentration")
                 sys.exit(1)
        elif arg == "--no-baseline":
            baseline_correction = False
        else:
             print(f"⚠️ Advertencia: Argumento desconocido '{arg}' ignorado.")
        i += 1
    
    # Analizar
    analyzer = SpectrumAnalyzer()
    try:
         results = analyzer.analyze_file(
             file_path,
             concentration=concentration,
             baseline_correction=baseline_correction
         )
    except Exception as e:
         print(f"\n❌ Ocurrió un error fatal durante el análisis: {e}")
         sys.exit(1)

    # Verificar si hubo un error devuelto por analyze_file (ej. no data points)
    if "error" in results:
         print(f"❌ Error en el análisis: {results['error']}")
         sys.exit(1)

    
    # Guardar resultados JSON
    output_file = file_path.parent / f"{file_path.stem}_analysis_v2.json"
    try:
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados JSON guardados en: {output_file}")
    except Exception as e:
         print(f"❌ Error al guardar el archivo JSON: {e}")

    
    # Guardar resumen CSV
    csv_output = file_path.parent / f"{file_path.stem}_summary_v2.csv"
    try:
        with open(csv_output, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Parámetro", "Valor", "Unidad"])
            writer.writerow(["Archivo", file_path.name, ""])
            # Extraer valores de forma segura con .get()
            analysis = results.get("analysis", {})
            quality = results.get("quality_metrics", {})
            peaks_list = results.get("peaks", [])
            writer.writerow(["Flúor Total (% Área)", analysis.get("fluor_percentage", "N/A"), "%"])
            writer.writerow(["PFAS (% Flúor)", analysis.get("pifas_percentage", "N/A"), "%"])
            writer.writerow(["Concentración PFAS", analysis.get("pifas_concentration", "N/A"), "mM"])
            writer.writerow(["Calidad (Score)", results.get("quality_score", "N/A"), "/10"])
            writer.writerow(["SNR", quality.get("snr", "N/A"), ""])
            writer.writerow(["Picos detectados", len(peaks_list), ""])
            writer.writerow(["Estabilidad Baseline (std)", quality.get("baseline_stability_std", "N/A"), "a.u."])

        print(f"💾 Resumen CSV guardado en: {csv_output}")
    except Exception as e:
         print(f"❌ Error al guardar el archivo CSV: {e}")

    print(f"\n✅ ANÁLISIS COMPLETADO\n")