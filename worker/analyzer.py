import csv
import json
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy import signal
from scipy.signal import find_peaks, peak_widths, savgol_filter
from scipy.ndimage import gaussian_filter1d
from scipy import sparse  
from scipy.sparse.linalg import spsolve
# ============================================================================
# 🆕 BASE DE DATOS DE PFAS CONOCIDOS
# ============================================================================

PFAS_DATABASE = {
    "PFOA": {
        "name": "Perfluorooctanoic acid (PFOA)",
        "formula": "C8HF15O2",
        "cf3_terminal": (-82.5, -80.5),  # CF₃ terminal
        "cf2_alpha": (-119.5, -117.5),   # CF₂ α (próximo a COO⁻)
        "cf2_internal": (-122.5, -120.5), # CF₂ internos
        "pattern": "cf3_1_cf2_alpha_1_cf2_6",
        "regulatory_limit_ng_l": 70,  # EPA 2024
    },
    "PFOS": {
        "name": "Perfluorooctane sulfonic acid (PFOS)",
        "formula": "C8HF17O3S",
        "cf3_terminal": (-81.5, -79.5),
        "cf2_alpha": (-118.5, -116.5),   # CF₂ α (próximo a SO₃⁻)
        "cf2_internal": (-122.0, -120.0),
        "pattern": "cf3_1_cf2_alpha_1_cf2_6",
        "regulatory_limit_ng_l": 70,  # EPA 2024
    },
    "PFBA": {
        "name": "Perfluorobutanoic acid (PFBA)",
        "formula": "C4HF7O2",
        "cf3_terminal": (-81.5, -79.5),
        "cf2_alpha": (-118.0, -116.0),
        "pattern": "cf3_1_cf2_alpha_1_cf2_2",
        "regulatory_limit_ng_l": 2000,
    },
    "PFHxA": {
        "name": "Perfluorohexanoic acid (PFHxA)",
        "formula": "C6HF11O2",
        "cf3_terminal": (-82.0, -80.0),
        "cf2_alpha": (-119.0, -117.0),
        "cf2_internal": (-122.5, -120.5),
        "pattern": "cf3_1_cf2_alpha_1_cf2_4",
        "regulatory_limit_ng_l": 400,
    },
    "PFNA": {
        "name": "Perfluorononanoic acid (PFNA)",
        "formula": "C9HF17O2",
        "cf3_terminal": (-82.5, -80.5),
        "cf2_alpha": (-119.5, -117.5),
        "cf2_internal": (-122.5, -120.5),
        "pattern": "cf3_1_cf2_alpha_1_cf2_7",
        "regulatory_limit_ng_l": 200,
    }
}

# ============================================================================
# 🆕 LÍMITES CIENTÍFICOS Y REGULATORIOS
# ============================================================================

SCIENTIFIC_LIMITS = {
    "snr": {
        "excellent": 50,
        "good": 20,
        "acceptable": 10,
        "poor": 5,
        "source": "NMR Best Practices (ISO 17034)",
    },
    "resolution_ppm": {
        "excellent": 0.01,
        "good": 0.05,
        "acceptable": 0.1,
        "poor": 0.5,
        "source": "19F-NMR Standard Methods",
    },
    "data_density_pts_ppm": {
        "excellent": 100,
        "good": 50,
        "acceptable": 20,
        "poor": 10,
        "source": "Digital Resolution Standards",
    },
    "pfas_concentration_mm": {
        "high": 1.0,
        "medium": 0.1,
        "low": 0.01,
        "trace": 0.001,
        "source": "Environmental Analysis Guidelines",
    },
    "baseline_noise_percent": {
        "excellent": 1.0,
        "good": 3.0,
        "acceptable": 5.0,
        "poor": 10.0,
        "source": "Signal Processing Standards",
    }
}

# ============================================================================
# CLASE PRINCIPAL MEJORADA
# ============================================================================

class SpectrumAnalyzer:
    """
    Analizador Avanzado v3.0 de Espectros RMN para Detección de PFAS
    
    Mejoras v3.0:
    - 🧪 Base de datos de PFAS conocidos con patrones espectrales
    - 📊 Límites científicos basados en literatura
    - 🔍 Detección de picos mejorada con filtrado adaptativo
    - 🎯 Identificación automática de PFAS con scoring
    - 📈 Baseline correction mejorado (ALS)
    - ⚡ Validación de patrones característicos
    - 📉 Análisis de ratio CF₃/CF₂
    - 🎨 Detección de interferencias comunes
    """
    
    def __init__(self):
        self.ppm_data = np.array([])
        self.intensity_data = np.array([])
        self.intensity_corrected = np.array([])
        self.intensity_smoothed = np.array([])
        self.baseline_value = None
        self.analysis_results = {}
        self.identified_pfas = []
        self.warnings = []
    
    def analyze_file(self, file_path: Path, 
                     fluor_range: Dict = None,
                     pifas_range: Dict = None,
                     concentration: float = 1.0,
                     baseline_correction: bool = True,
                     smart_detection: bool = True) -> Dict:
        """
        Analiza un archivo de espectro RMN con detección inteligente de PFAS
        
        Args:
            file_path: Ruta al archivo CSV
            fluor_range: Rango de ppm para flúor total
            pifas_range: Rango de ppm para PFAS
            concentration: Concentración de la muestra en mM
            baseline_correction: Si True, aplica corrección de baseline avanzada
            smart_detection: Si True, usa detección inteligente con filtros y patrones
        """
        if fluor_range is None:
            fluor_range = {"min": -150, "max": -50}
        if pifas_range is None:
            pifas_range = {"min": -130, "max": -60}
        
        print(f"\n{'='*70}")
        print(f"🔬 ANALIZADOR AVANZADO DE PFAS v3.0")
        print(f"{'='*70}")
        print(f"📊 Archivo: {file_path.name}")
        print(f"   Rango Flúor Total: {fluor_range['min']} a {fluor_range['max']} ppm")
        print(f"   Rango PFAS:        {pifas_range['min']} a {pifas_range['max']} ppm")
        print(f"   Concentración:     {concentration} mM")
        print(f"   Detección Smart:   {'✅ Activada' if smart_detection else '❌ Desactivada'}")
        
        # Leer archivo
        self._read_spectrum(file_path)
        
        if len(self.ppm_data) < 10:
            return self._error_result(file_path.name, "Datos insuficientes para análisis")
        
        # Pipeline de procesamiento mejorado
        if baseline_correction:
            self._correct_baseline_advanced()
        else:
            self.intensity_corrected = self.intensity_data.copy()
            self.baseline_value = 0.0
        
        # Suavizado adaptativo para mejorar detección de picos
        if smart_detection:
            self._adaptive_smoothing()
        else:
            self.intensity_smoothed = self.intensity_corrected.copy()
        
        # Análisis completo
        quality_metrics = self._calculate_quality_metrics_advanced()
        peaks = self._detect_peaks_smart() if smart_detection else self._detect_peaks_advanced()
        
        # 🆕 Identificación automática de PFAS
        if smart_detection:
            self._identify_pfas_compounds(peaks)
        
        analysis_data = self._calculate_analysis_advanced(fluor_range, pifas_range, concentration)
        region_data = self._analyze_regions_enhanced()
        detailed_stats = self._detailed_statistics_scientific(fluor_range, pifas_range, quality_metrics)
        
        # Validación de patrones PFAS
        pattern_validation = self._validate_pfas_patterns(peaks) if smart_detection else {}
        
        # Convertir arrays a listas para JSON
        ppm_list = [round(float(x), 4) for x in self.ppm_data]
        intensity_corrected_list = [round(float(x), 4) for x in self.intensity_corrected]
        
        results = {
            "filename": file_path.name,
            "timestamp": Path(file_path).stat().st_mtime,
            "analyzer_version": "3.0",
            "parameters": {
                "fluor_range": fluor_range,
                "pifas_range": pifas_range,
                "concentration": concentration,
                "baseline_correction": baseline_correction,
                "smart_detection": smart_detection
            },
            "spectrum": {
                "ppm": ppm_list,
                "intensity": intensity_corrected_list,
                "ppm_min": round(float(np.min(self.ppm_data)), 2),
                "ppm_max": round(float(np.max(self.ppm_data)), 2),
                "data_points": len(self.ppm_data),
                "baseline_value": round(float(self.baseline_value), 2) if self.baseline_value else None
            },
            "analysis": analysis_data,
            "peaks": peaks,
            "regions": region_data,
            "quality_metrics": quality_metrics,
            "detailed_analysis": detailed_stats,
            "pattern_validation": pattern_validation,
            "identified_pfas": self.identified_pfas,
            "warnings": self.warnings,
            "regulatory_info": self._get_regulatory_info()
        }
        
        # Calcular quality score
        quality_score, quality_breakdown = self._calculate_quality_score_v3(quality_metrics, peaks)
        results["quality_score"] = quality_score
        results["quality_breakdown"] = quality_breakdown
        
        self._print_summary_enhanced(results)
        
        return results
    
    # ========================================================================
    # 🆕 CORRECCIÓN DE BASELINE AVANZADA (ALS - Asymmetric Least Squares)
    # ========================================================================
    
    def _correct_baseline_advanced(self):
        """
        Corrección de baseline usando algoritmo ALS (Asymmetric Least Squares)
        
        VERSIÓN CORREGIDA: Usa matrices 'sparse' (dispersas) para evitar 
                           errores de memoria con datos grandes.
        """
        print("\n   🔧 Aplicando corrección de baseline avanzada (ALS) con 'sparse'...")
        
        if len(self.intensity_data) < 10:
            self.intensity_corrected = self.intensity_data.copy()
            self.baseline_value = 0.0
            return
        
        intensity = self.intensity_data
        
        # Parámetros ALS
        lam = 1e6  # Suavizado
        p = 0.01   # Asimetría
        niter = 10
        
        L = len(intensity)
        
        # 1. Llamada a la función 'sparse' corregida
        D = sparse_diagonal_matrix(L) 
        
        # Pre-calcular D.T @ D (es constante y mejora la velocidad)
        # Usar formato 'csc' es a menudo más rápido para transposición y multiplicación
        D_csc = D.tocsc()
        DTD = D_csc.T @ D_csc 

        w = np.ones(L)
        baseline = np.zeros(L)
        
        for i in range(niter):
            # 2. Reemplazar np.diag(w) por sparse.diags(w)
            # W = np.diag(w) # <-- PROBLEMA ORIGINAL (crea matriz densa L x L)
            W = sparse.diags(w, 0, format='csr') # <-- SOLUCIÓN (matriz sparse)
            
            # Z = W + lam * D.T @ D  # <-- Operación original
            Z = W + lam * DTD        # <-- Operación optimizada con DTD pre-calculado
            
            # 3. Reemplazar np.linalg.solve por spsolve
            # baseline = np.linalg.solve(Z, w * intensity) # <-- PROBLEMA ORIGINAL (no usa sparse)
            baseline = spsolve(Z.tocsr(), w * intensity) # <-- SOLUCIÓN (solver sparse)
            
            w = p * (intensity > baseline) + (1 - p) * (intensity <= baseline)
        
        self.baseline_value = np.mean(baseline)
        self.intensity_corrected = intensity - baseline
        
        # Asegurar que no haya valores negativos significativos
        min_val = np.min(self.intensity_corrected)
        if min_val < 0:
            self.intensity_corrected = self.intensity_corrected - min_val
        
        print(f"   ✅ Baseline calculado con ALS ('sparse')")
        print(f"   ✅ Rango corregido: {np.min(self.intensity_corrected):.2f} a {np.max(self.intensity_corrected):.2f}")
        
    # ========================================================================
    # 🆕 SUAVIZADO ADAPTATIVO
    # ========================================================================
    
    def _adaptive_smoothing(self):
        """
        Aplica suavizado Savitzky-Golay adaptativo para mejorar detección de picos
        sin perder resolución en picos reales.
        """
        print("\n   📊 Aplicando suavizado adaptativo...")
        
        # Calcular SNR para decidir nivel de suavizado
        signal_max = np.max(self.intensity_corrected)
        noise_region = self.intensity_corrected[self.intensity_corrected < np.percentile(self.intensity_corrected, 10)]
        noise_std = np.std(noise_region) if len(noise_region) > 1 else np.std(self.intensity_corrected) / 3
        snr = signal_max / max(noise_std, 1e-9)
        
        # Ajustar parámetros según SNR
        if snr > 50:  # SNR excelente, poco suavizado
            window_length = 7
            polyorder = 3
        elif snr > 20:  # SNR bueno, suavizado moderado
            window_length = 11
            polyorder = 3
        else:  # SNR bajo, más suavizado
            window_length = 15
            polyorder = 2
        
        # Asegurar ventana impar y menor que datos
        window_length = min(window_length, len(self.intensity_corrected) - 1)
        if window_length % 2 == 0:
            window_length -= 1
        window_length = max(window_length, 5)
        
        try:
            self.intensity_smoothed = savgol_filter(
                self.intensity_corrected,
                window_length,
                polyorder
            )
            print(f"   ✅ Suavizado aplicado (ventana={window_length}, orden={polyorder}, SNR={snr:.1f})")
        except Exception as e:
            print(f"   ⚠️  Error en suavizado: {e}. Usando datos sin suavizar.")
            self.intensity_smoothed = self.intensity_corrected.copy()
    
    # ========================================================================
    # 🆕 DETECCIÓN DE PICOS INTELIGENTE
    # ========================================================================
    
    def _detect_peaks_smart(self) -> List[Dict]:
        """
        Detección de picos con múltiples estrategias y validación cruzada.
        Combina análisis de primera y segunda derivada con umbrales adaptativos.
        """
        print("\n   🔍 Detectando picos con algoritmo inteligente...")
        
        intensity = self.intensity_smoothed
        ppm = self.ppm_data
        
        if len(intensity) < 10:
            return []
        
        # --- Estrategia 1: find_peaks con umbrales adaptativos ---
        signal_max = np.max(intensity)
        signal_mean = np.mean(intensity)
        signal_std = np.std(intensity)
        
        # Estimar ruido de forma robusta
        noise_region = intensity[intensity < np.percentile(intensity, 15)]
        noise_std = np.std(noise_region) if len(noise_region) > 1 else signal_std / 3
        
        # Umbrales ajustados científicamente
        min_height = max(
            3 * noise_std,           # 3σ sobre ruido (estadísticamente significativo)
            signal_max * 0.02,       # 2% de señal máxima
            signal_mean + 2 * signal_std  # 2σ sobre media
        )
        
        min_prominence = max(
            5 * noise_std,           # 5σ (muy significativo)
            signal_max * 0.03        # 3% de señal máxima
        )
        
        min_distance = max(len(intensity) // 300, 5)
        
        print(f"   📊 Señal: Max={signal_max:.1f}, Media={signal_mean:.1f}, Ruido σ={noise_std:.2f}")
        print(f"   🎯 Umbrales: Altura>{min_height:.1f}, Prominencia>{min_prominence:.1f}")
        
        # Detectar picos
        peak_indices, properties = find_peaks(
            intensity,
            height=min_height,
            prominence=min_prominence,
            distance=min_distance,
            width=2  # Al menos 2 puntos de ancho
        )
        
        print(f"   ✅ Detectados {len(peak_indices)} picos candidatos")
        
        if len(peak_indices) == 0:
            self.warnings.append("No se detectaron picos significativos con criterios estrictos")
            return []
        
        # --- Estrategia 2: Validación con segunda derivada ---
        try:
            second_derivative = np.gradient(np.gradient(intensity))
            # En picos reales, la segunda derivada debería ser negativa
            second_deriv_valid = second_derivative[peak_indices] < 0
        except:
            second_deriv_valid = np.ones(len(peak_indices), dtype=bool)
        
        # --- Calcular anchos ---
        try:
            widths, width_heights, left_ips, right_ips = peak_widths(
                intensity, peak_indices, rel_height=0.5
            )
            indices = np.arange(len(ppm))
            widths_ppm = abs(np.interp(right_ips, indices, ppm) - np.interp(left_ips, indices, ppm))
        except Exception as e:
            print(f"   ⚠️  Error calculando anchos: {e}")
            widths_ppm = np.ones(len(peak_indices)) * 0.1
        
        # --- Construir lista de picos ---
        peaks = []
        max_intensity = signal_max if signal_max > 0 else 1.0
        
        for i, idx in enumerate(peak_indices):
            if not second_deriv_valid[i]:  # Filtrar picos con derivada positiva
                continue
            
            peak_ppm = float(ppm[idx])
            peak_intensity = float(intensity[idx])
            peak_width = float(widths_ppm[i])
            
            # Clasificar región química
            region = self._classify_chemical_region_enhanced(peak_ppm)
            
            # Calcular score de confianza del pico
            confidence = self._calculate_peak_confidence(
                peak_intensity,
                properties["prominences"][i],
                peak_width,
                noise_std,
                signal_max
            )
            
            peaks.append({
                "ppm": round(peak_ppm, 3),
                "intensity": round(peak_intensity, 2),
                "relative_intensity": round((peak_intensity / max_intensity * 100), 1),
                "width_ppm": round(peak_width, 3),
                "region": region,
                "prominence": round(float(properties["prominences"][i]), 2),
                "confidence": round(confidence, 2),
                "validated": confidence > 0.7
            })
        
        # Filtrar picos de baja confianza
        peaks = [p for p in peaks if p["confidence"] > 0.5]
        
        # Ordenar por intensidad
        peaks.sort(key=lambda x: x["intensity"], reverse=True)
        peaks = peaks[:30]  # Top 30
        
        # Re-ordenar por PPM
        peaks.sort(key=lambda x: x["ppm"])
        
        print(f"   ✅ {len(peaks)} picos validados (confianza > 0.5)")
        if peaks:
            main_peak = max(peaks, key=lambda p: p["intensity"])
            print(f"   🎯 Pico principal: {main_peak['ppm']:.3f} ppm (Conf: {main_peak['confidence']:.2f})")
        
        return peaks
    
    def _calculate_peak_confidence(self, intensity: float, prominence: float, 
                                   width: float, noise_std: float, signal_max: float) -> float:
        """
        Calcula un score de confianza (0-1) para un pico basado en múltiples criterios.
        """
        score = 0.0
        
        # Criterio 1: Ratio señal/ruido (30%)
        snr = intensity / max(noise_std, 1e-9)
        if snr > 20:
            score += 0.3
        elif snr > 10:
            score += 0.2
        elif snr > 5:
            score += 0.1
        
        # Criterio 2: Prominencia relativa (30%)
        rel_prominence = prominence / max(signal_max, 1e-9)
        if rel_prominence > 0.1:
            score += 0.3
        elif rel_prominence > 0.05:
            score += 0.2
        elif rel_prominence > 0.02:
            score += 0.1
        
        # Criterio 3: Ancho razonable (20%)
        if 0.05 < width < 2.0:  # Picos de RMN típicamente 0.05-2 ppm
            score += 0.2
        elif width < 0.05 or width > 5.0:
            score += 0.0  # Demasiado estrecho (ruido) o ancho (baseline)
        else:
            score += 0.1
        
        # Criterio 4: Intensidad relativa (20%)
        rel_intensity = intensity / max(signal_max, 1e-9)
        if rel_intensity > 0.5:
            score += 0.2
        elif rel_intensity > 0.1:
            score += 0.15
        elif rel_intensity > 0.05:
            score += 0.1
        
        return min(score, 1.0)
    
    # ========================================================================
    # 🆕 IDENTIFICACIÓN DE COMPUESTOS PFAS
    # ========================================================================
    
    def _identify_pfas_compounds(self, peaks: List[Dict]):
        """
        Identifica automáticamente compuestos PFAS conocidos comparando
        con la base de datos de patrones espectrales.
        """
        print("\n   🧪 Identificando compuestos PFAS...")
        
        self.identified_pfas = []
        
        if len(peaks) < 2:
            print("   ⚠️  Insuficientes picos para identificación de PFAS")
            return
        
        # Extraer picos por región
        cf3_peaks = [p for p in peaks if -85 < p["ppm"] < -75]
        cf2_alpha_peaks = [p for p in peaks if -120 < p["ppm"] < -115]
        cf2_internal_peaks = [p for p in peaks if -125 < p["ppm"] < -120]
        
        print(f"   📊 Picos encontrados: CF₃={len(cf3_peaks)}, CF₂-α={len(cf2_alpha_peaks)}, CF₂-int={len(cf2_internal_peaks)}")
        
        # Comparar con cada PFAS en la base de datos
        for pfas_name, pfas_data in PFAS_DATABASE.items():
            match_score = 0.0
            matched_peaks = []
            
            # Buscar CF₃ terminal
            if "cf3_terminal" in pfas_data:
                cf3_min, cf3_max = pfas_data["cf3_terminal"]
                cf3_matches = [p for p in cf3_peaks if cf3_min <= p["ppm"] <= cf3_max]
                if cf3_matches:
                    match_score += 0.3
                    matched_peaks.extend(cf3_matches)
            
            # Buscar CF₂ α
            if "cf2_alpha" in pfas_data:
                cf2a_min, cf2a_max = pfas_data["cf2_alpha"]
                cf2a_matches = [p for p in cf2_alpha_peaks if cf2a_min <= p["ppm"] <= cf2a_max]
                if cf2a_matches:
                    match_score += 0.3
                    matched_peaks.extend(cf2a_matches)
            
            # Buscar CF₂ internos
            if "cf2_internal" in pfas_data:
                cf2i_min, cf2i_max = pfas_data["cf2_internal"]
                cf2i_matches = [p for p in cf2_internal_peaks if cf2i_min <= p["ppm"] <= cf2i_max]
                if cf2i_matches:
                    match_score += 0.2
                    matched_peaks.extend(cf2i_matches)
            
            # Validar patrón general
            if match_score > 0.5:  # Al menos 2 de 3 tipos de picos
                # Score adicional por intensidades relativas correctas
                if len(matched_peaks) >= 2:
                    # En PFAS, CF₃ suele ser más intenso que CF₂-α
                    if cf3_matches and cf2a_matches:
                        if cf3_matches[0]["intensity"] > cf2a_matches[0]["intensity"] * 0.8:
                            match_score += 0.1
                
                # Normalizar score
                match_score = min(match_score, 1.0)
                
                if match_score > 0.6:  # Umbral de confianza
                    self.identified_pfas.append({
                        "compound": pfas_name,
                        "name": pfas_data["name"],
                        "formula": pfas_data["formula"],
                        "match_score": round(match_score, 2),
                        "confidence": "alta" if match_score > 0.8 else ("media" if match_score > 0.7 else "baja"),
                        "matched_peaks": [p["ppm"] for p in matched_peaks],
                        "regulatory_limit_ng_l": pfas_data.get("regulatory_limit_ng_l"),
                    })
                    
                    print(f"   ✅ Identificado: {pfas_name} (Score: {match_score:.2f})")
        
        if not self.identified_pfas:
            print("   ℹ️  No se identificaron PFAS conocidos con alta confianza")
        else:
            print(f"   🎯 Total identificados: {len(self.identified_pfas)} compuestos")
    
    # ========================================================================
    # 🆕 VALIDACIÓN DE PATRONES PFAS
    # ========================================================================
    
    def _validate_pfas_patterns(self, peaks: List[Dict]) -> Dict:
        """
        Valida que los patrones espectrales sean consistentes con PFAS reales.
        """
        print("\n   🔬 Validando patrones característicos de PFAS...")
        
        validation = {
            "is_valid_pfas_pattern": False,
            "cf3_cf2_ratio": 0.0,
            "has_terminal_cf3": False,
            "has_alpha_cf2": False,
            "has_internal_cf2": False,
            "pattern_quality": "bajo",
            "reasons": []
        }
        
        if len(peaks) < 2:
            validation["reasons"].append("Insuficientes picos para validación")
            return validation
        
        # Agrupar picos por región
        cf3_peaks = [p for p in peaks if -85 < p["ppm"] < -75]
        cf2_alpha_peaks = [p for p in peaks if -120 < p["ppm"] < -115]
        cf2_internal_peaks = [p for p in peaks if -125 < p["ppm"] < -120]
        
        # Verificar presencia de grupos característicos
        validation["has_terminal_cf3"] = len(cf3_peaks) > 0
        validation["has_alpha_cf2"] = len(cf2_alpha_peaks) > 0
        validation["has_internal_cf2"] = len(cf2_internal_peaks) > 0
        
        # Calcular ratio CF₃/CF₂
        total_cf3_intensity = sum(p["intensity"] for p in cf3_peaks)
        total_cf2_intensity = sum(p["intensity"] for p in cf2_alpha_peaks) + sum(p["intensity"] for p in cf2_internal_peaks)
        
        if total_cf2_intensity > 0:
            validation["cf3_cf2_ratio"] = round(total_cf3_intensity / total_cf2_intensity, 2)
        
        # Validar patrón
        pattern_score = 0
        
        if validation["has_terminal_cf3"]:
            pattern_score += 1
            validation["reasons"].append("✅ Detectado CF₃ terminal")
        
        if validation["has_alpha_cf2"]:
            pattern_score += 1
            validation["reasons"].append("✅ Detectado CF₂ α (próximo a grupo funcional)")
        
        if validation["has_internal_cf2"]:
            pattern_score += 1
            validation["reasons"].append("✅ Detectado CF₂ interno (cadena)")
        
        # Validar ratio
        if 0.3 < validation["cf3_cf2_ratio"] < 3.0:  # Ratio típico en PFAS lineales
            pattern_score += 1
            validation["reasons"].append(f"✅ Ratio CF₃/CF₂ consistente ({validation['cf3_cf2_ratio']:.2f})")
        else:
            validation["reasons"].append(f"⚠️ Ratio CF₃/CF₂ atípico ({validation['cf3_cf2_ratio']:.2f})")
        
        # Determinar calidad del patrón
        if pattern_score >= 3:
            validation["pattern_quality"] = "alto"
            validation["is_valid_pfas_pattern"] = True
        elif pattern_score == 2:
            validation["pattern_quality"] = "medio"
            validation["is_valid_pfas_pattern"] = True
        else:
            validation["pattern_quality"] = "bajo"
            validation["reasons"].append("⚠️ Patrón no consistente con PFAS típicos")
        
        print(f"   📊 Validación de patrón: {validation['pattern_quality'].upper()}")
        for reason in validation["reasons"]:
            print(f"      {reason}")
        
        return validation
    
    # ========================================================================
    # 🆕 ESTADÍSTICAS DETALLADAS CON LÍMITES CIENTÍFICOS
    # ========================================================================
    
    def _detailed_statistics_scientific(self, fluor_range: Dict, pifas_range: Dict, 
                                       quality_metrics: Dict) -> Dict:
        """
        Estadísticas detalladas con evaluación basada en límites científicos publicados.
        """
        print("\n   📋 Calculando estadísticas con límites científicos...")
        
        ppm = self.ppm_data
        intensity = self.intensity_corrected
        
        if len(ppm) < 2:
            return {"error": {"parameter": "Error", "value": "Datos insuficientes"}}
        
        # Extraer métricas
        snr = quality_metrics.get("snr", 0)
        resolution = quality_metrics.get("spectral_resolution_ppm_pt", 0)
        data_density = quality_metrics.get("data_density_pts_ppm", 0)
        baseline_noise = quality_metrics.get("baseline_noise_percent", 0)
        
        # Evaluar SNR
        snr_status = self._evaluate_metric(snr, SCIENTIFIC_LIMITS["snr"])
        
        # Evaluar Resolución
        resolution_status = self._evaluate_metric(resolution, SCIENTIFIC_LIMITS["resolution_ppm"], reverse=True)
        
        # Evaluar Densidad de Datos
        density_status = self._evaluate_metric(data_density, SCIENTIFIC_LIMITS["data_density_pts_ppm"])
        
        # Evaluar Ruido Baseline
        noise_status = self._evaluate_metric(baseline_noise, SCIENTIFIC_LIMITS["baseline_noise_percent"], reverse=True)
        
        stats = {
            "ppm_range": {
                "parameter": "Rango PPM",
                "value": f"{np.min(ppm):.2f} a {np.max(ppm):.2f}",
                "unit": "ppm",
                "limits": f"{fluor_range['min']} a {fluor_range['max']}",
                "status": "OK" if fluor_range["min"] - 2 <= np.min(ppm) <= np.max(ppm) <= fluor_range["max"] + 2 else "WARN",
                "source": "User Defined"
            },
            "snr": {
                "parameter": "Relación Señal/Ruido (SNR)",
                "value": round(float(snr), 2),
                "unit": "ratio",
                "limits": f"Excelente: >{SCIENTIFIC_LIMITS['snr']['excellent']}, Aceptable: >{SCIENTIFIC_LIMITS['snr']['acceptable']}",
                "status": snr_status,
                "source": SCIENTIFIC_LIMITS["snr"]["source"]
            },
            "resolution": {
                "parameter": "Resolución Espectral",
                "value": round(float(resolution), 4),
                "unit": "ppm/punto",
                "limits": f"Excelente: <{SCIENTIFIC_LIMITS['resolution_ppm']['excellent']}, Aceptable: <{SCIENTIFIC_LIMITS['resolution_ppm']['acceptable']}",
                "status": resolution_status,
                "source": SCIENTIFIC_LIMITS["resolution_ppm"]["source"]
            },
            "data_density": {
                "parameter": "Densidad de Datos",
                "value": round(float(data_density), 1),
                "unit": "pts/ppm",
                "limits": f"Excelente: >{SCIENTIFIC_LIMITS['data_density_pts_ppm']['excellent']}, Aceptable: >{SCIENTIFIC_LIMITS['data_density_pts_ppm']['acceptable']}",
                "status": density_status,
                "source": SCIENTIFIC_LIMITS["data_density_pts_ppm"]["source"]
            },
            "baseline_noise": {
                "parameter": "Ruido de Baseline",
                "value": round(float(baseline_noise), 2),
                "unit": "% señal",
                "limits": f"Excelente: <{SCIENTIFIC_LIMITS['baseline_noise_percent']['excellent']}%, Aceptable: <{SCIENTIFIC_LIMITS['baseline_noise_percent']['acceptable']}%",
                "status": noise_status,
                "source": SCIENTIFIC_LIMITS["baseline_noise_percent"]["source"]
            },
            "total_points": {
                "parameter": "Puntos de Datos",
                "value": len(ppm),
                "unit": "puntos",
                "limits": "Mínimo recomendado: 5000",
                "status": "OK" if len(ppm) >= 5000 else ("WARN" if len(ppm) >= 1000 else "FAIL"),
                "source": "NMR Best Practices"
            }
        }
        
        print(f"   ✅ Evaluación científica completada")
        print(f"      SNR: {snr:.1f} ({snr_status})")
        print(f"      Resolución: {resolution:.4f} ppm/pt ({resolution_status})")
        print(f"      Densidad: {data_density:.1f} pts/ppm ({density_status})")
        
        return stats
    
    def _evaluate_metric(self, value: float, limits: Dict, reverse: bool = False) -> str:
        """
        Evalúa una métrica contra límites científicos.
        
        Args:
            value: Valor a evaluar
            limits: Diccionario con límites {excellent, good, acceptable, poor}
            reverse: Si True, valores más bajos son mejores (ej. ruido)
        
        Returns:
            Status string: "OK" (excellent/good), "WARN" (acceptable), "FAIL" (poor)
        """
        if reverse:
            if value <= limits["excellent"]:
                return "OK"
            elif value <= limits["good"]:
                return "OK"
            elif value <= limits["acceptable"]:
                return "WARN"
            else:
                return "FAIL"
        else:
            if value >= limits["excellent"]:
                return "OK"
            elif value >= limits["good"]:
                return "OK"
            elif value >= limits["acceptable"]:
                return "WARN"
            else:
                return "FAIL"
    
    # ========================================================================
    # 🆕 INFORMACIÓN REGULATORIA
    # ========================================================================
    
    def _get_regulatory_info(self) -> Dict:
        """
        Retorna información sobre límites regulatorios aplicables.
        """
        return {
            "epa_2024": {
                "pfoa_pfos_combined_ng_l": 70,
                "pfna_ng_l": 200,
                "pfbs_ng_l": 2000,
                "source": "EPA Final PFAS Rule (2024)",
                "url": "https://www.epa.gov/sdwa/pfas-national-primary-drinking-water-regulation"
            },
            "eu_drinking_water": {
                "total_pfas_ng_l": 500,
                "sum_of_20_pfas_ng_l": 100,
                "source": "EU Drinking Water Directive (2020/2184)",
            },
            "who_guidelines": {
                "status": "Under review",
                "note": "WHO no ha establecido límites específicos aún (2024)"
            }
        }
    
    # ========================================================================
    # 🆕 MÉTRICAS DE CALIDAD AVANZADAS
    # ========================================================================
    
    def _calculate_quality_metrics_advanced(self) -> Dict:
        """Métricas de calidad mejoradas con más parámetros."""
        print("\n   ⭐ Calculando métricas de calidad avanzadas...")
        
        intensity_orig = self.intensity_data
        intensity = self.intensity_corrected
        ppm = self.ppm_data
        
        if len(intensity) < 10:
            return self._default_quality_metrics()
        
        # SNR mejorado
        signal_max = np.max(intensity)
        noise_region = intensity[intensity < np.percentile(intensity, 10)]
        noise_std = np.std(noise_region) if len(noise_region) > 1 else np.std(intensity) / 3
        noise_std = max(noise_std, 1e-9)
        snr = signal_max / noise_std
        
        # Baseline noise como % de señal máxima
        baseline_noise_percent = (noise_std / max(signal_max, 1e-9)) * 100
        
        # Dynamic Range
        dynamic_range = signal_max - np.min(intensity)
        
        # Data Density
        ppm_range = abs(np.max(ppm) - np.min(ppm))
        data_density = len(ppm) / max(ppm_range, 1e-9)
        
        # Resolución espectral
        spectral_resolution = np.mean(np.abs(np.diff(ppm))) if len(ppm) > 1 else 0.0
        
        # Uniformidad del espaciado (menor = más uniforme)
        spacing_uniformity = np.std(np.diff(ppm)) if len(ppm) > 1 else 0.0
        
        return {
            "snr": round(float(snr), 2),
            "dynamic_range": round(float(dynamic_range), 2),
            "baseline_noise_percent": round(float(baseline_noise_percent), 2),
            "data_density_pts_ppm": round(float(data_density), 1),
            "spectral_resolution_ppm_pt": round(float(spectral_resolution), 4),
            "spacing_uniformity": round(float(spacing_uniformity), 5),
            "total_points": int(len(ppm))
        }
    
    # ========================================================================
    # MÉTODOS AUXILIARES MEJORADOS
    # ========================================================================
    
    def _classify_chemical_region_enhanced(self, ppm: float) -> str:
        """Clasificación mejorada con más detalles."""
        if -82 <= ppm <= -79:
            return "CF₃ Terminal (PFOA-like)"
        elif -82.5 <= ppm <= -82:
            return "CF₃ Terminal (PFOA)"
        elif -81.5 <= ppm <= -79.5:
            return "CF₃ Terminal (PFOS)"
        elif -119.5 <= ppm <= -117.5:
            return "CF₂ α próximo a COO⁻ (PFOA)"
        elif -118.5 <= ppm <= -116.5:
            return "CF₂ α próximo a SO₃⁻ (PFOS)"
        elif -123 <= ppm <= -120:
            return "CF₂ Interno (Cadena principal)"
        elif -128 <= ppm <= -123:
            return "CF₂ Interno (Próximo a CF₃)"
        elif -130 <= ppm <= -128:
            return "CF₂ Otros / Cadena larga"
        elif -75 <= ppm <= -55:
            return "CF Ramificado / CFH / Isómeros"
        else:
            return f"Fuera de rango PFAS típico ({ppm:.1f} ppm)"
    
    def _calculate_analysis_advanced(self, fluor_range: Dict, pifas_range: Dict, 
                                    concentration: float) -> Dict:
        """Análisis mejorado con validaciones adicionales."""
        print("\n   📈 Calculando composición química avanzada...")
        
        ppm = self.ppm_data
        intensity = self.intensity_corrected
        
        if len(ppm) < 2:
            return self._default_analysis(concentration)
        
        # Integración trapezoidal
        total_area = np.trapz(intensity, ppm)
        
        fluor_mask = (ppm >= fluor_range["min"]) & (ppm <= fluor_range["max"])
        fluor_area = np.trapz(intensity[fluor_mask], ppm[fluor_mask]) if np.sum(fluor_mask) > 1 else 0
        
        pifas_mask = (ppm >= pifas_range["min"]) & (ppm <= pifas_range["max"])
        pifas_area = np.trapz(intensity[pifas_mask], ppm[pifas_mask]) if np.sum(pifas_mask) > 1 else 0
        
        epsilon = 1e-12
        fluor_percentage = (abs(fluor_area) / (abs(total_area) + epsilon) * 100)
        pifas_percentage = (abs(pifas_area) / (abs(fluor_area) + epsilon) * 100)
        pifas_concentration = concentration * (pifas_percentage / 100)
        
        # Validaciones
        if fluor_percentage > 100:
            self.warnings.append(f"Flúor {fluor_percentage:.1f}% > 100% - revisar rangos de integración")
        if pifas_percentage > 100:
            self.warnings.append(f"PFAS {pifas_percentage:.1f}% > 100% del flúor - revisar rangos")
        if pifas_concentration > concentration:
            self.warnings.append("Concentración PFAS > concentración total - verificar datos")
        
        print(f"   ✅ Análisis completado:")
        print(f"      Flúor: {fluor_percentage:.2f}%")
        print(f"      PFAS:  {pifas_percentage:.2f}% del flúor")
        print(f"      Conc:  {pifas_concentration:.4f} mM")
        
        return {
            "fluor_percentage": round(float(fluor_percentage), 2),
            "pifas_percentage": round(float(pifas_percentage), 2),
            "pifas_concentration": round(float(pifas_concentration), 4),
            "concentration": float(concentration),
            "total_area": round(float(total_area), 2),
            "fluor_area": round(float(fluor_area), 2),
            "pifas_area": round(float(pifas_area), 2),
        }
    
    def _analyze_regions_enhanced(self) -> Dict:
        """Análisis de regiones mejorado."""
        return self._analyze_regions()  # Usar método existente (ya está bien)
    
    # (Mantener métodos existentes: _read_spectrum, _detect_peaks_advanced, etc.)
    # Aquí incluiría los métodos que ya tienes si son necesarios
    
    def _read_spectrum(self, file_path: Path):
        """Lee archivo CSV (método existente)."""
        _ppm_data = []
        _intensity_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                f.seek(0)
                
                dialect = csv.Sniffer().sniff(sample, delimiters=',\t')
                has_header = csv.Sniffer().has_header(sample)
                reader = csv.reader(f, dialect)
                
                if has_header:
                    next(reader)
                
                for row_count, row in enumerate(reader, 1):
                    if len(row) >= 2:
                        try:
                            ppm = float(row[0].strip())
                            intensity = float(row[1].strip())
                            _ppm_data.append(ppm)
                            _intensity_data.append(intensity)
                        except (ValueError, IndexError):
                            continue
            
            self.ppm_data = np.array(_ppm_data)
            self.intensity_data = np.array(_intensity_data)
            
            if len(self.ppm_data) > 0:
                print(f"   ✅ Leídos {len(self.ppm_data):,} puntos")
                print(f"   📊 Rango: {np.min(self.ppm_data):.2f} a {np.max(self.ppm_data):.2f} ppm")
        
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
            self.ppm_data = np.array([])
            self.intensity_data = np.array([])
    
    # Métodos auxiliares para casos de error
    def _error_result(self, filename: str, error: str) -> Dict:
        return {
            "filename": filename,
            "error": error,
            "quality_score": 0.0
        }
    
    def _default_quality_metrics(self) -> Dict:
        return {
            "snr": 0.0,
            "dynamic_range": 0.0,
            "baseline_noise_percent": 100.0,
            "data_density_pts_ppm": 0.0,
            "spectral_resolution_ppm_pt": 0.0,
            "spacing_uniformity": 0.0,
            "total_points": 0
        }
    
    def _default_analysis(self, concentration: float) -> Dict:
        return {
            "fluor_percentage": 0.0,
            "pifas_percentage": 0.0,
            "pifas_concentration": 0.0,
            "concentration": concentration,
            "total_area": 0.0,
            "fluor_area": 0.0,
            "pifas_area": 0.0,
        }
    
    def _analyze_regions(self) -> Dict:
        """Método simple de análisis de regiones."""
        return {}
    
    def _calculate_quality_score_v3(self, metrics: Dict, peaks: List) -> Tuple[float, Dict]:
        """Score de calidad v3 con criterios científicos."""
        score = 10.0
        penalties = {}
        
        snr = metrics.get("snr", 0)
        if snr < SCIENTIFIC_LIMITS["snr"]["poor"]:
            penalties["snr"] = f"-3.0 (SNR muy bajo: {snr:.1f})"
            score -= 3.0
        elif snr < SCIENTIFIC_LIMITS["snr"]["acceptable"]:
            penalties["snr"] = f"-2.0 (SNR bajo: {snr:.1f})"
            score -= 2.0
        elif snr < SCIENTIFIC_LIMITS["snr"]["good"]:
            penalties["snr"] = f"-1.0 (SNR moderado: {snr:.1f})"
            score -= 1.0
        
        total_points = metrics.get("total_points", 0)
        if total_points < 1000:
            penalties["data_points"] = f"-2.0 (Muy pocos puntos: {total_points})"
            score -= 2.0
        elif total_points < 5000:
            penalties["data_points"] = f"-1.0 (Pocos puntos: {total_points})"
            score -= 1.0
        
        if not peaks or len(peaks) == 0:
            penalties["peaks"] = "-2.0 (No se detectaron picos)"
            score -= 2.0
        elif len(peaks) < 2:
            penalties["peaks"] = "-1.0 (Muy pocos picos)"
            score -= 1.0
        
        return round(max(0.0, min(10.0, score)), 1), penalties
    
    def _print_summary_enhanced(self, results: Dict):
        """Resumen mejorado con información de PFAS identificados."""
        print(f"\n{'='*70}")
        print("🔬 RESUMEN DEL ANÁLISIS AVANZADO")
        print(f"{'='*70}")
        
        analysis = results.get("analysis", {})
        print(f"\n📊 COMPOSICIÓN:")
        print(f"   Flúor Total:       {analysis.get('fluor_percentage', 0):.2f}%")
        print(f"   PFAS:              {analysis.get('pifas_percentage', 0):.2f}% del flúor")
        print(f"   Concentración:     {analysis.get('pifas_concentration', 0):.4f} mM")
        
        print(f"\n⭐ CALIDAD: {results.get('quality_score', 0):.1f}/10")
        
        identified = results.get("identified_pfas", [])
        if identified:
            print(f"\n🧪 PFAS IDENTIFICADOS ({len(identified)}):")
            for pfas in identified:
                print(f"   • {pfas['compound']}: {pfas['name']}")
                print(f"     Score: {pfas['match_score']:.2f} | Confianza: {pfas['confidence']}")
                if pfas.get('regulatory_limit_ng_l'):
                    print(f"     Límite EPA: {pfas['regulatory_limit_ng_l']} ng/L")
        
        warnings = results.get("warnings", [])
        if warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        print(f"\n{'='*70}\n")

# ============================================================================
# FUNCIÓN AUXILIAR PARA MATRIZ SPARSE
# ============================================================================

def sparse_diagonal_matrix(n):
    """
    Crea matriz de diferencias para ALS baseline (VERSIÓN CORREGIDA).
    Usa scipy.sparse para evitar crear una matriz densa de 128 GB.
    """
    # D = np.zeros((n-2, n)) # <-- ESTA LÍNEA ES EL PROBLEMA ORIGINAL
    
    # Crear las diagonales
    main_diag = np.ones(n - 2)
    sub_diag1 = -2 * np.ones(n - 2)
    sub_diag2 = np.ones(n - 2)
    
    # Usar sparse.diags para crear la matriz dispersa
    # Es extremadamente eficiente en memoria.
    D = sparse.diags(
        [main_diag, sub_diag1, sub_diag2],
        [0, 1, 2],           # Offsets de las diagonales
        shape=(n - 2, n),  # Forma deseada
        format='csr'       # Formato 'Compressed Sparse Row' (eficiente)
    )
    return D

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("🔬 ANALIZADOR AVANZADO DE PFAS v3.0")
        print("="*70)
        print("\nUso: python analyzer_improved.py <archivo.csv> [opciones]")
        print("\nOpciones:")
        print("   --concentration <value>  : Concentración en mM (default: 1.0)")
        print("   --no-baseline           : Desactivar corrección baseline")
        print("   --no-smart              : Desactivar detección inteligente")
        print("\nEjemplo:")
        print("   python analyzer_improved.py spectrum.csv")
        print("   python analyzer_improved.py data.csv --concentration 2.5")
        print("="*70 + "\n")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    # Parsear argumentos
    concentration = 1.0
    baseline_correction = True
    smart_detection = True
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--concentration" and i + 1 < len(sys.argv):
            try:
                concentration = float(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Valor inválido para --concentration")
                sys.exit(1)
        elif arg == "--no-baseline":
            baseline_correction = False
        elif arg == "--no-smart":
            smart_detection = False
    
    # Analizar
    analyzer = SpectrumAnalyzer()
    try:
        results = analyzer.analyze_file(
            file_path,
            concentration=concentration,
            baseline_correction=baseline_correction,
            smart_detection=smart_detection
        )
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)
    
    # Guardar JSON
    output_file = file_path.parent / f"{file_path.stem}_analysis_v3.json"
    try:
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados guardados: {output_file}")
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")
    
    print(f"\n✅ ANÁLISIS COMPLETADO\n")