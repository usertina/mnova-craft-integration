"""
Detector de PFAS Mejorado v2.0
- Base de datos expandida (30+ compuestos)
- Algoritmos de matching mejorados
- Detección de mezclas
- Sistema de scoring refinado
- Análisis de patrones espectrales avanzado
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from pfas_database import (
    PFAS_DATABASE, 
    PFAS_CATEGORIES, 
    FUNCTIONAL_GROUP_SIGNATURES,
    get_pfas_by_category,
    get_pfas_by_chain_length
)

class PFASDetectorEnhanced:
    """
    Detector de PFAS de nueva generación con capacidades avanzadas.
    """
    
    def __init__(self, confidence_threshold: float = 0.55):
        """
        Inicializa el detector mejorado.
        
        Args:
            confidence_threshold: Umbral de confianza mínimo (0-1)
        """
        self.confidence_threshold = confidence_threshold
        self.pfas_library = PFAS_DATABASE
        self.detected_compounds = []
        self.mixture_detected = False
        
        # Configuración de pesos para scoring
        self.scoring_weights = {
            "key_peaks": 0.35,      # Aumentado: más peso a picos clave
            "patterns": 0.25,       # Patrones de regiones
            "intensity_ratio": 0.20,  # Ratios de intensidad
            "chain_length": 0.10,   # Longitud de cadena
            "spectral_quality": 0.10  # Nuevo: calidad espectral
        }
        
    def detect_pfas(self, peaks: List[Dict], analysis_data: Dict = None) -> Dict:
        """
        Detecta PFAS en el espectro con algoritmos mejorados.
        
        Args:
            peaks: Lista de picos detectados
            analysis_data: Datos adicionales del análisis
        
        Returns:
            Dict con resultados completos de detección
        """
        if not peaks or len(peaks) == 0:
            return {
                "detected": False,
                "compounds": [],
                "message": "No hay picos suficientes para análisis"
            }
        
        print("\n" + "="*80)
        print("🔬 DETECTOR DE PFAS MEJORADO v2.0")
        print("="*80)
        print(f"   Base de datos: {len(self.pfas_library)} compuestos")
        print(f"   Picos analizados: {len(peaks)}")
        print(f"   Umbral de confianza: {self.confidence_threshold:.1%}")
        
        # 1. Análisis preliminar del espectro
        spectral_features = self._extract_spectral_features(peaks)
        self._print_spectral_features(spectral_features)
        
        # 2. Detección de compuestos individuales
        compound_matches = self._detect_individual_compounds(peaks, spectral_features)
        
        # 3. Análisis de mezclas
        mixture_analysis = self._analyze_mixture(peaks, compound_matches)
        
        # 4. Detección de compuestos desconocidos
        unknown_analysis = self._detect_unknown_pfas(peaks, compound_matches)
        
        # 5. Análisis avanzado de características
        advanced_analysis = self._advanced_spectral_analysis(peaks, spectral_features)
        
        # 6. Construir resultado final
        result = {
            "detected": len(compound_matches) > 0,
            "compounds": compound_matches,
            "mixture": mixture_analysis,
            "unknown_pfas": unknown_analysis,
            "spectral_features": spectral_features,
            "advanced_analysis": advanced_analysis,
            "quality_score": self._calculate_overall_quality(peaks, spectral_features)
        }
        
        self._print_detection_summary(result)
        
        return result
    
    def _extract_spectral_features(self, peaks: List[Dict]) -> Dict:
        """
        Extrae características espectrales del espectro 19F-NMR.
        """
        features = {
            "total_peaks": len(peaks),
            "ppm_range": (
                min(p.get("ppm", 0) for p in peaks),
                max(p.get("ppm", 0) for p in peaks)
            ),
            "regions": {}
        }
        
        # Definir regiones espectrales importantes
        regions = {
            "CF3_terminal": (-85, -75),
            "CF3_branch": (-78, -70),
            "CF2_ether": (-95, -82),
            "CF2_alpha_COOH": (-120, -117),
            "CF2_alpha_SO3": (-117, -113),
            "CF2_internal": (-125, -120),
            "CF2_beta": (-130, -125),
            "CF_ether": (-150, -140)
        }
        
        for region_name, (min_ppm, max_ppm) in regions.items():
            peaks_in_region = [p for p in peaks 
                             if min_ppm <= p.get("ppm", 0) <= max_ppm]
            
            if peaks_in_region:
                total_intensity = sum(p.get("intensity", p.get("height", 0)) 
                                    for p in peaks_in_region)
                total_area = sum(p.get("area", 0) for p in peaks_in_region)
                
                features["regions"][region_name] = {
                    "peak_count": len(peaks_in_region),
                    "peaks": peaks_in_region,
                    "intensity_sum": total_intensity,
                    "area_sum": total_area,
                    "avg_ppm": np.mean([p.get("ppm", 0) for p in peaks_in_region])
                }
        
        # Calcular ratios importantes
        cf3_intensity = features["regions"].get("CF3_terminal", {}).get("intensity_sum", 0)
        cf2_internal = features["regions"].get("CF2_internal", {}).get("intensity_sum", 0)
        cf2_alpha_cooh = features["regions"].get("CF2_alpha_COOH", {}).get("intensity_sum", 0)
        cf2_alpha_so3 = features["regions"].get("CF2_alpha_SO3", {}).get("intensity_sum", 0)
        
        features["intensity_ratios"] = {
            "CF3/CF2_internal": cf3_intensity / cf2_internal if cf2_internal > 0 else 0,
            "alpha_COOH/alpha_SO3": cf2_alpha_cooh / cf2_alpha_so3 if cf2_alpha_so3 > 0 else 0
        }
        
        return features
    
    def _detect_individual_compounds(self, peaks: List[Dict], 
                                    features: Dict) -> List[Dict]:
        """
        Detecta compuestos individuales con algoritmo mejorado.
        """
        print("\n" + "-"*80)
        print("📊 ANÁLISIS DE COMPUESTOS INDIVIDUALES")
        print("-"*80)
        
        matches = []
        
        for pfas_id, pfas_data in self.pfas_library.items():
            # Calcular score de match mejorado
            match_scores = self._calculate_enhanced_match_score(
                peaks, pfas_data, features
            )
            
            total_confidence = sum(
                score * self.scoring_weights.get(component, 0)
                for component, score in match_scores.items()
            )
            
            if total_confidence >= self.confidence_threshold:
                match_result = {
                    "id": pfas_id,
                    "name": pfas_data["name"],
                    "formula": pfas_data["formula"],
                    "cas": pfas_data["cas"],
                    "confidence": round(total_confidence * 100, 1),
                    "confidence_breakdown": {
                        k: round(v * 100, 1) for k, v in match_scores.items()
                    },
                    "chain_length": pfas_data["chain_length"],
                    "functional_group": pfas_data["functional_group"],
                    "category": pfas_data.get("category", "Unknown"),
                    "molecular_weight": pfas_data.get("molecular_weight", None),
                    "regulation_status": pfas_data.get("regulation_status", "Not specified")
                }
                
                matches.append(match_result)
                
                # Imprimir match si es bueno
                if total_confidence >= 0.65:
                    self._print_compound_match(match_result)
        
        # Ordenar por confianza
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches
    
    def _calculate_enhanced_match_score(self, peaks: List[Dict], 
                                       pfas_data: Dict, 
                                       features: Dict) -> Dict:
        """
        Calcula scores de match con algoritmo mejorado.
        """
        scores = {}
        
        # 1. Score de picos clave (35%)
        scores["key_peaks"] = self._match_key_peaks_enhanced(
            peaks, pfas_data.get("key_peaks", [])
        )
        
        # 2. Score de patrones de regiones (25%)
        scores["patterns"] = self._match_patterns_enhanced(
            peaks, pfas_data.get("patterns", {}), features
        )
        
        # 3. Score de ratios de intensidad (20%)
        scores["intensity_ratio"] = self._match_intensity_ratios_enhanced(
            features, pfas_data.get("intensity_ratio", {})
        )
        
        # 4. Score de longitud de cadena (10%)
        scores["chain_length"] = self._match_chain_length_enhanced(
            peaks, features, pfas_data.get("chain_length", 0)
        )
        
        # 5. Score de calidad espectral (10%)
        scores["spectral_quality"] = self._assess_spectral_quality(peaks, features)
        
        return scores
    
    def _match_key_peaks_enhanced(self, peaks: List[Dict], 
                                  key_peaks: List[float], 
                                  tolerance: float = 1.5) -> float:
        """
        Matching de picos clave con tolerancia adaptativa y ponderación.
        """
        if not key_peaks:
            return 0.5
        
        peak_positions = [p.get("ppm", 0) for p in peaks]
        weighted_matches = 0
        # Convertir key_peaks a lista de floats si son dicts
        peak_values = []
        for kp in key_peaks:
            if isinstance(kp, dict):
                peak_values.append(kp.get("ppm", 0))
            else:
                peak_values.append(float(kp))
        total_weight = 0
        
        # Ponderar picos: CF3 terminal es más importante
        for i, key_peak in enumerate(peak_values):
            # Primer pico (CF3) tiene más peso
            weight = 1.5 if i == 0 else 1.0
            total_weight += weight
            
            # Buscar match con tolerancia
            matches = [pos for pos in peak_positions 
                      if abs(pos - key_peak) <= tolerance]
            
            if matches:
                # Score basado en qué tan cerca está el mejor match
                best_match = min(matches, key=lambda x: abs(x - key_peak))
                distance = abs(best_match - key_peak)
                match_quality = 1.0 - (distance / tolerance)
                weighted_matches += match_quality * weight
        
        return weighted_matches / total_weight if total_weight > 0 else 0
    
    def _match_patterns_enhanced(self, peaks: List[Dict], 
                                patterns: Dict, 
                                features: Dict) -> float:
        """
        Matching de patrones con consideración de intensidades.
        """
        if not patterns:
            return 0.5
        
        pattern_scores = []
        
        for region_name, region_data in patterns.items():
            ppm_range = region_data["range"]
            expected_intensity = region_data.get("expected_intensity", "medium")
            
            # Buscar picos en región
            peaks_in_region = [p for p in peaks 
                             if ppm_range[0] <= p.get("ppm", 0) <= ppm_range[1]]
            
            if not peaks_in_region:
                pattern_scores.append(0.0)
                continue
            
            # Score base por presencia
            presence_score = 0.7
            
            # Bonus por intensidad correcta
            total_intensity = sum(p.get("intensity", p.get("height", 0)) 
                                for p in peaks_in_region)
            
            intensity_bonus = 0
            if expected_intensity == "very_high" and total_intensity > 1000:
                intensity_bonus = 0.3
            elif expected_intensity == "high" and total_intensity > 500:
                intensity_bonus = 0.2
            elif expected_intensity == "medium" and total_intensity > 100:
                intensity_bonus = 0.1
            
            pattern_scores.append(min(1.0, presence_score + intensity_bonus))
        
        return np.mean(pattern_scores) if pattern_scores else 0
    
    def _match_intensity_ratios_enhanced(self, features: Dict, 
                                        expected_ratios: Dict) -> float:
        """
        Matching de ratios con análisis de múltiples ratios.
        """
        if not expected_ratios:
            return 0.5
        
        observed_ratio = features["intensity_ratios"].get("CF3/CF2_internal", 0)
        expected_ratio = expected_ratios.get("CF3/CF2", 0)
        
        if expected_ratio == 0 or observed_ratio == 0:
            return 0.3
        
        # Score basado en desviación relativa
        relative_error = abs(observed_ratio - expected_ratio) / expected_ratio
        
        if relative_error < 0.2:  # < 20% error
            return 1.0
        elif relative_error < 0.4:  # 20-40% error
            return 0.8
        elif relative_error < 0.6:  # 40-60% error
            return 0.6
        else:
            return max(0.2, 1.0 - relative_error)
    
    def _match_chain_length_enhanced(self, peaks: List[Dict], 
                                    features: Dict, 
                                    expected_length: int) -> float:
        """
        Estimación mejorada de longitud de cadena.
        """
        # Método 1: Contar picos en región CF2
        cf2_peaks = features["regions"].get("CF2_internal", {}).get("peak_count", 0)
        cf2_beta_peaks = features["regions"].get("CF2_beta", {}).get("peak_count", 0)
        
        # Estimación aproximada
        estimated_length = cf2_peaks + cf2_beta_peaks + 1  # +1 por CF3
        
        # Método 2: Usar ratio CF3/CF2 como indicador
        cf3_cf2_ratio = features["intensity_ratios"].get("CF3/CF2_internal", 0)
        
        # Cadenas largas tienen ratio más bajo
        if cf3_cf2_ratio > 0:
            ratio_based_estimate = int(1 / cf3_cf2_ratio) if cf3_cf2_ratio < 1 else 5
        else:
            ratio_based_estimate = expected_length
        
        # Promediar estimaciones
        avg_estimate = (estimated_length + ratio_based_estimate) / 2
        
        # Score basado en diferencia
        diff = abs(avg_estimate - expected_length)
        
        if diff <= 1:
            return 1.0
        elif diff <= 2:
            return 0.7
        elif diff <= 3:
            return 0.5
        else:
            return max(0.2, 1.0 - (diff * 0.15))
    
    def _assess_spectral_quality(self, peaks: List[Dict], 
                                features: Dict) -> float:
        """
        Evalúa la calidad del espectro para identificación.
        """
        score = 0.5  # Base score
        
        # Bonus por número adecuado de picos
        if 5 <= features["total_peaks"] <= 20:
            score += 0.2
        elif features["total_peaks"] > 20:
            score += 0.1
        
        # Bonus por cobertura de regiones clave
        key_regions = ["CF3_terminal", "CF2_internal"]
        covered_regions = sum(1 for r in key_regions 
                            if r in features["regions"])
        score += 0.15 * (covered_regions / len(key_regions))
        
        # Bonus por presencia de CF3
        if "CF3_terminal" in features["regions"]:
            score += 0.15
        
        return min(1.0, score)
    
    def _analyze_mixture(self, peaks: List[Dict], 
                        compound_matches: List[Dict]) -> Dict:
        """
        Analiza si el espectro contiene una mezcla de PFAS.
        """
        mixture_indicators = []
        
        # Indicador 1: Múltiples compuestos con alta confianza
        high_confidence_matches = [m for m in compound_matches 
                                  if m["confidence"] >= 70]
        
        if len(high_confidence_matches) >= 2:
            mixture_indicators.append("Múltiples compuestos detectados con alta confianza")
        
        # Indicador 2: Picos en múltiples regiones α-CF2
        alpha_cooh = len([p for p in peaks 
                         if -120 <= p.get("ppm", 0) <= -117])
        alpha_so3 = len([p for p in peaks 
                        if -117 <= p.get("ppm", 0) <= -113])
        
        if alpha_cooh > 0 and alpha_so3 > 0:
            mixture_indicators.append("Presencia de grupos COOH y SO3H")
        
        # Indicador 3: Múltiples CF3 con diferentes desplazamientos
        cf3_peaks = [p for p in peaks if -85 <= p.get("ppm", 0) <= -75]
        if len(cf3_peaks) >= 3:
            mixture_indicators.append("Múltiples señales CF₃ distintas")
        
        # Indicador 4: Patrón complejo en región CF2
        cf2_peaks = [p for p in peaks if -130 <= p.get("ppm", 0) <= -115]
        if len(cf2_peaks) >= 8:
            mixture_indicators.append("Patrón CF₂ muy complejo")
        
        is_mixture = len(mixture_indicators) >= 2
        
        return {
            "is_mixture": is_mixture,
            "confidence": len(mixture_indicators) / 4.0,
            "indicators": mixture_indicators,
            "likely_components": high_confidence_matches if is_mixture else []
        }
    
    def _detect_unknown_pfas(self, peaks: List[Dict], 
                            compound_matches: List[Dict]) -> Dict:
        """
        Detecta presencia de PFAS no identificados.
        """
        # Si no hay matches buenos, podría ser un PFAS desconocido
        has_good_match = any(m["confidence"] >= 75 for m in compound_matches)
        
        # Características PFAS generales
        has_cf3 = any(-85 <= p.get("ppm", 0) <= -75 for p in peaks)
        has_cf2 = any(-130 <= p.get("ppm", 0) <= -115 for p in peaks)
        
        is_likely_pfas = has_cf3 and has_cf2
        
        if is_likely_pfas and not has_good_match:
            return {
                "detected": True,
                "confidence": 0.6,
                "reason": "Patrón PFAS general detectado sin match específico",
                "suggestions": [
                    "Puede ser un PFAS no en la base de datos",
                    "Considerar análisis por MS para identificación estructural",
                    "Verificar si es un isómero o derivado de PFAS conocidos"
                ]
            }
        
        return {
            "detected": False,
            "confidence": 0.0
        }
    
    def _advanced_spectral_analysis(self, peaks: List[Dict], 
                                   features: Dict) -> Dict:
        """
        Análisis espectral avanzado adicional.
        """
        analysis = {}
        
        # Análisis de distribución de picos
        peak_ppm = [p.get("ppm", 0) for p in peaks]
        analysis["peak_distribution"] = {
            "mean_ppm": float(np.mean(peak_ppm)),
            "std_ppm": float(np.std(peak_ppm)),
            "range_ppm": float(max(peak_ppm) - min(peak_ppm))
        }
        
        # Análisis de grupo funcional
        alpha_cooh_intensity = features["regions"].get(
            "CF2_alpha_COOH", {}
        ).get("intensity_sum", 0)
        alpha_so3_intensity = features["regions"].get(
            "CF2_alpha_SO3", {}
        ).get("intensity_sum", 0)
        
        if alpha_cooh_intensity > alpha_so3_intensity:
            likely_group = "COOH (Carboxylic acid)"
        elif alpha_so3_intensity > alpha_cooh_intensity:
            likely_group = "SO3H (Sulfonic acid)"
        else:
            likely_group = "Ambiguous or mixed"
        
        analysis["functional_group_prediction"] = {
            "likely_group": likely_group,
            "cooh_evidence": alpha_cooh_intensity,
            "so3h_evidence": alpha_so3_intensity
        }
        
        # Detección de características especiales
        analysis["special_features"] = []
        
        # Éteres
        if "CF2_ether" in features["regions"]:
            analysis["special_features"].append("Ether groups present (new-gen PFAS?)")
        
        # Ramificaciones
        if "CF3_branch" in features["regions"]:
            analysis["special_features"].append("Branched structure indicated")
        
        return analysis
    
    def _calculate_overall_quality(self, peaks: List[Dict], 
                                   features: Dict) -> float:
        """
        Calcula score de calidad general del análisis.
        """
        quality_factors = []
        
        # Factor 1: Número de picos
        if 5 <= features["total_peaks"] <= 25:
            quality_factors.append(1.0)
        elif features["total_peaks"] < 5:
            quality_factors.append(0.4)
        else:
            quality_factors.append(0.7)
        
        # Factor 2: Cobertura de regiones
        total_regions = 6  # Regiones clave definidas
        covered = len(features["regions"])
        quality_factors.append(min(1.0, covered / total_regions))
        
        # Factor 3: Presencia de CF3
        has_cf3 = "CF3_terminal" in features["regions"]
        quality_factors.append(1.0 if has_cf3 else 0.3)
        
        # Factor 4: Intensidades razonables
        all_intensities = [p.get("intensity", p.get("height", 0)) for p in peaks]
        if all_intensities:
            max_int = max(all_intensities)
            has_good_dynamic_range = max_int > 100
            quality_factors.append(1.0 if has_good_dynamic_range else 0.6)
        
        return float(np.mean(quality_factors))
    
    # ========== FUNCIONES DE IMPRESIÓN ==========
    
    def _print_spectral_features(self, features: Dict):
        """Imprime características espectrales extraídas."""
        print(f"\n{'='*80}")
        print("📈 CARACTERÍSTICAS ESPECTRALES")
        print(f"{'='*80}")
        print(f"   Picos totales: {features['total_peaks']}")
        print(f"   Rango PPM: {features['ppm_range'][0]:.1f} a {features['ppm_range'][1]:.1f}")
        
        print(f"\n   Regiones detectadas:")
        for region_name, region_data in features["regions"].items():
            print(f"      • {region_name}: {region_data['peak_count']} picos "
                  f"(Σ intensidad: {region_data['intensity_sum']:.0f})")
        
        print(f"\n   Ratios de intensidad:")
        for ratio_name, ratio_value in features["intensity_ratios"].items():
            print(f"      • {ratio_name}: {ratio_value:.3f}")
    
    def _print_compound_match(self, match: Dict):
        """Imprime detalles de un compuesto detectado."""
        print(f"\n   ✅ MATCH: {match['name']}")
        print(f"      Confianza: {match['confidence']:.1f}%")
        print(f"      Fórmula: {match['formula']}")
        print(f"      Categoría: {match['category']}")
        if match.get("regulation_status"):
            print(f"      Estado regulatorio: {match['regulation_status']}")
        print(f"      Breakdown:")
        for component, score in match['confidence_breakdown'].items():
            print(f"         - {component}: {score:.1f}%")
    
    def _print_detection_summary(self, result: Dict):
        """Imprime resumen completo de detección."""
        print(f"\n{'='*80}")
        print("📋 RESUMEN DE DETECCIÓN")
        print(f"{'='*80}")
        
        if result["detected"]:
            print(f"   ✅ PFAS DETECTADOS: {len(result['compounds'])}\n")
            
            for i, compound in enumerate(result["compounds"], 1):
                print(f"   {i}. {compound['name']}")
                print(f"      - Confianza: {compound['confidence']:.1f}%")
                print(f"      - CAS: {compound['cas']}")
                print(f"      - Cadena: C{compound['chain_length']}")
                print(f"      - Grupo funcional: {compound['functional_group']}")
                if compound.get("molecular_weight"):
                    print(f"      - Peso molecular: {compound['molecular_weight']:.2f}")
                if compound.get("regulation_status"):
                    print(f"      - Regulación: {compound['regulation_status']}")
                print()
        else:
            print("   ℹ️  No se detectaron PFAS conocidos")
        
        # Información de mezcla
        if result["mixture"]["is_mixture"]:
            print(f"   ⚠️  MEZCLA DETECTADA (confianza: {result['mixture']['confidence']:.0%})")
            print(f"      Indicadores:")
            for indicator in result["mixture"]["indicators"]:
                print(f"         • {indicator}")
            print()
        
        # PFAS desconocidos
        if result["unknown_pfas"]["detected"]:
            print(f"   ⚠️  POSIBLE PFAS DESCONOCIDO")
            print(f"      {result['unknown_pfas']['reason']}")
            print(f"      Sugerencias:")
            for suggestion in result['unknown_pfas']['suggestions']:
                print(f"         • {suggestion}")
            print()
        
        # Calidad del análisis
        quality = result["quality_score"]
        quality_label = "Excelente" if quality >= 0.8 else \
                       "Buena" if quality >= 0.6 else \
                       "Regular" if quality >= 0.4 else "Pobre"
        
        print(f"   Calidad del análisis: {quality_label} ({quality:.0%})")
        print(f"{'='*80}\n")


# Función auxiliar para facilitar uso
def detect_pfas_enhanced(peaks: List[Dict], 
                        confidence_threshold: float = 0.55) -> Dict:
    """
    Función helper para detección rápida de PFAS.
    
    Args:
        peaks: Lista de picos del espectro
        confidence_threshold: Umbral de confianza (0-1)
    
    Returns:
        Dict con resultados de detección
    """
    detector = PFASDetectorEnhanced(confidence_threshold=confidence_threshold)
    return detector.detect_pfas(peaks)