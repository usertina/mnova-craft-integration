#!/usr/bin/env python3
"""
Test de Estructura Completa de la App (Optimizado)
Verifica todos los directorios y archivos clave del proyecto.
"""

import sys
from pathlib import Path

# --- Configuración de Rutas ---
BASE_PATH = Path(__file__).resolve().parent.parent
# -----------------------------

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}🧪 TEST: {title.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'-' * 70}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET} | {message}")

def print_fail(message):
    print(f"{Colors.RED}❌ FAIL{Colors.RESET} | {message}")

def print_info(message):
    print(f"   {Colors.CYAN}ℹ️  {message}{Colors.RESET}")

def check_paths(base, paths, is_dir=False) -> bool:
    """Verifica una lista de archivos o directorios"""
    all_ok = True
    for p in paths:
        path_to_check = base / p
        if (is_dir and path_to_check.is_dir()) or (not is_dir and path_to_check.is_file()):
            print_pass(f"{path_to_check.relative_to(BASE_PATH)}")
        else:
            print_fail(f"FALTA: {path_to_check.relative_to(BASE_PATH)}")
            all_ok = False
    return all_ok

def main():
    print_header("Verificación de Estructura Completa del Proyecto")
    
    test_results = {}

    # --- 1. Directorios Principales ---
    print("\n--- 1. Directorios Principales ---")
    test_results['Dirs_Root'] = check_paths(BASE_PATH, [
        "backend",
        "worker",
        "frontend",
        "tests"
    ], is_dir=True)

    # --- 2. Backend Core ---
    print("\n--- 2. Backend (Core) ---")
    test_results['Backend_Core'] = check_paths(BASE_PATH, [
        "backend/app.py",
        "backend/database.py",
        "backend/auth.py",
        "backend/security.py",
        "backend/extensions.py",
        "backend/config_manager.py",
        "backend/company_data.py",
        "backend/pfas_database.py",
        "backend/audit_logger.py",
        "backend/.env",
        # --- INICIO DE LA CORRECCIÓN ---
        "backend/nmr_constants.py" # Movido desde 'worker'
        # --- FIN DE LA CORRECCIÓN ---
    ])

    # --- 3. Backend (Rutas) ---
    print("\n--- 3. Backend (Rutas) ---")
    test_results['Backend_Routes'] = check_paths(BASE_PATH, [
        "backend/routes/auth_routes.py",
        "backend/routes/analysis_routes.py",
        "backend/routes/config_routes.py",
        "backend/routes/measurement_routes.py",
        "backend/routes/export_routes.py",
        "backend/routes/sync_routes.py",
        "backend/routes/frontend_routes.py"
    ])

    # --- 4. Worker ---
    print("\n--- 4. Worker (Lógica de Análisis) ---")
    test_results['Worker'] = check_paths(BASE_PATH, [
        "worker/analyzer.py"
        # nmr_constants.py movido a la sección 'Backend'
    ])

    # --- 5. Frontend (JS Core) ---
    print("\n--- 5. Frontend (JavaScript Core) ---")
    test_results['Frontend_Core'] = check_paths(BASE_PATH, [
        "frontend/js/app.js",
        "frontend/js/apiClient.js",
        "frontend/js/chartManager.js",
        "frontend/js/dashboard.js",
        "frontend/js/comparison.js",
        "frontend/js/uiComponents.js",
        "frontend/js/fileProcessor.js",
        # --- INICIO DE LA CORRECCIÓN ---
        "frontend/js/i18n/LanguageManager.js" # Ruta corregida
        # --- FIN DE LA CORRECCIÓN ---
    ])
    
    # --- 6. Frontend (Estructura i18n) ---
    print("\n--- 6. Frontend (Traducciones) ---")
    test_results['Frontend_i18n'] = check_paths(BASE_PATH, [
        "frontend/js/i18n/translations/es.json",
        "frontend/js/i18n/translations/en.json",
        "frontend/js/i18n/translations/eu.json"
    ])

    # --- 7. Resumen de Conteo de Archivos ---
    print("\n--- 7. Conteo de Archivos (Resumen) ---")
    py_files = len(list(BASE_PATH.glob('backend/**/*.py'))) + len(list(BASE_PATH.glob('worker/**/*.py')))
    js_files = len(list(BASE_PATH.glob('frontend/js/**/*.js')))
    test_files = len(list(BASE_PATH.glob('tests/*.py')))
    
    print_info(f"{py_files} archivos .py encontrados en 'backend/' y 'worker/'")
    print_info(f"{js_files} archivos .js encontrados en 'frontend/js/'")
    print_info(f"{test_files} archivos .py encontrados en 'tests/'")

    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}📊 RESUMEN DE ESTRUCTURA{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    all_passed = all(test_results.values())
    
    for test_name, result in test_results.items():
        status = f"{Colors.GREEN}✅ PASÓ{Colors.RESET}" if result else f"{Colors.RED}❌ FALLÓ{Colors.RESET}"
        print(f"{status} | {test_name}")
            
    if all_passed:
        print(f"\n{Colors.GREEN}🎉 ¡EXCELENTE! La estructura completa de tu proyecto parece correcta.{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  ATENCIÓN: Faltan archivos o directorios clave.{Colors.RESET}")
        print("   Revisa los errores ❌ de arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())