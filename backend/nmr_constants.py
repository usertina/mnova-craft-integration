"""
Constantes físicas para RMN según Levitt "Spin Dynamics"
CraftRMN Pro v2.3 - Correcciones según fundamentos de NMR

Valores de referencia:
- Levitt "Spin Dynamics", Tabla 2.1 (Gyromagnetic ratios)
- Levitt, Apéndice A (Constantes físicas)
- Literatura 19F-NMR de PFAS
"""

import numpy as np
from typing import Dict, Tuple

# ============================================================================
# CONSTANTES GIROMAGNÉTICAS (MHz/T)
# Levitt, Tabla 2.1
# ============================================================================

GYROMAGNETIC_RATIOS = {
    '1H':  42.577,   # Hidrógeno (protón)
    '2H':   6.536,   # Deuterio
    '13C': 10.708,   # Carbono-13
    '15N': -4.316,   # Nitrógeno-15 (negativo!)
    '19F': 40.077,   # Flúor-19 ← IMPORTANTE
    '31P': 17.235,   # Fósforo-31
}

# Relaciones frecuencia respecto a 1H
# Ξ = ν_X / ν_1H (Levitt, Ec. 2.17)
FREQUENCY_RATIOS = {
    '1H':  1.0000,
    '2H':  0.1535,
    '13C': 0.2515,
    '15N': 0.1013,
    '19F': 0.9412,  # ← CRÍTICO: 19F es 94.12% de 1H
    '31P': 0.4048,
}

# ============================================================================
# FUNCIONES DE CONVERSIÓN (Levitt Capítulo 2)
# ============================================================================

def calculate_nucleus_frequency(h1_frequency_mhz: float, nucleus: str) -> float:
    """
    Calcula la frecuencia de Larmor para un núcleo dado.
    
    Basado en Levitt Ec. 2.15: ω_0 = -γB_0
    Donde γ es el ratio giromagnético y B_0 el campo magnético
    
    Args:
        h1_frequency_mhz: Frecuencia del espectrómetro para 1H (ej: 500 MHz)
        nucleus: Símbolo del núcleo ('1H', '19F', etc.)
    
    Returns:
        Frecuencia en MHz
        
    Ejemplo:
        >>> calculate_nucleus_frequency(500, '19F')
        470.6  # MHz
        
    Raises:
        ValueError: Si el núcleo no está en la tabla
    """
    if nucleus not in FREQUENCY_RATIOS:
        available = ', '.join(FREQUENCY_RATIOS.keys())
        raise ValueError(
            f"Núcleo '{nucleus}' no soportado.\n"
            f"Disponibles: {available}"
        )
    
    return h1_frequency_mhz * FREQUENCY_RATIOS[nucleus]


def ppm_to_hz(delta_ppm: float, nucleus_frequency_mhz: float) -> float:
    """
    Convierte desplazamiento químico (ppm) a frecuencia (Hz).
    
    Levitt Ec. 2.15: Δν(Hz) = δ(ppm) × ν_0(MHz)
    
    La frecuencia absoluta depende del campo magnético.
    ppm es una medida relativa independiente del campo.
    
    Args:
        delta_ppm: Desplazamiento químico en ppm
        nucleus_frequency_mhz: Frecuencia de Larmor del núcleo en MHz
    
    Returns:
        Frecuencia en Hz
        
    Ejemplo:
        >>> ppm_to_hz(1.0, 470.6)  # 1 ppm en 19F a 470 MHz
        470.6  # Hz
        
        >>> ppm_to_hz(0.04, 470.6)  # Tolerancia típica
        18.8  # Hz
    """
    return abs(delta_ppm * nucleus_frequency_mhz)


def hz_to_ppm(frequency_hz: float, nucleus_frequency_mhz: float) -> float:
    """
    Convierte frecuencia (Hz) a desplazamiento químico (ppm).
    
    Inversa de Levitt Ec. 2.15: δ(ppm) = Δν(Hz) / ν_0(MHz)
    
    Args:
        frequency_hz: Frecuencia en Hz
        nucleus_frequency_mhz: Frecuencia de Larmor del núcleo en MHz
    
    Returns:
        Desplazamiento químico en ppm
        
    Ejemplo:
        >>> hz_to_ppm(470.6, 470.6)
        1.0  # ppm
        
        >>> hz_to_ppm(10, 470.6)  # FWHM típico
        0.021  # ppm
    """
    return abs(frequency_hz / nucleus_frequency_mhz)


def calculate_linewidth_tolerance(linewidth_hz: float, 
                                  nucleus_frequency_mhz: float,
                                  n_fwhm: float = 2.0) -> float:
    """
    Calcula tolerancia apropiada para matching de picos.
    
    Según Levitt Cap. 12.3: El ancho de línea FWHM está relacionado con T2*
    FWHM = 1/(π·T2*)
    
    Para matching de picos, la tolerancia debe ser proporcional al FWHM.
    Regla práctica: 2×FWHM cubre ~95% del área del pico (distribución Lorentziana)
    
    Args:
        linewidth_hz: Ancho de línea a media altura (FWHM) en Hz
        nucleus_frequency_mhz: Frecuencia del núcleo en MHz
        n_fwhm: Múltiplo de FWHM (default: 2.0 para 95% de área)
    
    Returns:
        Tolerancia en ppm
        
    Ejemplo:
        >>> # 19F con FWHM = 10 Hz en espectrómetro 500 MHz
        >>> f19_freq = calculate_nucleus_frequency(500, '19F')
        >>> calculate_linewidth_tolerance(10, f19_freq, 2.0)
        0.0425  # ppm
        
        >>> # Comparación con valor anterior (1.5 ppm)
        >>> 1.5 / 0.0425
        35.3  # ¡35 veces más preciso!
    
    Notes:
        - Para 19F, FWHM típico: 5-20 Hz (depende del shimming)
        - Tolerancia resultante: 0.02-0.09 ppm
        - Tolerancia antigua (1.5 ppm) equivalía a FWHM de 350 Hz (absurdo)
    """
    linewidth_ppm = hz_to_ppm(linewidth_hz, nucleus_frequency_mhz)
    return n_fwhm * linewidth_ppm


# ============================================================================
# CONFIGURACIÓN POR DEFECTO PARA 19F-NMR
# ============================================================================

class F19Config:
    """
    Configuración por defecto para 19F-NMR en análisis de PFAS.
    
    Basado en:
    - Levitt "Spin Dynamics" (fundamentos)
    - Literatura de 19F-NMR de PFAS
    - Experiencia práctica con espectrómetros modernos
    """
    
    # ========== ESPECTRÓMETRO ==========
    # Ajustar según tu equipo (400, 500, 600 MHz son comunes)
    SPECTROMETER_H1_FREQ = 500.0  # MHz (para 1H)
    
    # Frecuencia calculada para 19F (automático)
    NUCLEUS_FREQ = calculate_nucleus_frequency(SPECTROMETER_H1_FREQ, '19F')  # 470.6 MHz
    
    # ========== ANCHOS DE LÍNEA TÍPICOS (Hz) ==========
    # Dependen de: homogeneidad del campo, T2*, shimming
    LINEWIDTH_MIN = 5.0       # Hz (shimming excelente, T2* largo)
    LINEWIDTH_TYPICAL = 10.0  # Hz (condiciones normales)
    LINEWIDTH_MAX = 20.0      # Hz (shimming pobre o T2* corto)
    
    # ========== TOLERANCIAS CALCULADAS (ppm) ==========
    # Basadas en 2×FWHM (95% del área del pico)
    TOLERANCE_TIGHT = calculate_linewidth_tolerance(
        LINEWIDTH_MIN, NUCLEUS_FREQ, 2.0
    )  # ~0.021 ppm
    
    TOLERANCE_NORMAL = calculate_linewidth_tolerance(
        LINEWIDTH_TYPICAL, NUCLEUS_FREQ, 2.0
    )  # ~0.043 ppm
    
    TOLERANCE_RELAXED = calculate_linewidth_tolerance(
        LINEWIDTH_MAX, NUCLEUS_FREQ, 2.0
    )  # ~0.085 ppm
    
    # ========== REGIONES ESPECTRALES PFAS (ppm) ==========
    # Basado en literatura de PFAS
    PFAS_REGION = (-150, -50)      # Rango completo de PFAS
    CF3_REGION = (-85, -75)        # CF3 terminal
    CF2_INTERNAL_REGION = (-125, -120)  # CF2 internos
    CF2_ALPHA_COOH = (-120, -117)  # CF2-α a COOH (PFCAs)
    CF2_ALPHA_SO3 = (-117, -113)   # CF2-α a SO3 (PFSAs)
    CF2_BETA_REGION = (-130, -125) # CF2-β
    CF_ETHER_REGION = (-150, -140) # CF en enlaces éter (GenX, etc.)
    
    # ========== ACOPLAMIENTO J TÍPICO 19F-19F (Hz) ==========
    # Levitt Capítulo 10: J depende del número de enlaces
    J_FF_2BOND = (40, 80)    # 2JFF: F-C-F (geminal)
    J_FF_3BOND = (0, 20)     # 3JFF: F-C-C-F (vicinal, más común en PFAS)
    J_FF_4BOND = (0, 5)      # 4JFF: F-C-C-C-F (long-range)
    
    # ========== TIEMPOS DE RELAJACIÓN TÍPICOS ==========
    # Para validación de condiciones cuantitativas (Levitt Cap. 12)
    T1_MIN = 0.5   # segundos (PFAS de cadena corta)
    T1_TYPICAL = 1.0  # segundos
    T1_MAX = 2.0   # segundos (PFAS de cadena larga)
    
    # Delay mínimo recomendado: 5×T1
    RECOMMENDED_DELAY = 5.0 * T1_MAX  # 10 segundos
    
    # ========== SNR MÍNIMOS RECOMENDADOS ==========
    # Levitt Cap. 16: SNR necesario según aplicación
    SNR_MIN_DETECTION = 3.0      # Límite de detección
    SNR_MIN_QUANTIFICATION = 10.0  # Análisis cuantitativo confiable
    SNR_EXCELLENT = 50.0         # Calidad excelente


# ============================================================================
# FUNCIONES HELPER PARA ANÁLISIS
# ============================================================================

def get_optimal_tolerance(estimated_linewidth_hz: float = 10.0,
                         spectrometer_h1_freq: float = 500.0) -> Dict[str, float]:
    """
    Calcula tolerancias óptimas para diferentes niveles de stringencia.
    
    Args:
        estimated_linewidth_hz: FWHM estimado en Hz
        spectrometer_h1_freq: Frecuencia del espectrómetro (1H) en MHz
    
    Returns:
        Dict con tolerancias en ppm y Hz
    
    Ejemplo:
        >>> tol = get_optimal_tolerance(10.0, 500.0)
        >>> print(f"Normal: {tol['normal_ppm']:.4f} ppm")
        Normal: 0.0425 ppm
    """
    f19_freq = calculate_nucleus_frequency(spectrometer_h1_freq, '19F')
    
    return {
        'tight_ppm': calculate_linewidth_tolerance(estimated_linewidth_hz, f19_freq, 1.5),
        'tight_hz': estimated_linewidth_hz * 1.5,
        'normal_ppm': calculate_linewidth_tolerance(estimated_linewidth_hz, f19_freq, 2.0),
        'normal_hz': estimated_linewidth_hz * 2.0,
        'relaxed_ppm': calculate_linewidth_tolerance(estimated_linewidth_hz, f19_freq, 3.0),
        'relaxed_hz': estimated_linewidth_hz * 3.0,
        'f19_frequency': f19_freq
    }


def estimate_multiplet_width(j_coupling_hz: float,
                            n_couplings: int = 1) -> float:
    """
    Estima el ancho de un multiplete por acoplamiento J.
    
    Levitt Cap. 10: Un núcleo con n acoplamientos equivalentes
    produce un multiplete de (n+1) líneas espaciadas por J.
    
    Ancho total ≈ n × J
    
    Args:
        j_coupling_hz: Constante de acoplamiento en Hz
        n_couplings: Número de acoplamientos equivalentes
    
    Returns:
        Ancho del multiplete en Hz
    
    Ejemplo:
        >>> # CF3 acoplado a 1 CF2 (J=10Hz)
        >>> estimate_multiplet_width(10, 1)
        10.0  # Hz (triplete: 3 líneas espaciadas 10 Hz)
        
        >>> # CF2 acoplado a 2 CF2 (J=12Hz cada uno)
        >>> estimate_multiplet_width(12, 2)
        24.0  # Hz (quintuplete si son equivalentes)
    """
    return n_couplings * j_coupling_hz


def validate_quantitative_conditions(relaxation_delay_s: float,
                                    estimated_t1_s: float = 1.0) -> Tuple[bool, list]:
    """
    Valida si las condiciones de adquisición permiten análisis cuantitativo.
    
    Levitt Cap. 12.4: Para integrales cuantitativas, se requiere:
    - Delay entre pulsos ≥ 5×T1 (recuperación completa de magnetización)
    - Pulso de 90° (flip angle correcto)
    - No saturación
    
    Args:
        relaxation_delay_s: Delay (D1) entre pulsos en segundos
        estimated_t1_s: T1 estimado del núcleo en segundos
    
    Returns:
        Tuple (es_valido, lista_de_warnings)
    
    Ejemplo:
        >>> valid, warnings = validate_quantitative_conditions(1.0, 1.0)
        >>> if not valid:
        ...     for w in warnings:
        ...         print(w)
        ⚠️ Delay (1.0s) < 5×T1 (5.0s)
           Magnetización recuperada: ~63%
           Error en integrales: ~37%
    """
    warnings = []
    is_valid = True
    
    recommended_delay = 5 * estimated_t1_s
    
    if relaxation_delay_s < recommended_delay:
        is_valid = False
        
        # Calcular recuperación de magnetización: 1 - exp(-D1/T1)
        recovery = 1 - np.exp(-relaxation_delay_s / estimated_t1_s)
        error = (1 - recovery) * 100
        
        warnings.append(
            f"⚠️ Delay ({relaxation_delay_s:.1f}s) < 5×T1 ({recommended_delay:.1f}s)\n"
            f"   Magnetización recuperada: ~{recovery*100:.0f}%\n"
            f"   Error en integrales: ~{error:.0f}%\n"
            f"   Recomendación: Usar D1 ≥ {recommended_delay:.1f}s"
        )
    
    return is_valid, warnings


# ============================================================================
# TESTING Y EJEMPLOS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("🧲 CONSTANTES RMN - MÓDULO DE TEST")
    print("="*70)
    
    # Test 1: Cálculo de frecuencias
    print("\n1️⃣ FRECUENCIAS PARA ESPECTRÓMETRO 500 MHz (1H):")
    print("-" * 70)
    for nucleus in ['1H', '13C', '19F', '31P']:
        freq = calculate_nucleus_frequency(500, nucleus)
        ratio = FREQUENCY_RATIOS[nucleus]
        print(f"   {nucleus:4s}: {freq:7.2f} MHz  (ratio: {ratio:.4f})")
    
    # Test 2: Conversiones ppm ↔ Hz para 19F
    print("\n2️⃣ CONVERSIONES PARA 19F A 470.6 MHz:")
    print("-" * 70)
    test_values = [0.01, 0.04, 0.1, 1.0, 1.5]
    for ppm_val in test_values:
        hz_val = ppm_to_hz(ppm_val, 470.6)
        print(f"   {ppm_val:5.2f} ppm = {hz_val:7.1f} Hz")
    
    # Test 3: Tolerancias
    print("\n3️⃣ TOLERANCIAS DE MATCHING PARA 19F:")
    print("-" * 70)
    print(f"   FWHM =  5 Hz → Tolerancia = {F19Config.TOLERANCE_TIGHT:.4f} ppm "
          f"(±{ppm_to_hz(F19Config.TOLERANCE_TIGHT, 470.6):.1f} Hz)")
    print(f"   FWHM = 10 Hz → Tolerancia = {F19Config.TOLERANCE_NORMAL:.4f} ppm "
          f"(±{ppm_to_hz(F19Config.TOLERANCE_NORMAL, 470.6):.1f} Hz)")
    print(f"   FWHM = 20 Hz → Tolerancia = {F19Config.TOLERANCE_RELAXED:.4f} ppm "
          f"(±{ppm_to_hz(F19Config.TOLERANCE_RELAXED, 470.6):.1f} Hz)")
    
    old_tolerance = 1.5
    print(f"\n   ⚠️  Tolerancia ANTERIOR: {old_tolerance} ppm = "
          f"{ppm_to_hz(old_tolerance, 470.6):.0f} Hz")
    print(f"   ✅  Mejora: {old_tolerance / F19Config.TOLERANCE_NORMAL:.0f}× más preciso")
    
    # Test 4: Análisis de multiplete
    print("\n4️⃣ ANÁLISIS DE MULTIPLETES:")
    print("-" * 70)
    print(f"   CF3 acoplado a CF2 (3JFF=10Hz):")
    width = estimate_multiplet_width(10, 1)
    print(f"      → Triplete de ancho ~{width:.0f} Hz "
          f"({hz_to_ppm(width, 470.6):.3f} ppm)")
    
    print(f"\n   CF2 central acoplado a 2 CF2 (3JFF=12Hz cada uno):")
    width = estimate_multiplet_width(12, 2)
    print(f"      → Multiplete de ancho ~{width:.0f} Hz "
          f"({hz_to_ppm(width, 470.6):.3f} ppm)")
    
    # Test 5: Validación cuantitativa
    print("\n5️⃣ VALIDACIÓN DE CONDICIONES CUANTITATIVAS:")
    print("-" * 70)
    
    test_cases = [
        (1.0, 1.0, "Delay insuficiente"),
        (3.0, 1.0, "Delay marginal"),
        (5.0, 1.0, "Delay óptimo")
    ]
    
    for delay, t1, description in test_cases:
        valid, warnings = validate_quantitative_conditions(delay, t1)
        status = "✅ VÁLIDO" if valid else "❌ NO VÁLIDO"
        print(f"\n   {description}: D1={delay}s, T1={t1}s → {status}")
        if warnings:
            for w in warnings:
                print(f"      {w}")
    
    print("\n" + "="*70)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("="*70 + "\n")