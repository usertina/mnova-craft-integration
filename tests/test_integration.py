#!/usr/bin/env python3
"""
Script de Test de Integración End-to-End (v2 Optimizado)
=========================================================
Prueba el flujo completo:
1. Servidor responde (Health Check)
2. Carga de /api/config
3. Verificación de archivo DB
4. Login con PIN de empresa (ej. FAES)
5. Envío de un archivo para análisis (con token)
6. Verificación de que el análisis se guardó en la BD (devuelve measurement_id)

Ejecutar con el servidor Flask (app.py) corriendo.
"""

import requests
import json
from pathlib import Path
import sys
import os

# --- Configuración ---
BASE_URL = "http://localhost:5000"
# Pines de las empresas (de company_data.py)
COMPANY_ID_TO_TEST = "FAES"
COMPANY_PIN_TO_TEST = "1234" # Asegúrate de que este es el PIN de FAES
# ---------------------

# --- Configuración de Rutas ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TEST_FILE_PATH = SCRIPT_DIR / "test_spectrum.txt"
DB_PATH = BACKEND_DIR / "storage" / "measurements.db"
# -----------------------------

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
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

# Diccionario para rastrear resultados
test_results = {}

def get_token(company_id, pin):
    """Helper para obtener un token JWT."""
    print_header(f"Paso 4: Login como '{company_id}'")
    try:
        r = requests.post(f"{BASE_URL}/api/validate_pin", json={
            "company_id": company_id,
            "pin": pin
        }, timeout=5)
        r.raise_for_status() # Lanza error si no es 2xx
        
        token = r.json().get('access_token')
        if not token:
            print_fail("Respuesta 200 OK pero no se recibió 'access_token'.")
            return None
        
        print_pass(f"Login exitoso. Token obtenido.")
        test_results['Login'] = True
        return token
        
    except requests.exceptions.HTTPError as e:
        print_fail(f"Login falló: {e.response.status_code} {e.response.json().get('error', 'N/A')}")
    except requests.exceptions.ConnectionError:
        print_fail(f"Error de conexión. ¿Servidor (app.py) corriendo en {BASE_URL}?")
    except Exception as e:
        print_fail(f"Error inesperado en login: {e}")
        
    test_results['Login'] = False
    return None

def test_health():
    """Paso 1: Verificar que el servidor responde"""
    print_header("Paso 1: Verificando servidor (Health Check)")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        resp.raise_for_status()
        print_pass(f"Servidor funcionando (200 OK). Versión: {resp.json().get('version', 'N/A')}")
        test_results['Health Check'] = True
        return True
    except requests.exceptions.ConnectionError:
        print_fail(f"Error de conexión. ¿Servidor (app.py) corriendo en {BASE_URL}?")
    except requests.exceptions.HTTPError as e:
        print_fail(f"Servidor devolvió error: {e.response.status_code}")
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
    
    test_results['Health Check'] = False
    return False

def test_config():
    """Paso 2: Verificar configuración del dispositivo"""
    print_header("Paso 2: Verificando /api/config")
    try:
        resp = requests.get(f"{BASE_URL}/api/config", timeout=5)
        resp.raise_for_status()
        config = resp.json()
        
        if 'device_id' in config and 'available_companies' in config:
            print_pass(f"Configuración cargada. Device ID: {config['device_id']}")
            print(f"   - Dispositivo activado: {config.get('activated')}")
            print(f"   - Empresas disponibles: {len(config.get('available_companies', []))}")
            test_results['Config API'] = True
            return True
        else:
            print_fail("La respuesta de /api/config no tiene la estructura esperada.")
            
    except Exception as e:
        print_fail(f"Error cargando /api/config: {e}")
    
    test_results['Config API'] = False
    return False

def verify_database_file():
    """Paso 3: Verificar que el archivo de base de datos existe"""
    print_header("Paso 3: Verificando archivo de base de datos")
    if DB_PATH.exists():
        size_kb = DB_PATH.stat().st_size / 1024
        print_pass(f"Base de datos existe en: {DB_PATH.relative_to(PROJECT_ROOT)}")
        print(f"   - Tamaño: {size_kb:.2f} KB")
        test_results['DB File'] = True
        return True
    else:
        print_fail(f"No se encuentra la base de datos en: {DB_PATH}")
        test_results['DB File'] = False
        return False

def test_analysis_with_db(token, company_id):
    """Paso 5: Verificar que el análisis guarda en SQLite (CON ARCHIVO REAL)"""
    print_header(f"Paso 5: Probando análisis End-to-End ({company_id})")
    
    # --- ⚡ CAMBIO: Buscar un archivo de prueba real ---
    analysis_test_file = None
    output_dir = BACKEND_DIR / "storage" / "output"
    csv_files = sorted(output_dir.glob("*.csv"))
    
    if not csv_files:
        print_fail(f"No se encontró ningún archivo CSV de prueba en {output_dir}")
        print("   Ejecuta 'test_analyzer_offline.py' primero, o añade un CSV allí.")
        test_results['Analysis E2E'] = False
        return False
    
    analysis_test_file = csv_files[0]
    print(f"   - Usando archivo de prueba real: {analysis_test_file.name}")
    # --- FIN DEL CAMBIO ---

    try:
        with open(analysis_test_file, 'rb') as f:
            form_data = {
                'company_id': company_id,
                'parameters': json.dumps({'concentration': 1.0})
            }
            files = {'file': (analysis_test_file.name, f, 'text/csv')} # Tipo MIME correcto
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = requests.post(
                f"{BASE_URL}/api/analyze",
                files=files,
                data=form_data,
                headers=headers,
                timeout=15 
            )
            
            resp.raise_for_status() # Lanza error si no es 200
            
            result = resp.json() # <-- Aquí es donde fallaba
            
            if 'measurement_id' in result and result['measurement_id'] is not None:
                print_pass(f"Análisis completado y guardado en SQLite con ID: {result['measurement_id']}")
                test_results['Analysis E2E'] = True
                return True
            else:
                print_fail("Análisis OK (200) pero no se recibió 'measurement_id'.")

    except requests.exceptions.HTTPError as e:
        print_fail(f"Error en /api/analyze: {e.response.status_code} - {e.response.text[:200]}...")
    except Exception as e:
        print_fail(f"Error inesperado en análisis: {e}")
        import traceback
        traceback.print_exc() # Imprime el traceback completo
            
    test_results['Analysis E2E'] = False
    return False

def main():
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🚀 TEST DE INTEGRACIÓN END-TO-END - CraftRMN Pro{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")

    # Pasos 1, 2, 3 (Críticos)
    if not test_health() or not test_config() or not verify_database_file():
        print_fail("Fallaron las comprobaciones iniciales (servidor/BD). Abortando.")
        sys.exit(1)

    # Paso 4 (Crítico)
    token = get_token(COMPANY_ID_TO_TEST, COMPANY_PIN_TO_TEST)
    if not token:
        print_fail("Fallo de login. Abortando prueba de análisis.")
        sys.exit(1)
        
    # Paso 5 (Crítico)
    if not test_analysis_with_db(token, COMPANY_ID_TO_TEST):
        print_fail("Fallo el test de análisis End-to-End.")
        sys.exit(1)

    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}📊 RESUMEN FINAL DE INTEGRACIÓN{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    passed = 0
    for test_name, result in test_results.items():
        if result:
            print(f"{Colors.GREEN}✅ {test_name}: PASÓ{Colors.RESET}")
            passed += 1
        else:
            print(f"{Colors.RED}❌ {test_name}: FALLÓ{Colors.RESET}")
            
    if passed == len(test_results):
        print(f"\n{Colors.GREEN}🎉 ¡INTEGRACIÓN EXITOSA! Todos los {len(test_results)} pasos pasaron.{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  FALLO DE INTEGRACIÓN: {len(test_results) - passed} paso(s) fallaron.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())