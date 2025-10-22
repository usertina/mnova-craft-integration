import csv
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from scipy import signal
from scipy.interpolate import UnivariateSpline

class SpectrumAnalyzer:
    """
    Analizador mejorado de espectros RMN para detección de PFAS
    
    PFAS (Per- and Polyfluoroalkyl Substances) son compuestos orgánicos
    que contienen enlaces carbono-flúor. En espectroscopia de RMN de flúor (19F),
    estos compuestos aparecen típicamente en el rango de -60 a -130 ppm.
    
    Mejoras v2.0:
    - Corrección automática de baseline
    - Detección robusta de picos con scipy
    - Manejo de intensidades negativas
    - Mejor cálculo de SNR
    - Identificación de regiones de interés
    """
    
    def __init__(self):
        self.ppm_data = []
        self.intensity_data = []
        self.intensity_corrected = []
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
        
        # Corrección de baseline
        if baseline_correction:
            self._correct_baseline()
        else:
            self.intensity_corrected = self.intensity_data.copy()
        
        # ✅ Convertir arrays numpy a listas para JSON
        ppm_list = [float(x) for x in self.ppm_data]
        intensity_corrected_list = [float(x) for x in self.intensity_corrected]
        
        # Realizar análisis completo
        results = {
            "filename": file_path.name,
            "timestamp": Path(file_path).stat().st_mtime,
            "parameters": {
                "fluor_range": fluor_range,
                "pifas_range": pifas_range,
                "concentration": concentration,
                "baseline_correction": baseline_correction
            },
            # ✅ CORRECCIÓN: Agregar arrays completos para el gráfico
            "spectrum": {
                "ppm": ppm_list,
                "intensity": intensity_corrected_list,
                "ppm_min": float(np.min(self.ppm_data)),
                "ppm_max": float(np.max(self.ppm_data)),
                "data_points": len(self.ppm_data),
                "intensity_min": float(np.min(self.intensity_data)),
                "intensity_max": float(np.max(self.intensity_data)),
                "intensity_corrected_min": float(np.min(self.intensity_corrected)),
                "intensity_corrected_max": float(np.max(self.intensity_corrected))
            },
            "analysis": self._calculate_analysis(fluor_range, pifas_range, concentration),
            "peaks": self._detect_peaks_advanced(),
            "regions": self._analyze_regions(),
            "quality_metrics": self._calculate_quality_metrics(),
            "detailed_analysis": self._detailed_statistics(fluor_range, pifas_range)
        }
        
        # Calcular quality score final
        results["quality_score"] = self._calculate_quality_score_v2(results)
        
        self._print_summary(results)
        
        return results
    
    def _read_spectrum(self, file_path: Path):
        """Lee archivo CSV con datos del espectro, detectando automáticamente el delimitador."""
        self.ppm_data = []
        self.intensity_data = []
        
        try:
            with open(file_path, 'r') as f:
                sample = f.read(2048)
                f.seek(0)
                
                dialect = csv.Sniffer().sniff(sample, delimiters=',\t')
                has_header = csv.Sniffer().has_header(sample)
                
                reader = csv.reader(f, dialect)
                
                if has_header:
                    print("   ℹ️  Detectado encabezado, saltando primera línea")
                    next(reader)
                
                for row in reader:
                    if len(row) >= 2:
                        try:
                            ppm = float(row[0].strip())
                            intensity = float(row[1].strip())
                            self.ppm_data.append(ppm)
                            self.intensity_data.append(intensity)
                        except ValueError:
                            continue
            
            print(f"   ✅ Leídos {len(self.ppm_data):,} puntos de datos")
            print(f"   ℹ️  Delimitador detectado: '{dialect.delimiter}'")
            print(f"   ℹ️  Rango PPM: {min(self.ppm_data):.2f} a {max(self.ppm_data):.2f}")
            print(f"   ℹ️  Rango Intensidad original: {min(self.intensity_data):.2f} a {max(self.intensity_data):.2f}")

        except Exception as e:
            print(f"   ❌ Error al leer el archivo: {e}")
            raise

    def _correct_baseline(self):
        """
        Corrección de baseline usando el percentil inferior como referencia.
        Esto es crucial cuando hay offset negativo en las intensidades.
        """
        print("\n   🔧 Aplicando corrección de baseline...")
        
        intensity = np.array(self.intensity_data)
        
        # Método 1: Usar el percentil 5 como baseline (región sin señal)
        baseline = np.percentile(intensity, 5)
        
        # Método 2 alternativo: Usar la mediana de los valores más bajos
        low_values = intensity[intensity < np.percentile(intensity, 10)]
        baseline_median = np.median(low_values) if len(low_values) > 0 else baseline
        
        # Usar el promedio de ambos métodos para más robustez
        baseline_final = (baseline + baseline_median) / 2
        
        # Corregir: restar el baseline y asegurar valores >= 0
        self.intensity_corrected = intensity - baseline_final
        
        # Si aún hay valores negativos muy pequeños (ruido), llevarlos a 0
        self.intensity_corrected = np.maximum(self.intensity_corrected, 0)
        
        print(f"   ✅ Baseline detectado: {baseline_final:.2f} a.u.")
        print(f"   ✅ Rango corregido: {np.min(self.intensity_corrected):.2f} a {np.max(self.intensity_corrected):.2f} a.u.")
        print(f"   ✅ Intensidad media corregida: {np.mean(self.intensity_corrected):.2f} a.u.")
    
    def _calculate_analysis(self, fluor_range: Dict, pifas_range: Dict, 
                           concentration: float) -> Dict:
        """Calcula análisis principal: % Flúor, % PFAS, Concentración"""
        
        print("\n   📈 Calculando composición química...")
        
        ppm = np.array(self.ppm_data)
        intensity = np.array(self.intensity_corrected)
        
        # 1. ÁREA TOTAL DEL ESPECTRO
        total_area = np.trapz(intensity, ppm)
        
        # 2. FLÚOR TOTAL
        fluor_mask = (ppm >= fluor_range["min"]) & (ppm <= fluor_range["max"])
        fluor_intensity = intensity[fluor_mask]
        fluor_ppm = ppm[fluor_mask]
        fluor_area = np.trapz(fluor_intensity, fluor_ppm) if len(fluor_intensity) > 1 else 0
        
        # 3. PFAS
        pifas_mask = (ppm >= pifas_range["min"]) & (ppm <= pifas_range["max"])
        pifas_intensity = intensity[pifas_mask]
        pifas_ppm = ppm[pifas_mask]
        pifas_area = np.trapz(pifas_intensity, pifas_ppm) if len(pifas_intensity) > 1 else 0
        
        # 4. CALCULAR PORCENTAJES
        fluor_percentage = abs((fluor_area / total_area * 100)) if abs(total_area) > 1e-10 else 0
        pifas_percentage = abs((pifas_area / fluor_area * 100)) if abs(fluor_area) > 1e-10 else 0
        
        # 5. CONCENTRACIÓN DE PFAS
        pifas_concentration = concentration * (pifas_percentage / 100)
        
        # 6. CALCULAR NÚMERO DE ÁTOMOS DE FLÚOR (estimación)
        fluor_atoms_estimate = fluor_area / (np.max(intensity) + 1e-10)
        
        print(f"   ✅ Área total:         {total_area:.2f}")
        print(f"   ✅ Área flúor:         {fluor_area:.2f} ({fluor_percentage:.2f}%)")
        print(f"   ✅ Área PFAS:          {pifas_area:.2f} ({pifas_percentage:.2f}% del flúor)")
        print(f"   ✅ Concentración PFAS: {pifas_concentration:.4f} mM")
        
        return {
            "fluor_percentage": round(float(fluor_percentage), 2),
            "pifas_percentage": round(float(pifas_percentage), 2),
            "pifas_concentration": round(float(pifas_concentration), 4),
            "concentration": concentration,
            "total_area": round(float(total_area), 2),
            "fluor_area": round(float(fluor_area), 2),
            "pifas_area": round(float(pifas_area), 2),
            "fluor_atoms_estimate": round(float(fluor_atoms_estimate), 1)
        }
    
    def _detect_peaks_advanced(self) -> List[Dict]:
        """Detecta picos usando scipy.signal.find_peaks"""
        print("\n   🔍 Detectando picos significativos...")
        
        if len(self.intensity_corrected) < 5:
            return []
        
        intensity = np.array(self.intensity_corrected)
        ppm = np.array(self.ppm_data)
        
        # Parámetros para find_peaks
        prominence = np.std(intensity) * 2
        height = np.mean(intensity) + np.std(intensity)
        distance = len(intensity) // 100
        
        # Encontrar picos
        peak_indices, properties = signal.find_peaks(
            intensity,
            prominence=prominence,
            height=height,
            distance=max(distance, 5)
        )
        
        peaks = []
        max_intensity = np.max(intensity)
        
        for idx in peak_indices:
            peak_ppm = float(ppm[idx])
            peak_intensity = float(intensity[idx])
            
            # Estimar FWHM
            half_height = peak_intensity / 2
            left_idx = idx
            right_idx = idx
            
            while left_idx > 0 and intensity[left_idx] > half_height:
                left_idx -= 1
            while right_idx < len(intensity) - 1 and intensity[right_idx] > half_height:
                right_idx += 1
            
            fwhm = abs(float(ppm[right_idx] - ppm[left_idx]))
            
            region = self._classify_chemical_region(peak_ppm)
            
            peaks.append({
                "ppm": round(peak_ppm, 3),
                "intensity": round(peak_intensity, 2),
                "relative_intensity": round((peak_intensity / max_intensity * 100), 1),
                "fwhm": round(fwhm, 3),
                "region": region,
                "prominence": round(float(properties["prominences"][len(peaks)]), 2)
            })
        
        peaks.sort(key=lambda x: x["intensity"], reverse=True)
        
        print(f"   ✅ Detectados {len(peaks)} picos significativos")
        if len(peaks) > 0:
            print(f"   ✅ Pico principal: {peaks[0]['ppm']} ppm (intensidad: {peaks[0]['intensity']:.1f})")
        
        return peaks
    
    def _classify_chemical_region(self, ppm: float) -> str:
        """Clasifica la región química"""
        if -90 <= ppm <= -70:
            return "CF3 terminal"
        elif -115 <= ppm <= -90:
            return "CF2 interno"
        elif -130 <= ppm <= -115:
            return "CF2 α-carbonilo"
        elif ppm < -130:
            return "CF2 cadena larga"
        else:
            return "Otra región"
    
    def _analyze_regions(self) -> Dict:
        """Analiza regiones específicas del espectro"""
        ppm = np.array(self.ppm_data)
        intensity = np.array(self.intensity_corrected)
        
        regions = {
            "CF3_terminal": {"range": (-90, -70), "name": "CF₃ Terminal"},
            "CF2_internal": {"range": (-115, -90), "name": "CF₂ Interno"},
            "CF2_alpha": {"range": (-130, -115), "name": "CF₂ α-carbonilo"},
            "CF2_chain": {"range": (-150, -130), "name": "CF₂ Cadena Larga"}
        }
        
        results = {}
        total_area = np.trapz(intensity, ppm)
        
        for key, region_info in regions.items():
            min_ppm, max_ppm = region_info["range"]
            mask = (ppm >= min_ppm) & (ppm <= max_ppm)
            
            if np.any(mask):
                region_intensity = intensity[mask]
                region_ppm = ppm[mask]
                area = np.trapz(region_intensity, region_ppm)
                percentage = abs((area / total_area * 100)) if abs(total_area) > 1e-10 else 0
                max_int = np.max(region_intensity)
                
                results[key] = {
                    "name": region_info["name"],
                    "range_ppm": f"{min_ppm} to {max_ppm}",
                    "area": round(float(area), 2),
                    "percentage": round(float(percentage), 2),
                    "max_intensity": round(float(max_int), 2),
                    "points": int(np.sum(mask))
                }
        
        return results
    
    def _calculate_quality_metrics(self) -> Dict:
        """Calcula métricas de calidad del espectro"""
        intensity_orig = np.array(self.intensity_data)
        intensity = np.array(self.intensity_corrected)
        
        # SNR
        signal = np.max(intensity)
        noise_region = intensity[intensity < np.percentile(intensity, 10)]
        noise = np.std(noise_region) if len(noise_region) > 0 else 1e-10
        snr = signal / noise if noise > 0 else 100
        
        # Dynamic Range
        dynamic_range = (np.max(intensity) - np.min(intensity))
        
        # Baseline Stability
        baseline_std = np.std(noise_region) if len(noise_region) > 0 else 0
        
        # Data completeness
        data_density = len(self.ppm_data) / (abs(max(self.ppm_data) - min(self.ppm_data)))
        
        # Resolución espectral
        ppm_spacing = abs(self.ppm_data[1] - self.ppm_data[0]) if len(self.ppm_data) > 1 else 0
        
        return {
            "snr": round(float(snr), 2),
            "dynamic_range": round(float(dynamic_range), 2),
            "baseline_stability": round(float(baseline_std), 3),
            "data_density": round(float(data_density), 1),
            "spectral_resolution": round(float(ppm_spacing), 4),
            "total_points": len(self.ppm_data)
        }
    
    def _calculate_quality_score_v2(self, results: Dict) -> float:
        """Calcula score de calidad (0-10)"""
        score = 10.0
        metrics = results["quality_metrics"]
        
        # SNR
        snr = metrics["snr"]
        if snr < 5:
            score -= 3.0
        elif snr < 10:
            score -= 2.0
        elif snr < 20:
            score -= 1.0
        
        # Puntos de datos
        if metrics["total_points"] < 1000:
            score -= 2.0
        elif metrics["total_points"] < 10000:
            score -= 1.0
        
        # Dynamic Range
        if metrics["dynamic_range"] < 50:
            score -= 2.0
        elif metrics["dynamic_range"] < 100:
            score -= 1.0
        
        # Baseline Stability
        if metrics["baseline_stability"] > 10:
            score -= 2.0
        elif metrics["baseline_stability"] > 5:
            score -= 1.0
        
        # Picos detectados
        if len(results["peaks"]) < 1:
            score -= 1.0
        
        return round(max(0.0, min(10.0, score)), 1)
    
    def _detailed_statistics(self, fluor_range: Dict, pifas_range: Dict) -> Dict:
        """Estadísticas detalladas para el frontend"""
        ppm = np.array(self.ppm_data)
        intensity_orig = np.array(self.intensity_data)
        intensity = np.array(self.intensity_corrected)
        
        return {
            "ppm_range": {
                "parameter": "Rango PPM",
                "value": f"{np.min(ppm):.2f} to {np.max(ppm):.2f}",
                "unit": "ppm",
                "limits": f"{fluor_range['min']} to {fluor_range['max']}"
            },
            "intensity_range_original": {
                "parameter": "Rango Intensidad (original)",
                "value": f"{np.min(intensity_orig):.2f} to {np.max(intensity_orig):.2f}",
                "unit": "a.u.",
                "limits": "—"
            },
            "intensity_range_corrected": {
                "parameter": "Rango Intensidad (corregido)",
                "value": f"{np.min(intensity):.2f} to {np.max(intensity):.2f}",
                "unit": "a.u.",
                "limits": "—"
            },
            "mean_intensity": {
                "parameter": "Intensidad Media",
                "value": round(float(np.mean(intensity)), 4),
                "unit": "a.u.",
                "limits": "—"
            },
            "std_intensity": {
                "parameter": "Desviación Estándar",
                "value": round(float(np.std(intensity)), 4),
                "unit": "a.u.",
                "limits": "—"
            },
            "signal_to_noise": {
                "parameter": "Relación Señal/Ruido",
                "value": round(float(np.max(intensity) / max(np.std(intensity), 1e-10)), 4),
                "unit": "ratio",
                "limits": "> 10"
            },
            "max_signal": {
                "parameter": "Señal Máxima",
                "value": round(float(np.max(intensity)), 2),
                "unit": "a.u.",
                "limits": "—"
            }
        }
    
    def _print_summary(self, results: Dict):
        """Imprime resumen de resultados"""
        print(f"\n{'='*70}")
        print("📊 RESUMEN DEL ANÁLISIS")
        print(f"{'='*70}")
        
        analysis = results["analysis"]
        print(f"\n🧪 COMPOSICIÓN:")
        print(f"   Flúor Total:       {analysis['fluor_percentage']:>6.2f} %")
        print(f"   PFAS (del flúor):  {analysis['pifas_percentage']:>6.2f} %")
        print(f"   Concentración:     {analysis['pifas_concentration']:>6.4f} mM")
        
        print(f"\n📈 ÁREAS INTEGRADAS:")
        print(f"   Área Total:        {analysis['total_area']:>8.2f}")
        print(f"   Área Flúor:        {analysis['fluor_area']:>8.2f}")
        print(f"   Área PFAS:         {analysis['pifas_area']:>8.2f}")
        
        print(f"\n⭐ CALIDAD:")
        print(f"   Score:             {results['quality_score']:>6.1f} / 10")
        print(f"   SNR:               {results['quality_metrics']['snr']:>6.2f}")
        print(f"   Rango Dinámico:    {results['quality_metrics']['dynamic_range']:>6.2f}")
        
        print(f"\n🔍 PICOS DETECTADOS: {len(results['peaks'])}")
        for i, peak in enumerate(results['peaks'][:5], 1):
            print(f"   {i}. {peak['ppm']:>8.3f} ppm  |  Int: {peak['intensity']:>7.1f}  |  {peak['region']}")
        
        print(f"\n{'='*70}\n")


# ============================================================================
# Modo standalone
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("🔬 ANALIZADOR DE ESPECTROS RMN - DETECCIÓN DE PFAS")
        print("="*70)
        print("\nUso: python analyzer.py <archivo.csv> [opciones]")
        print("\nEjemplo:")
        print("  python analyzer.py spectrum_001.csv")
        print("  python analyzer.py data.csv --concentration 2.5")
        print("\nOpciones:")
        print("  --concentration <value>  : Concentración en mM (default: 1.0)")
        print("  --no-baseline           : Desactivar corrección de baseline")
        print("="*70 + "\n")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Parsear argumentos opcionales
    concentration = 1.0
    baseline_correction = True
    
    for i, arg in enumerate(sys.argv):
        if arg == "--concentration" and i + 1 < len(sys.argv):
            concentration = float(sys.argv[i + 1])
        elif arg == "--no-baseline":
            baseline_correction = False
    
    # Analizar
    analyzer = SpectrumAnalyzer()
    results = analyzer.analyze_file(
        file_path,
        concentration=concentration,
        baseline_correction=baseline_correction
    )
    
    # Guardar resultados
    output_file = file_path.parent / f"{file_path.stem}_analysis.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Resultados guardados en: {output_file}")
    
    # Guardar resumen CSV
    csv_output = file_path.parent / f"{file_path.stem}_summary.csv"
    with open(csv_output, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Parámetro", "Valor", "Unidad"])
        writer.writerow(["Archivo", file_path.name, ""])
        writer.writerow(["Flúor Total", results["analysis"]["fluor_percentage"], "%"])
        writer.writerow(["PFAS", results["analysis"]["pifas_percentage"], "%"])
        writer.writerow(["Concentración PFAS", results["analysis"]["pifas_concentration"], "mM"])
        writer.writerow(["Calidad", results["quality_score"], "/10"])
        writer.writerow(["SNR", results["quality_metrics"]["snr"], ""])
        writer.writerow(["Picos detectados", len(results["peaks"]), ""])
    
    print(f"💾 Resumen CSV guardado en: {csv_output}")
    print(f"\n✅ ANÁLISIS COMPLETADO\n")