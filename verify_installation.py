#!/usr/bin/env python3
"""
Script de verificación rápida para CraftRMN Pro v2.3
Verifica que todos los archivos corregidos estén en su lugar
y que las correcciones de Levitt estén aplicadas.
"""

import sys
import os
from pathlib import Path

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def check_file(filepath, required_strings=None):
    """
    Verifica que un archivo exista y opcionalmente que contenga ciertas strings.
    """
    if not os.path.exists(filepath):
        print(f"{RED}❌ FALTA: {filepath}{RESET}")
        return False
    
    print(f"{GREEN}✅ Existe: {filepath}{RESET}")
    
    if required_strings:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for req_str, description in required_strings:
            if req_str in content:
                print(f"   {GREEN}✓{RESET} {description}")
            else:
                print(f"   {RED}✗{RESET} {RED}FALTA: {description}{RESET}")
                return False
    
    return True

def check_imports():
    """Verifica que todos los imports necesarios funcionen"""
    print_header("VERIFICANDO IMPORTS")
    
    all_ok = True
    
    # Verificar imports de backend
    try:
        sys.path.insert(0, 'backend')
        print(f"{BLUE}Importando módulos del backend...{RESET}")
        
        from nmr_constants import (
            F19Config, 
            calculate_nucleus_frequency, 
            ppm_to_hz, 
            hz_to_ppm,
            calculate_linewidth_tolerance
        )
        print(f"{GREEN}✅ nmr_constants importado correctamente{RESET}")
        
        # Verificar cálculos
        f19_freq = calculate_nucleus_frequency(500, '19F')
        if abs(f19_freq - 470.6) < 0.1:
            print(f"   {GREEN}✓{RESET} Frecuencia 19F correcta: {f19_freq:.1f} MHz")
        else:
            print(f"   {RED}✗{RESET} Frecuencia 19F incorrecta: {f19_freq:.1f} MHz (esperado: 470.6)")
            all_ok = False
        
        hz_val = ppm_to_hz(1.0, 470.6)
        if abs(hz_val - 470.6) < 0.1:
            print(f"   {GREEN}✓{RESET} Conversión ppm→Hz correcta")
        else:
            print(f"   {RED}✗{RESET} Conversión ppm→Hz incorrecta")
            all_ok = False
        
    except Exception as e:
        print(f"{RED}❌ Error importando nmr_constants: {e}{RESET}")
        all_ok = False
    
    try:
        from pfas_database import PFAS_DATABASE, FUNCTIONAL_GROUP_SIGNATURES
        print(f"{GREEN}✅ pfas_database importado correctamente{RESET}")
        print(f"   {GREEN}✓{RESET} Base de datos: {len(PFAS_DATABASE)} compuestos PFAS")
        
    except Exception as e:
        print(f"{RED}❌ Error importando pfas_database: {e}{RESET}")
        all_ok = False
    
    try:
        from pfas_detector_enhanced import PFASDetectorEnhanced
        print(f"{GREEN}✅ pfas_detector_enhanced importado correctamente{RESET}")
        
        # Verificar inicialización correcta
        detector = PFASDetectorEnhanced(nucleus_frequency_mhz=470.6)
        print(f"   {GREEN}✓{RESET} Detector inicializa correctamente")
        print(f"   {GREEN}✓{RESET} Tolerancia: {detector.base_tolerance_ppm:.4f} ppm")
        
        if abs(detector.base_tolerance_ppm - 0.043) < 0.01:
            print(f"   {GREEN}✓{RESET} Tolerancia física correcta (~0.04 ppm)")
        else:
            print(f"   {YELLOW}⚠{RESET} Tolerancia: {detector.base_tolerance_ppm:.4f} ppm (esperado: ~0.043)")
        
    except Exception as e:
        print(f"{RED}❌ Error importando pfas_detector_enhanced: {e}{RESET}")
        all_ok = False
    
    # Verificar imports de worker
    try:
        sys.path.insert(0, 'worker')
        from analyzer import SpectrumAnalyzer
        print(f"{GREEN}✅ analyzer (SpectrumAnalyzer) importado correctamente{RESET}")
        
        # Verificar inicialización
        analyzer = SpectrumAnalyzer(spectrometer_h1_freq_mhz=500.0)
        print(f"   {GREEN}✓{RESET} Analyzer inicializa correctamente")
        print(f"   {GREEN}✓{RESET} Frecuencia 19F: {analyzer.f19_frequency:.1f} MHz")
        
        if hasattr(analyzer, 'pfas_detector'):
            print(f"   {GREEN}✓{RESET} Detector de PFAS integrado correctamente")
        else:
            print(f"   {RED}✗{RESET} FALTA: pfas_detector en SpectrumAnalyzer")
            all_ok = False
        
    except Exception as e:
        print(f"{RED}❌ Error importando analyzer: {e}{RESET}")
        all_ok = False
    
    return all_ok

def main():
    print_header("VERIFICACIÓN DE CRAFTRMN PRO v2.3")
    print(f"{BLUE}Verificando implementación de correcciones según Levitt{RESET}\n")
    
    all_checks_passed = True
    
    # 1. Verificar estructura de directorios
    print_header("ESTRUCTURA DE DIRECTORIOS")
    
    required_dirs = [
        'backend',
        'worker',
        'frontend',
        'frontend/js'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"{GREEN}✅ {dir_path}/{RESET}")
        else:
            print(f"{RED}❌ FALTA: {dir_path}/{RESET}")
            all_checks_passed = False
    
    # 2. Verificar archivos backend
    print_header("ARCHIVOS BACKEND")
    
    backend_files = {
        'backend/nmr_constants.py': [
            ('calculate_nucleus_frequency', 'Función de cálculo de frecuencias'),
            ('ppm_to_hz', 'Conversión ppm→Hz'),
            ('FREQUENCY_RATIOS', 'Tabla de ratios según Levitt'),
            ('F19Config', 'Configuración 19F-NMR')
        ],
        'backend/pfas_database.py': [
            ('PFAS_DATABASE', 'Base de datos de PFAS'),
            ('PFOS', 'Compuesto PFOS'),
            ('PFOA', 'Compuesto PFOA')
        ],
        'backend/pfas_detector_enhanced.py': [
            ('PFASDetectorEnhanced', 'Clase del detector'),
            ('nucleus_frequency_mhz', 'Parámetro de inicialización correcto'),
            ('detect_pfas', 'Método de detección'),
            ('Levitt', 'Referencias a Levitt en comentarios')
        ]
    }
    
    for filepath, checks in backend_files.items():
        if not check_file(filepath, checks):
            all_checks_passed = False
    
    # 3. Verificar archivos worker
    print_header("ARCHIVOS WORKER")
    
    worker_files = {
        'worker/analyzer.py': [
            ('SpectrumAnalyzer', 'Clase principal del analizador'),
            ('self.pfas_detector = PFASDetectorEnhanced', 'Inicialización correcta del detector'),
            ('self.f19_frequency', 'Configuración de frecuencia 19F'),
            ('_correct_baseline_polynomial', 'Método de corrección de baseline'),
            ('Levitt', 'Referencias a Levitt')
        ]
    }
    
    for filepath, checks in worker_files.items():
        if not check_file(filepath, checks):
            all_checks_passed = False
    
    # 4. Verificar archivos frontend
    print_header("ARCHIVOS FRONTEND")
    
    frontend_files = {
        'frontend/js/apiClient.js': [
            ('parseBackendError', 'Función de parsing de errores mejorada'),
            ('window.APP_LOGGER', 'Sistema de logging')
        ],
        'frontend/js/config.js': [
            ('APP_CONFIG', 'Configuración de la app'),
            ('apiBaseURL', 'URL base del API')
        ]
    }
    
    for filepath, checks in frontend_files.items():
        if not check_file(filepath, checks):
            # No marcar como fallo crítico si faltan archivos frontend
            print(f"{YELLOW}⚠ Archivo frontend faltante o sin verificar{RESET}")
    
    # 5. Verificar imports
    if check_imports():
        print(f"\n{GREEN}✅ Todos los imports funcionan correctamente{RESET}")
    else:
        print(f"\n{RED}❌ Hay problemas con los imports{RESET}")
        all_checks_passed = False
    
    # Resultado final
    print_header("RESULTADO FINAL")
    
    if all_checks_passed:
        print(f"{GREEN}✅ TODAS LAS VERIFICACIONES PASARON{RESET}")
        print(f"\n{GREEN}El sistema está correctamente configurado con las correcciones de Levitt.{RESET}")
        print(f"\n{BLUE}Próximos pasos:{RESET}")
        print(f"  1. Reinicia el servidor Flask")
        print(f"  2. Recarga el navegador (Ctrl+F5)")
        print(f"  3. Prueba con un archivo CSV")
        return 0
    else:
        print(f"{RED}❌ ALGUNAS VERIFICACIONES FALLARON{RESET}")
        print(f"\n{YELLOW}Revisa los errores arriba y:{RESET}")
        print(f"  1. Copia los archivos corregidos a las rutas indicadas")
        print(f"  2. Verifica que la estructura de directorios sea correcta")
        print(f"  3. Ejecuta este script nuevamente")
        return 1

if __name__ == '__main__':
    sys.exit(main())