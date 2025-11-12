#!/usr/bin/env python3
"""
Verificación de instalación CraftRMN Pro v2.3
Comprueba estructura de directorios, archivos y imports
"""

import sys
from pathlib import Path
import importlib

# ----------------------------------------------------------------------
# Rutas base
# ----------------------------------------------------------------------
BASE_PATH = Path(__file__).resolve().parent.parent
BACKEND_PATH = BASE_PATH / "backend"
WORKER_PATH = BASE_PATH / "worker"
FRONTEND_PATH = BASE_PATH / "frontend/js"

# Agregar rutas al sys.path para que Python encuentre los módulos
sys.path.insert(0, str(BACKEND_PATH))
sys.path.insert(0, str(WORKER_PATH))

# ----------------------------------------------------------------------
# Directorios y archivos esperados
# ----------------------------------------------------------------------
expected_dirs = [
    BACKEND_PATH,
    WORKER_PATH,
    FRONTEND_PATH,
]

expected_files = [
    BACKEND_PATH / "nmr_constants.py",
    BACKEND_PATH / "pfas_database.py",
    BACKEND_PATH / "pfas_detector_enhanced.py",
    BACKEND_PATH / "i18n/es.json",
    BACKEND_PATH / "i18n/en.json",
    BACKEND_PATH / "i18n/eu.json",
    BACKEND_PATH / "i18n/gl.json",
    WORKER_PATH / "analyzer.py",
    FRONTEND_PATH / "apiClient.js",
    FRONTEND_PATH / "config.js",
    FRONTEND_PATH / "i18n/translations/es.json",
    FRONTEND_PATH / "i18n/translations/en.json",
    FRONTEND_PATH / "i18n/translations/eu.json",
    FRONTEND_PATH / "i18n/translations/gl.json",
]

# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------
def check_dirs(dirs):
    print("\n=== ESTRUCTURA DE DIRECTORIOS ===")
    for d in dirs:
        if d.exists():
            print(f"✅ {d.relative_to(BASE_PATH)}")
        else:
            print(f"❌ FALTA: {d.relative_to(BASE_PATH)}")

def check_files(files):
    print("\n=== ARCHIVOS ESPERADOS ===")
    for f in files:
        if f.exists():
            print(f"✅ {f.relative_to(BASE_PATH)}")
        else:
            print(f"❌ FALTA: {f.relative_to(BASE_PATH)}")

def check_imports(modules):
    print("\n=== VERIFICANDO IMPORTS BACKEND ===")
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"✅ Importando módulo {mod}: OK")
        except ImportError as e:
            print(f"❌ Error importando {mod}: {e}")

# ----------------------------------------------------------------------
# Ejecución principal
# ----------------------------------------------------------------------
def main():
    print("\n======================================================================")
    print("                  VERIFICACIÓN DE CRAFTRMN PRO v2.3")
    print("======================================================================")

    # Directorios
    check_dirs(expected_dirs)

    # Archivos
    check_files(expected_files)

    # Imports
    backend_modules = [
        "nmr_constants",
        "pfas_database",
        "pfas_detector_enhanced",
        "analyzer",
    ]
    check_imports(backend_modules)

    print("\n=== RESULTADO FINAL ===")
    print("Revisa los archivos/directorios y errores de imports arriba.\n")

if __name__ == "__main__":
    main()
