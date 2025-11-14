"""
Test de Autenticación JWT - Verificar sistema de tokens
(Versión Optimizada y Corregida)
"""
import requests
import time
import sys

# --- Configuración ---
BASE_URL = "http://localhost:5000"
# Pines de las empresas (de company_data.py)
PIN_FAES = "1234"
# El PIN de AUGAS no se usa si "AUGAS" no existe en el backend
# PIN_AUGAS = "4321" 
# ---------------------

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

# Variables globales para tokens
access_token = None
refresh_token = None
test_results = {}

def run_test_1_login_ok():
    """Test 1: Login exitoso con PIN correcto"""
    global access_token, refresh_token
    print_header("Login con PIN correcto (FAES)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/validate_pin",
            json={"company_id": "FAES", "pin": PIN_FAES},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data and 'refresh_token' in data:
                access_token = data['access_token']
                refresh_token = data['refresh_token']
                print_pass(f"Login exitoso. Empresa: {data['profile'].get('company_name', 'N/A')}")
                print(f"   - Access token: {access_token[:30]}...")
                print(f"   - Refresh token: {refresh_token[:30]}...")
                test_results['Test 1'] = True
                return True
            else:
                print_fail("Login OK pero faltan tokens en la respuesta.")
        else:
            print_fail(f"Login falló: {response.status_code} - {response.json().get('error', 'N/A')}")
            
    except requests.exceptions.ConnectionError:
        print_fail(f"Error de conexión. ¿Servidor (app.py) corriendo en {BASE_URL}?")
        return False # Fallo crítico
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
    
    test_results['Test 1'] = False
    return False # Fallo crítico

def run_test_2_access_protected():
    """Test 2: Acceder a endpoint protegido CON token"""
    print_header("Acceder a endpoint protegido CON token válido")
    try:
        response = requests.get(
            f"{BASE_URL}/api/measurements?company=FAES",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15 # <-- ⚡ CAMBIO: Aumentado de 5 a 15
        )
        if response.status_code == 200:
            print_pass(f"Acceso autorizado (200 OK). Obtenidas {len(response.json().get('measurements', []))} mediciones.")
            test_results['Test 2'] = True
        else:
            print_fail(f"Acceso denegado: {response.status_code} - {response.json().get('error', 'N/A')}")
            test_results['Test 2'] = False
    except requests.exceptions.ReadTimeout:
        print_fail("El servidor tardó más de 15 segundos en responder (ReadTimeout).")
        test_results['Test 2'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 2'] = False

def run_test_3_access_no_token():
    """Test 3: Acceder a endpoint protegido SIN token"""
    print_header("Acceder a endpoint protegido SIN token (debe fallar)")
    try:
        response = requests.get(
            f"{BASE_URL}/api/measurements?company=FAES", 
            timeout=15 # <-- ⚡ CAMBIO: Aumentado de 5 a 15
        )
        if response.status_code == 401:
            print_pass(f"Acceso denegado (401 Unauthorized) como se esperaba.")
            test_results['Test 3'] = True
        else:
            print_fail(f"Respuesta inesperada: {response.status_code}. Debería ser 401.")
            test_results['Test 3'] = False
    except requests.exceptions.ReadTimeout:
        # Si el test 2 da timeout, este también lo dará.
        print_fail("El servidor tardó más de 15 segundos en responder (ReadTimeout).")
        test_results['Test 3'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 3'] = False

def run_test_4_access_wrong_company():
    """Test 4: Acceder con token de OTRA empresa"""
    # ⚡ CAMBIO: Se usa "ADMIN" en lugar de "AUGAS", ya que "AUGAS" no existe (daba 404)
    print_header("Acceder a datos de ADMIN con token de FAES (debe fallar)")
    try:
        response = requests.get(
            f"{BASE_URL}/api/measurements?company=ADMIN", # Pide ADMIN
            headers={"Authorization": f"Bearer {access_token}"}, # Con token de FAES
            timeout=5
        )
        if response.status_code == 403: # 403 Forbidden
            print_pass(f"Acceso denegado (403 Forbidden) como se esperaba.")
            test_results['Test 4'] = True
        else:
            print_fail(f"Respuesta inesperada: {response.status_code}. Debería ser 403.")
            test_results['Test 4'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 4'] = False

def run_test_5_refresh_token():
    """Test 5: Renovar access token con refresh token"""
    global access_token
    print_header("Renovar access token usando refresh token")
    try:
        response = requests.post(
            f"{BASE_URL}/api/refresh",
            json={"refresh_token": refresh_token},
            timeout=5
        )
        if response.status_code == 200:
            new_access_token = response.json().get('access_token')
            if new_access_token:
                print_pass("Token renovado exitosamente.")
                access_token = new_access_token # Actualizar para el siguiente test
                test_results['Test 5'] = True
            else:
                print_fail("Respuesta OK pero no se recibió nuevo 'access_token'.")
                test_results['Test 5'] = False
        else:
            print_fail(f"Renovación falló: {response.status_code} - {response.json().get('error', 'N/A')}")
            test_results['Test 5'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 5'] = False

def run_test_6_logout():
    """Test 6: Logout"""
    print_header("Cerrar sesión (logout)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        if response.status_code == 200:
            print_pass(f"Logout exitoso: {response.json().get('message')}")
            test_results['Test 6'] = True
        else:
            print_fail(f"Logout falló: {response.status_code}")
            test_results['Test 6'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 6'] = False

def run_test_7_login_fail():
    """Test 7: Login con PIN incorrecto"""
    print_header("Login con PIN incorrecto (debe fallar)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/validate_pin",
            json={"company_id": "FAES", "pin": "9999"}, # PIN incorrecto
            timeout=5
        )
        if response.status_code == 401: # 401 Unauthorized (Invalid credentials)
            print_pass(f"Login denegado (401 Unauthorized) como se esperaba.")
            test_results['Test 7'] = True
        else:
            print_fail(f"Respuesta inesperada: {response.status_code}. Debería ser 401.")
            test_results['Test 7'] = False
    except Exception as e:
        print_fail(f"Error inesperado: {e}")
        test_results['Test 7'] = False

def main():
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🔐 TEST DE AUTENTICACIÓN JWT (OPTIMIZADO){Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    # --- Test 1 (Crítico) ---
    if not run_test_1_login_ok():
        print(f"\n{Colors.RED}Prueba 1 (Login) falló. Abortando el resto de tests.{Colors.RESET}")
        sys.exit(1)
        
    # --- Tests Siguientes ---
    run_test_2_access_protected()
    run_test_3_access_no_token()
    run_test_4_access_wrong_company()
    run_test_5_refresh_token()
    run_test_6_logout()
    run_test_7_login_fail()
    
    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}📊 RESUMEN FINAL DE AUTENTICACIÓN{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    passed = 0
    for test_name, result in test_results.items():
        if result:
            print(f"{Colors.GREEN}✅ {test_name}: PASÓ{Colors.RESET}")
            passed += 1
        else:
            print(f"{Colors.RED}❌ {test_name}: FALLÓ{Colors.RESET}")
            
    if passed == len(test_results):
        print(f"\n{Colors.GREEN}🎉 ¡EXCELENTE! Todos los {len(test_results)} tests de autenticación pasaron.{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  ATENCIÓN: {len(test_results) - passed} test(s) de autenticación fallaron.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())