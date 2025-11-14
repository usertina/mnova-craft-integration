#!/usr/bin/env python3
"""
Test Suite de Seguridad Unificada - CraftRMN Pro
==================================================
Verifica:
1. Headers de Seguridad (incluyendo CSP para 'blob:')
2. Rate Limiting (límites de abuso)
3. Inyección SQL (en endpoints de API)
4. Subida de Archivos Maliciosos (Path Traversal, Exe, etc.)

Ejecutar con el servidor Flask (app.py) corriendo.
"""

import requests
import sys
import time
from io import BytesIO

# --- Configuración ---
BASE_URL = "http://localhost:5000"
ADMIN_PIN = "0000"  # Asegúrate de que este es el PIN de 'ADMIN'
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

def get_admin_token():
    """Obtiene un token de administrador para las pruebas"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/validate_pin",
            json={"company_id": "ADMIN", "pin": ADMIN_PIN},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get('access_token')
            if token:
                print(f"{Colors.GREEN}✅ Token de ADMIN obtenido.{Colors.RESET}")
                return token
        print(f"{Colors.RED}❌ FAIL: No se pudo obtener token de ADMIN. ¿PIN '{ADMIN_PIN}' es correcto?{Colors.RESET}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ FAIL: No se puede conectar al servidor en {BASE_URL}{Colors.RESET}")
        return None
    except Exception as e:
        print(f"{Colors.RED}❌ FAIL: Error obteniendo token: {e}{Colors.RESET}")
        return None

# --- SUITE 1: HEADERS DE SEGURIDAD ---

def test_security_headers():
    print_header("Headers de Seguridad")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    except Exception as e:
        print_fail(f"No se pudo conectar al servidor: {e}")
        return False
    
    headers = response.headers
    results = []

    def check(name, expected):
        val = headers.get(name)
        if val and expected.lower() in val.lower():
            print_pass(f"{name}: {val}")
            return True
        print_fail(f"{name}: Esperado '{expected}', Obtenido '{val}'")
        return False

    results.append(check('X-Frame-Options', 'SAMEORIGIN'))
    results.append(check('X-Content-Type-Options', 'nosniff'))
    results.append(check('X-XSS-Protection', '1; mode=block'))
    results.append(check('Content-Security-Policy', "default-src 'self'"))
    
    # Verificación CRÍTICA para la exportación de gráficos
    results.append(check('Content-Security-Policy', "img-src 'self' data: https: blob:"))
    
    # Verificar que el Server header no revela información
    server = headers.get('Server', '')
    if 'Werkzeug' in server or 'Python' in server:
        print_fail(f"Server header revela tecnología: {server}")
        results.append(False)
    else:
        print_pass(f"Server header oculto: {server}")
        results.append(True)

    return all(results)

# --- SUITE 2: RATE LIMITING ---

def test_rate_limiting():
    print_header("Rate Limiting (Límites de Abuso)")
    blocked_count = 0
    for i in range(8): # 8 intentos (debe bloquear después de 5)
        try:
            r = requests.post(
                f"{BASE_URL}/api/validate_pin",
                json={"company_id": "FAES", "pin": "9999"}, # PIN incorrecto
                timeout=2
            )
            if r.status_code == 429:
                print(f"   Intento {i+1}: 🚫 BLOQUEADO (429)")
                blocked_count += 1
            else:
                print(f"   Intento {i+1}: ✅ Permitido ({r.status_code})")
        except Exception as e:
            print_fail(f"Error en intento {i+1}: {e}")
            return False

    if blocked_count > 0:
        print_pass("Rate limit de 'validate_pin' funciona.")
        return True
    print_fail("Rate limit de 'validate_pin' NO se activó.")
    return False

# --- SUITE 3: INYECCIÓN SQL (vía API) ---

def test_sql_injection(token):
    print_header("Inyección SQL (en API /history)")
    if not token: return False
    
    headers = {"Authorization": f"Bearer {token}"}
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE measurements--",
        "1' UNION SELECT * FROM measurements--"
    ]
    results = []

    for payload in payloads:
        try:
            r = requests.get(
                f"{BASE_URL}/api/history",
                params={'company_id': 'ADMIN', 'search': payload},
                headers=headers,
                timeout=5
            )
            # El servidor debe responder 200 OK, pero la sanitización
            # debe prevenir que el query malicioso devuelva resultados.
            if r.status_code == 200 and len(r.json().get('measurements', [])) == 0:
                print_pass(f"Payload bloqueado: {payload[:30]}...")
                results.append(True)
            else:
                print_fail(f"Payload peligroso: {payload[:30]}...")
                results.append(False)
        except Exception as e:
            print_fail(f"Error en test de SQLi: {e}")
            results.append(False)
            
    return all(results)

# --- SUITE 4: SUBIDA DE ARCHIVOS MALICIOSOS ---

def _test_upload(token, filename, content, expected_status):
    """Helper para la suite de subida de archivos"""
    files = {'file': (filename, BytesIO(content), 'application/octet-stream')}
    data = {'company_id': 'ADMIN'}
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            files=files, data=data, headers=headers, timeout=10
        )
        if response.status_code == expected_status:
            print_pass(f"'{filename}' → {response.status_code} (Esperado)")
            return True
        else:
            err = response.json().get('error', 'N/A') if response.status_code == 400 else ''
            print_fail(f"'{filename}' → Esperado {expected_status}, Obtenido {response.status_code}. {err}")
            return False
    except Exception as e:
        print_fail(f"'{filename}' → Error: {e}")
        return False

def test_file_uploads(token):
    print_header("Subida de Archivos Maliciosos (Seguridad)")
    if not token: return False

    tests = [
        # 1. Extensión prohibida
        ("malware.exe", b'fake exe data', 400),
        # 2. Path Traversal
        ("../../etc/passwd", b'test data', 400),
        # 3. Path Traversal (Windows)
        ("..\\..\\windows\\system32\\drivers\\etc\\hosts", b'test data', 400),
        # 4. Archivo legítimo (debe pasar la validación de seguridad)
        ("spectrum.csv", b'ppm,intensity\n1.0,100\n', 200) # Falla el análisis (500) o pasa (200)
    ]
    
    results = []
    for filename, content, status in tests:
        # El test 4 puede devolver 200 (éxito) o 500 (falla de análisis), 
        # ambos son correctos si pasan la validación de *seguridad* (que ocurre antes).
        if filename == "spectrum.csv":
            # Repetimos la lógica de _test_upload pero permitiendo 200 o 500
            try:
                r = requests.post(
                    f"{BASE_URL}/api/analyze",
                    files={'file': (filename, BytesIO(content), 'text/csv')},
                    data={'company_id': 'ADMIN'}, headers={'Authorization': f'Bearer {token}'}, timeout=10
                )
                if r.status_code in [200, 500]: # 200 (OK) o 500 (Error de Análisis) son aceptables
                    print_pass(f"'{filename}' → {r.status_code} (Pasa validación de seguridad)")
                    results.append(True)
                else:
                    print_fail(f"'{filename}' → Esperado 200 o 500, Obtenido {r.status_code}")
                    results.append(False)
            except Exception as e:
                print_fail(f"'{filename}' → Error: {e}")
                results.append(False)
        else:
            results.append(_test_upload(token, filename, content, status))
            
    return all(results)

# --- EJECUCIÓN PRINCIPAL ---

def main():
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🚀 SUITE DE SEGURIDAD INTEGRADA - CraftRMN Pro{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    token = get_admin_token()
    if not token:
        print(f"\n{Colors.RED}Pruebas abortadas: No se pudo obtener el token de admin.{Colors.RESET}")
        return 1

    results = {
        "Headers": test_security_headers(),
        "Rate Limit": test_rate_limiting(),
        "SQL Injection": test_sql_injection(token),
        "File Uploads": test_file_uploads(token)
    }
    
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}📊 RESUMEN FINAL DE SEGURIDAD{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    passed = 0
    for test_name, result in results.items():
        if result:
            print(f"{Colors.GREEN}✅ {test_name}: PASÓ{Colors.RESET}")
            passed += 1
        else:
            print(f"{Colors.RED}❌ {test_name}: FALLÓ{Colors.RESET}")
            
    if passed == len(results):
        print(f"\n{Colors.GREEN}🎉 ¡EXCELENTE! Todos los {len(results)} tests de seguridad pasaron.{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  ATENCIÓN: {len(results) - passed} test(s) de seguridad fallaron.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())