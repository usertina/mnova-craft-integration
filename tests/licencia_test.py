#!/usr/bin/env python3
"""
Test de Verificación de .env (Optimizado)
Comprueba que todas las claves secretas necesarias están cargadas.
"""

import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# --- Configuración de Rutas ---
# Asume que .env está en la carpeta 'backend'
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
DOTENV_PATH = PROJECT_ROOT / "backend" / ".env"
# -----------------------------

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_header(title):
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🧪 TEST: {title.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET} | {message}")

def print_fail(message):
    print(f"{Colors.RED}❌ FAIL{Colors.RESET} | {message}")

def main():
    print_header("Verificación de variables de entorno (.env)")

    if not DOTENV_PATH.exists():
        print_fail(f"No se encontró el archivo .env en: {DOTENV_PATH}")
        print("   Por favor, crea el archivo 'backend/.env' a partir de '.env.example'")
        return 1
    
    print(f"✅ Archivo .env encontrado en: {DOTENV_PATH}\n")
    load_dotenv(DOTENV_PATH)

    required_keys = [
        "FLASK_SECRET_KEY",
        "CRAFTRMN_MASTER_KEY",
        "JWT_SECRET_KEY",
        "PASSWORD_SALT",
        "GOOGLE_SCRIPT_URL" # Añadida, ya que es crítica para la sincronización
    ]
    
    results = {}
    missing_keys = False

    for key in required_keys:
        value = os.getenv(key)
        if value:
            print_pass(f"{key}: Encontrada (Valor: {value[:4]}...{value[-4:]})")
            results[key] = True
        else:
            print_fail(f"{key}: ¡NO ENCONTRADA!")
            results[key] = False
            missing_keys = True

    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'-' * 70}{Colors.RESET}")
    if missing_keys:
        print(f"{Colors.RED}❌ RESULTADO: Faltan variables de entorno críticas.{Colors.RESET}")
        print("   Revisa tu archivo 'backend/.env' y asegúrate de que todas las claves están definidas.")
        return 1
    else:
        print(f"{Colors.GREEN}🎉 ¡EXCELENTE! Todas las variables de entorno están cargadas.{Colors.RESET}")
        return 0

if __name__ == "__main__":
    sys.exit(main())