"""
Detector de PFAS basado en análisis de espectros 19F-NMR
Identifica tipo, longitud de cadena y grupo funcional
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

class PFASDetector:
    """
    Identifica compuestos PFAS analizando patrones de 19F-NMR.
    
    Basado en:
    - Desplazamientos químicos característicos
    - Ratios de intensidad entre regiones
    - Patrones de picos múltiples
    """
    
    # Biblioteca de PFAS conocidos con sus patrones característicos
    PFAS_LIBRARY = {
        "PFOA": {
            "name": "Ácido Perfluorooctanoico",
            "formula": "C8HF15O2",
            "cas": "335-67-1",
            "chain_length": 8,
            "functional_group": "COOH",
            "patterns": {
                "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
                "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
                "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
                "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
            },
            "key_peaks": [-80.7, -118.0, -121.9, -126.1],
            "intensity_ratio": {"CF3/CF2": 0.3}  # Aproximado
        },
        "PFOS": {
            "name": "Sulfonato de Perfluorooctano",
            "formula": "C8HF17O3S",
            "cas": "1763-23-1",
            "chain_length": 8,
            "functional_group": "SO3H",
            "patterns": {
                "CF3_terminal": {"range": (-82, -79), "expected_intensity": "high"},
                "CF2_alpha": {"range": (-115, -113), "expected_intensity": "medium"},
                "CF2_internal": {"range": (-122, -120), "expected_intensity": "very_high"},
                "CF2_near_SO3": {"range": (-117, -115), "expected_intensity": "medium"}
            },
            "key_peaks": [-80.9, -114.3, -120.8, -116.2],
            "intensity_ratio": {"CF3/CF2": 0.3}
        },
        "PFNA": {
            "name": "Ácido Perfluorononanoico",
            "formula": "C9HF17O2",
            "cas": "375-95-1",
            "chain_length": 9,
            "functional_group": "COOH",
            "patterns": {
                "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
                "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
                "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
                "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
            },
            "key_peaks": [-80.7, -118.1, -122.0, -126.2],
            "intensity_ratio": {"CF3/CF2": 0.27}  # Menor que PFOA por cadena más larga
        },
        "PFDA": {
            "name": "Ácido Perfluorodecanoico",
            "formula": "C10HF19O2",
            "cas": "335-76-2",
            "chain_length": 10,
            "functional_group": "COOH",
            "patterns": {
                "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
                "CF2_alpha": {"range": (-119, -117), "expected_intensity": "medium"},
                "CF2_internal": {"range": (-123, -121), "expected_intensity": "very_high"},
                "CF2_beta": {"range": (-127, -125), "expected_intensity": "high"}
            },
            "key_peaks": [-80.7, -118.2, -122.1, -126.3],
            "intensity_ratio": {"CF3/CF2": 0.25}
        },
        "GenX": {
            "name": "HFPO-DA (GenX)",
            "formula": "C6HF11O3",
            "cas": "13252-13-6",
            "chain_length": 6,
            "functional_group": "COOH",
            "patterns": {
                "CF3_terminal": {"range": (-83, -78), "expected_intensity": "high"},
                "CF3_branch": {"range": (-75, -72), "expected_intensity": "medium"},
                "CF2_ether": {"range": (-88, -84), "expected_intensity": "medium"},
                "CF2_alpha": {"range": (-119, -115), "expected_intensity": "medium"}
            },
            "key_peaks": [-80.2, -73.5, -85.6, -117.3],
            "intensity_ratio": {"CF3/CF2": 0.6},  # Más alto por ramificación
            "notes": "Estructura ramificada con éter"
        },
        "PFHxS": {
            "name": "Sulfonato de Perfluorohexano",
            "formula": "C6HF13O3S",
            "cas": "355-46-4",
            "chain_length": 6,
            "functional_group": "SO3H",
            "patterns": {
                "CF3_terminal": {"range": (-82, -80), "expected_intensity": "high"},
                "CF2_internal": {"range": (-122, -119), "expected_intensity": "high"},
                "CF2_near_SO3": {"range": (-116, -114), "expected_intensity": "medium"}
            },
            "key_peaks": [-81.0, -120.5, -115.1],
            "intensity_ratio": {"CF3/CF2": 0.4}  # Cadena corta
        }
    }
    
    def __init__(self):
        """Inicializa el detector."""
        self.detected_compounds = []
        self.confidence_threshold = 0.6  # 60% de confianza mínima
    
    def detect_pfas(self, peaks: List[Dict], analysis_data: Dict) -> Dict:
        """
        Detecta PFAS en el espectro analizado.
        
        Args:
            peaks: Lista de picos detectados con ppm, intensity, area
            analysis_data: Datos del análisis completo
        
        Returns:
            Dict con compuestos detectados y confianza
        """
        if not peaks or len(peaks) == 0:
            return {
                "detected": False,
                "compounds": [],
                "message": "No hay picos suficientes para identificar"
            }
        
        print("\n" + "="*70)
        print("🔬 DETECTOR DE PFAS - Análisis de Compuestos")
        print("="*70)
        
        # Analizar cada compuesto de la biblioteca
        results = []
        for pfas_id, pfas_data in self.PFAS_LIBRARY.items():
            confidence = self._match_compound(peaks, pfas_data, pfas_id)
            if confidence >= self.confidence_threshold:
                results.append({
                    "id": pfas_id,
                    "name": pfas_data["name"],
                    "formula": pfas_data["formula"],
                    "cas": pfas_data["cas"],
                    "confidence": round(confidence * 100, 1),
                    "chain_length": pfas_data["chain_length"],
                    "functional_group": pfas_data["functional_group"]
                })
        
        # Ordenar por confianza
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Análisis adicional
        chain_estimate = self._estimate_chain_length(peaks)
        functional_group = self._detect_functional_group(peaks)
        
        # Resultado final
        detection_result = {
            "detected": len(results) > 0,
            "compounds": results,
            "chain_length_estimate": chain_estimate,
            "functional_group_detected": functional_group,
            "analysis": {
                "total_peaks": len(peaks),
                "cf3_detected": self._has_cf3_peak(peaks),
                "cf2_detected": self._has_cf2_region(peaks),
                "pattern_quality": self._assess_pattern_quality(peaks)
            }
        }
        
        self._print_detection_summary(detection_result)
        
        return detection_result
    
    def _match_compound(self, peaks: List[Dict], pfas_data: Dict, pfas_id: str) -> float:
        """
        Calcula confianza de match con un compuesto específico.
        
        Returns:
            float: Confianza entre 0 y 1
        """
        scores = []
        
        # 1. Verificar presencia de picos clave (40% del score)
        key_peaks_score = self._match_key_peaks(peaks, pfas_data["key_peaks"])
        scores.append(("key_peaks", key_peaks_score, 0.4))
        
        # 2. Verificar patrones de regiones (30% del score)
        pattern_score = self._match_patterns(peaks, pfas_data["patterns"])
        scores.append(("patterns", pattern_score, 0.3))
        
        # 3. Verificar ratio de intensidades (20% del score)
        ratio_score = self._match_intensity_ratio(peaks, pfas_data["intensity_ratio"])
        scores.append(("ratio", ratio_score, 0.2))
        
        # 4. Verificar longitud de cadena (10% del score)
        chain_score = self._match_chain_length(peaks, pfas_data["chain_length"])
        scores.append(("chain", chain_score, 0.1))
        
        # Calcular score ponderado
        total_score = sum(score * weight for name, score, weight in scores)
        
        if total_score >= 0.5:  # Solo mostrar matches razonables
            print(f"\n   📊 Match con {pfas_id} ({pfas_data['name']}):")
            for name, score, weight in scores:
                print(f"      - {name}: {score:.2f} (peso: {weight:.0%})")
            print(f"      ➤ Confianza total: {total_score:.2%}")
        
        return total_score
    
    def _match_key_peaks(self, peaks: List[Dict], key_peaks: List[float], tolerance: float = 2.0) -> float:
        """Verifica cuántos picos clave están presentes."""
        if not key_peaks:
            return 0.5  # Neutral si no hay picos de referencia
        
        peak_positions = [p.get("ppm", p.get("position", 0)) for p in peaks]
        matches = 0
        
        for key_peak in key_peaks:
            # Buscar pico cercano dentro de la tolerancia
            if any(abs(pos - key_peak) <= tolerance for pos in peak_positions):
                matches += 1
        
        return matches / len(key_peaks)
    
    def _match_patterns(self, peaks: List[Dict], patterns: Dict) -> float:
        """Verifica presencia de patrones en regiones específicas."""
        if not patterns:
            return 0.5
        
        pattern_matches = 0
        for region_name, region_data in patterns.items():
            ppm_range = region_data["range"]
            # Buscar picos en este rango
            peaks_in_region = [p for p in peaks 
                             if ppm_range[0] <= p.get("ppm", p.get("position", 0)) <= ppm_range[1]]
            
            if len(peaks_in_region) > 0:
                pattern_matches += 1
        
        return pattern_matches / len(patterns) if patterns else 0
    
    def _match_intensity_ratio(self, peaks: List[Dict], expected_ratios: Dict) -> float:
        """Compara ratios de intensidad observados vs esperados."""
        if not expected_ratios or "CF3/CF2" not in expected_ratios:
            return 0.5
        
        # Separar picos por región
        cf3_peaks = [p for p in peaks if -85 <= p.get("ppm", 0) <= -75]
        cf2_peaks = [p for p in peaks if -130 <= p.get("ppm", 0) <= -115]
        
        if not cf3_peaks or not cf2_peaks:
            return 0.3
        
        # Calcular intensidad total de cada región
        cf3_intensity = sum(p.get("intensity", p.get("height", 0)) for p in cf3_peaks)
        cf2_intensity = sum(p.get("intensity", p.get("height", 0)) for p in cf2_peaks)
        
        if cf2_intensity == 0:
            return 0.3
        
        observed_ratio = cf3_intensity / cf2_intensity
        expected_ratio = expected_ratios["CF3/CF2"]
        
        # Score basado en qué tan cerca está el ratio
        ratio_diff = abs(observed_ratio - expected_ratio) / expected_ratio
        score = max(0, 1 - ratio_diff)  # 0 si diff > 100%, 1 si diff = 0
        
        return score
    
    def _match_chain_length(self, peaks: List[Dict], expected_length: int) -> float:
        """Estima si la longitud de cadena coincide."""
        estimated_length = self._estimate_chain_length(peaks)
        
        if estimated_length is None:
            return 0.5
        
        # Score basado en diferencia de longitud
        diff = abs(estimated_length - expected_length)
        if diff == 0:
            return 1.0
        elif diff <= 1:
            return 0.8
        elif diff <= 2:
            return 0.6
        else:
            return 0.3
    
    def _estimate_chain_length(self, peaks: List[Dict]) -> Optional[int]:
        """
        Estima longitud de cadena basado en número de señales CF2.
        
        Aproximación: número de picos en región CF2 + 1 (CF3)
        """
        cf2_peaks = [p for p in peaks if -130 <= p.get("ppm", 0) <= -115]
        cf3_peaks = [p for p in peaks if -85 <= p.get("ppm", 0) <= -75]
        
        if not cf3_peaks:
            return None
        
        # Estimación burda: CF2 internos + 1 (CF3)
        # En realidad los CF2 pueden solaparse en un solo pico ancho
        return len(cf2_peaks) + 1
    
    def _detect_functional_group(self, peaks: List[Dict]) -> str:
        """Detecta tipo de grupo funcional basado en desplazamiento α-CF2."""
        alpha_cf2_peaks = [p for p in peaks if -120 <= p.get("ppm", 0) <= -113]
        
        if not alpha_cf2_peaks:
            return "Unknown"
        
        # Buscar el más desplazado (más cercano a 0)
        most_shifted = max(alpha_cf2_peaks, key=lambda p: p.get("ppm", -999))
        ppm_val = most_shifted.get("ppm", 0)
        
        if -120 <= ppm_val <= -117:
            return "COOH (Ácido carboxílico)"
        elif -117 <= ppm_val <= -113:
            return "SO3H (Ácido sulfónico)"
        else:
            return "Other"
    
    def _has_cf3_peak(self, peaks: List[Dict]) -> bool:
        """Verifica presencia de CF3 terminal."""
        return any(-85 <= p.get("ppm", 0) <= -75 for p in peaks)
    
    def _has_cf2_region(self, peaks: List[Dict]) -> bool:
        """Verifica presencia de región CF2."""
        return any(-130 <= p.get("ppm", 0) <= -115 for p in peaks)
    
    def _assess_pattern_quality(self, peaks: List[Dict]) -> str:
        """Evalúa calidad del patrón para identificación."""
        if len(peaks) < 3:
            return "Poor"
        elif len(peaks) < 10:
            return "Fair"
        elif len(peaks) < 15:
            return "Good"
        else:
            return "Excellent"
    
    def _print_detection_summary(self, result: Dict):
        """Imprime resumen de detección."""
        print(f"\n{'='*70}")
        print("📋 RESUMEN DE DETECCIÓN")
        print(f"{'='*70}")
        
        if result["detected"]:
            print(f"   ✅ PFAS DETECTADOS: {len(result['compounds'])}")
            for i, compound in enumerate(result["compounds"], 1):
                print(f"\n   {i}. {compound['name']}")
                print(f"      - Fórmula: {compound['formula']}")
                print(f"      - CAS: {compound['cas']}")
                print(f"      - Confianza: {compound['confidence']:.1f}%")
                print(f"      - Cadena: C{compound['chain_length']}")
                print(f"      - Grupo funcional: {compound['functional_group']}")
        else:
            print("   ℹ️  No se detectaron PFAS conocidos con suficiente confianza")
            print(f"   ℹ️  Esto puede deberse a:")
            print(f"      - PFAS no está en la biblioteca")
            print(f"      - Mezcla de múltiples PFAS")
            print(f"      - Calidad del espectro insuficiente")
        
        print(f"\n   Análisis general:")
        analysis = result["analysis"]
        print(f"      - Picos totales: {analysis['total_peaks']}")
        print(f"      - CF₃ detectado: {'Sí' if analysis['cf3_detected'] else 'No'}")
        print(f"      - CF₂ detectado: {'Sí' if analysis['cf2_detected'] else 'No'}")
        print(f"      - Calidad patrón: {analysis['pattern_quality']}")
        
        if result["chain_length_estimate"]:
            print(f"      - Longitud cadena estimada: C{result['chain_length_estimate']}")
        if result["functional_group_detected"] != "Unknown":
            print(f"      - Grupo funcional: {result['functional_group_detected']}")
        
        print(f"{'='*70}\n")