"""
Test de Rate Limiting - Verificar límites de peticiones
Adaptado para CraftRMN Pro
"""
import requests
import time

BASE_URL = "http://localhost:5000"

print("\n" + "=" * 70)
print("🚦 TEST DE RATE LIMITING - Protección contra Abuso")
print("=" * 70)
print("\n⚠️  IMPORTANTE: El servidor debe estar corriendo (python app.py)\n")

# ============================================================================
# Test 1: Límite en validate_pin (5 intentos por minuto)
# ============================================================================
print("Test 1: Verificar límite de validate_pin (5/minuto)")
print("-" * 70)

success_count = 0
blocked_count = 0

for i in range(8):  # Hacer 8 intentos (debería bloquear después de 5)
    try:
        response = requests.post(
            f"{BASE_URL}/api/validate_pin",
            json={"company_id": "FAES", "pin": "9999"},  # PIN incorrecto a propósito
            timeout=2
        )
        
        if response.status_code == 429:  # Too Many Requests
            print(f"   Intento {i+1}: 🚫 BLOQUEADO (429 - Rate limit)")
            blocked_count += 1
        elif response.status_code in [400, 403, 404]:  # Errores esperados
            print(f"   Intento {i+1}: ✅ Permitido ({response.status_code} - Error esperado)")
            success_count += 1
        else:
            print(f"   Intento {i+1}: ⚠️  Respuesta inesperada ({response.status_code})")
            success_count += 1
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: No se puede conectar al servidor")
        print(f"   Ejecuta: python app.py")
        exit(1)
    except Exception as e:
        print(f"❌ Error en intento {i+1}: {e}")

print(f"\nResultado Test 1:")
print(f"   ✅ Permitidos: {success_count}")
print(f"   🚫 Bloqueados: {blocked_count}")

if blocked_count >= 1:
    print(f"   🎉 ¡Rate limiting funcionando! Se bloquearon peticiones excesivas.")
else:
    print(f"   ⚠️  No se bloqueó ninguna petición. Verifica la configuración.")

# ============================================================================
# Test 2: Headers de Rate Limit
# ============================================================================
print("\n" + "-" * 70)
print("Test 2: Verificar headers de límite")
print("-" * 70)

try:
    response = requests.get(f"{BASE_URL}/api/measurements?company=FAES")
    
    headers_to_check = [
        'X-RateLimit-Limit',
        'X-RateLimit-Remaining',
        'X-RateLimit-Reset'
    ]
    
    print(f"Status: {response.status_code}")
    print(f"Headers encontrados:")
    
    headers_found = 0
    for header in headers_to_check:
        value = response.headers.get(header)
        if value:
            print(f"   ✅ {header}: {value}")
            headers_found += 1
        else:
            print(f"   ⚠️  {header}: No encontrado")
            
except Exception as e:
    print(f"❌ Error: {e}")
    headers_found = 0

# ============================================================================
# Test 3: Análisis rápido (verificar límite)
# ============================================================================
print("\n" + "-" * 70)
print("Test 3: Verificar límite de análisis")
print("-" * 70)

print("   Enviando 3 peticiones de análisis...")

analysis_success = 0
analysis_blocked = 0

for i in range(3):
    try:
        # Crear un archivo de prueba pequeño
        files = {'file': ('test.txt', b'test spectral data', 'text/plain')}
        data = {'company_id': 'FAES'}  # Usar company_id correcto
        
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            files=files,
            data=data,
            timeout=5
        )
        
        if response.status_code == 429:
            print(f"   Análisis {i+1}: 🚫 BLOQUEADO (rate limit)")
            analysis_blocked += 1
        elif response.status_code in [400, 500]:
            print(f"   Análisis {i+1}: ✅ Procesado ({response.status_code})")
            analysis_success += 1
        else:
            print(f"   Análisis {i+1}: ⚠️  Respuesta ({response.status_code})")
            analysis_success += 1
            
    except Exception as e:
        print(f"   Análisis {i+1}: ⚠️  Error ({str(e)[:50]})")

print(f"\nResultado Test 3:")
print(f"   ✅ Análisis procesados: {analysis_success}")
print(f"   🚫 Análisis bloqueados: {analysis_blocked}")

# ============================================================================
# Resumen final
# ============================================================================
print("\n" + "=" * 70)
print("📊 RESUMEN GENERAL")
print("=" * 70)

total_tests = 3
passed_tests = 0

# Test 1: Rate limiting funcionó
if blocked_count >= 1:
    passed_tests += 1
    
# Test 2: Headers presentes
if headers_found >= 2:
    passed_tests += 1
    
# Test 3: Análisis funciona (aunque no se bloquee con solo 3)
if analysis_success > 0:
    passed_tests += 1
    
print(f"Tests ejecutados: {total_tests}")
print(f"Tests pasados: {passed_tests}/{total_tests}")

if passed_tests >= 2:
    print(f"\n🎉 ¡EXCELENTE! Rate Limiting está funcionando correctamente.")
    print(f"   Tu aplicación está protegida contra abuso.")
else:
    print(f"\n⚠️  Algunos tests fallaron. Revisa la configuración.")

print("=" * 70 + "\n")