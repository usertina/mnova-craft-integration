import csv
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

class SpectrumAnalyzer:
    """
    Analizador de espectros RMN para detección de PFAS
    
    PFAS (Per- and Polyfluoroalkyl Substances) son compuestos orgánicos
    que contienen enlaces carbono-flúor. En espectroscopia de RMN de flúor (19F),
    estos compuestos aparecen típicamente en el rango de -60 a -130 ppm.
    """
    
    def __init__(self):
        self.ppm_data = []
        self.intensity_data = []
        self.analysis_results = {}
    
    def analyze_file(self, file_path: Path, 
                    fluor_range: Dict = None,
                    pifas_range: Dict = None,
                    concentration: float = 1.0) -> Dict:
        """
        Analiza un archivo de espectro RMN
        
        Args:
            file_path: Ruta al archivo CSV
            fluor_range: Rango de ppm para flúor total {"min": -150, "max": -50}
            pifas_range: Rango de ppm para PFAS/PIFAS {"min": -60, "max": -130}
            concentration: Concentración de la muestra en mM
        
        Returns:
            Dict con resultados del análisis
        """
        # Configuración por defecto
        if fluor_range is None:
            fluor_range = {"min": -150, "max": -50}
        if pifas_range is None:
            pifas_range = {"min": -130, "max": -60}  # Rango típico PFAS
        
        print(f"📊 Analizando: {file_path.name}")
        print(f"   Rango Flúor: {fluor_range['min']} a {fluor_range['max']} ppm")
        print(f"   Rango PIFAS: {pifas_range['min']} a {pifas_range['max']} ppm")
        
        # Leer archivo
        self._read_spectrum(file_path)
        
        # Realizar análisis
        results = {
            "filename": file_path.name,
            "timestamp": Path(file_path).stat().st_mtime,
            "parameters": {
                "fluor_range": fluor_range,
                "pifas_range": pifas_range,
                "concentration": concentration
            },
            "spectrum": {
                "ppm": self.ppm_data,
                "intensity": self.intensity_data,
                "data_points": len(self.ppm_data)
            },
            "analysis": self._calculate_analysis(fluor_range, pifas_range, concentration),
            "peaks": self._detect_peaks(),
            "quality_score": self._calculate_quality_score(),
            "detailed_analysis": self._detailed_analysis(fluor_range, pifas_range)
        }
        
        return results
    
    def _read_spectrum(self, file_path: Path):
        """Lee archivo CSV con datos del espectro"""
        self.ppm_data = []
        self.intensity_data = []
        
        with open(file_path, 'r') as f:
            # Detectar si tiene encabezado
            first_line = f.readline().strip()
            f.seek(0)
            
            has_header = not self._is_numeric_line(first_line)
            
            reader = csv.reader(f)
            
            if has_header:
                next(reader)  # Saltar encabezado
            
            for row in reader:
                if len(row) >= 2:
                    try:
                        ppm = float(row[0].strip())
                        intensity = float(row[1].strip())
                        self.ppm_data.append(ppm)
                        self.intensity_data.append(intensity)
                    except ValueError:
                        continue
        
        print(f"   ✓ Leídos {len(self.ppm_data)} puntos de datos")
    
    def _is_numeric_line(self, line: str) -> bool:
        """Verifica si una línea contiene datos numéricos"""
        try:
            values = line.split(',')
            float(values[0])
            return True
        except:
            return False
    
    def _calculate_analysis(self, fluor_range: Dict, pifas_range: Dict, 
                           concentration: float) -> Dict:
        """Calcula análisis principal: % Flúor, % PFAS, Concentración"""
        
        # Convertir a numpy arrays para cálculos eficientes
        ppm = np.array(self.ppm_data)
        intensity = np.array(self.intensity_data)
        
        # 1. FLÚOR TOTAL - Integrar en el rango completo de flúor
        fluor_mask = (ppm >= fluor_range["min"]) & (ppm <= fluor_range["max"])
        fluor_intensity = intensity[fluor_mask]
        fluor_area = np.trapz(fluor_intensity) if len(fluor_intensity) > 0 else 0
        
        # 2. PFAS - Integrar en el rango específico de PFAS
        # IMPORTANTE: En RMN 19F, PFAS típicamente aparecen entre -60 y -130 ppm
        pifas_mask = (ppm >= pifas_range["min"]) & (ppm <= pifas_range["max"])
        pifas_intensity = intensity[pifas_mask]
        pifas_area = np.trapz(pifas_intensity) if len(pifas_intensity) > 0 else 0
        
        # 3. CALCULAR PORCENTAJES
        total_area = np.trapz(intensity)
        
        fluor_percentage = (fluor_area / total_area * 100) if total_area > 0 else 0
        pifas_percentage = (pifas_area / fluor_area * 100) if fluor_area > 0 else 0
        
        # 4. CONCENTRACIÓN DE PFAS
        # Concentración de PFAS = Concentración total × (% PFAS / 100)
        pifas_concentration = concentration * (pifas_percentage / 100)
        
        print(f"   ✓ Flúor: {fluor_percentage:.2f}%")
        print(f"   ✓ PFAS: {pifas_percentage:.2f}% del flúor")
        print(f"   ✓ Concentración PFAS: {pifas_concentration:.4f} mM")
        
        return {
            "fluor_percentage": round(fluor_percentage, 2),
            "pifas_percentage": round(pifas_percentage, 2),
            "pifas_concentration": round(pifas_concentration, 4),
            "concentration": concentration,
            "total_area": float(total_area),
            "fluor_area": float(fluor_area),
            "pifas_area": float(pifas_area)
        }
    
    def _detect_peaks(self) -> List[Dict]:
        """Detecta picos significativos en el espectro"""
        if len(self.intensity_data) < 3:
            return []
        
        intensity = np.array(self.intensity_data)
        ppm = np.array(self.ppm_data)
        
        # Encontrar máximos locales
        peaks = []
        threshold = np.mean(intensity) + np.std(intensity)
        
        for i in range(1, len(intensity) - 1):
            if intensity[i] > intensity[i-1] and intensity[i] > intensity[i+1]:
                if intensity[i] > threshold:
                    peaks.append({
                        "ppm": round(float(ppm[i]), 2),
                        "intensity": round(float(intensity[i]), 2),
                        "relative_intensity": round(float(intensity[i] / np.max(intensity) * 100), 1)
                    })
        
        # Ordenar por intensidad descendente
        peaks.sort(key=lambda x: x["intensity"], reverse=True)
        
        print(f"   ✓ Detectados {len(peaks)} picos")
        
        return peaks[:10]  # Top 10 picos
    
    def _calculate_quality_score(self) -> float:
        """Calcula un score de calidad del espectro (0-10)"""
        if len(self.intensity_data) == 0:
            return 0.0
        
        intensity = np.array(self.intensity_data)
        
        # Factores de calidad
        score = 10.0
        
        # 1. Número de puntos de datos
        if len(intensity) < 100:
            score -= 2.0
        
        # 2. Rango dinámico
        signal_range = np.max(intensity) - np.min(intensity)
        if signal_range < 100:
            score -= 1.5
        
        # 3. Relación señal/ruido (estimación simple)
        noise_estimate = np.std(intensity[intensity < np.percentile(intensity, 10)])
        signal = np.max(intensity)
        snr = signal / noise_estimate if noise_estimate > 0 else 100
        
        if snr < 10:
            score -= 2.0
        elif snr < 50:
            score -= 1.0
        
        # 4. Variabilidad de la señal
        unique_values = len(np.unique(intensity.astype(int)))
        if unique_values < 10:
            score -= 1.5
        
        return max(0.0, min(10.0, score))
    
    def _detailed_analysis(self, fluor_range: Dict, pifas_range: Dict) -> Dict:
        """Análisis detallado adicional"""
        ppm = np.array(self.ppm_data)
        intensity = np.array(self.intensity_data)
        
        return {
            "ppm_range": {
                "value": f"{np.min(ppm):.2f} to {np.max(ppm):.2f}",
                "unit": "ppm",
                "limits": f"{fluor_range['min']} to {fluor_range['max']}"
            },
            "intensity_range": {
                "value": f"{np.min(intensity):.2f} to {np.max(intensity):.2f}",
                "unit": "a.u.",
                "limits": "N/A"
            },
            "mean_intensity": {
                "value": round(float(np.mean(intensity)), 2),
                "unit": "a.u.",
                "limits": "N/A"
            },
            "std_intensity": {
                "value": round(float(np.std(intensity)), 2),
                "unit": "a.u.",
                "limits": "N/A"
            },
            "signal_to_noise": {
                "value": round(float(np.max(intensity) / np.std(intensity)), 2),
                "unit": "ratio",
                "limits": "> 10"
            }
        }


# ============================================================================
# Modo standalone - Procesar archivos individualmente
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python analyzer.py <archivo.csv>")
        print("\nEjemplo: python analyzer.py spectrum_001.csv")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Analizar
    analyzer = SpectrumAnalyzer()
    results = analyzer.analyze_file(file_path)
    
    # Guardar resultados
    output_file = file_path.parent / f"{file_path.stem}_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {output_file}")
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DEL ANÁLISIS")
    print("="*60)
    print(f"Flúor Total:       {results['analysis']['fluor_percentage']:.2f}%")
    print(f"PFAS:              {results['analysis']['pifas_percentage']:.2f}% del flúor")
    print(f"Concentración:     {results['analysis']['pifas_concentration']:.4f} mM")
    print(f"Calidad:           {results['quality_score']:.1f}/10")
    print(f"Picos detectados:  {len(results['peaks'])}")
    print("="*60)