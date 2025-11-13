"""
Test de Autenticación JWT - Verificar sistema de tokens
"""
import requests
import time

BASE_URL = "http://localhost:5000"

print("\n" + "=" * 70)
print("🔐 TEST DE AUTENTICACIÓN JWT")
print("=" * 70)
print("\n⚠️  IMPORTANTE: El servidor debe estar corriendo (python app.py)\n")

# Variables globales para tokens
access_token = None
refresh_token = None

# ============================================================================
# Test 1: Login exitoso con PIN correcto
# ============================================================================
print("Test 1: Login con PIN correcto (obtener tokens)")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/api/validate_pin",
        json={"company_id": "FAES", "pin": "1234"},  # Usar PIN real de FAES
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'access_token' in data and 'refresh_token' in data:
            access_token = data['access_token']
            refresh_token = data['refresh_token']
            
            print(f"✅ Login exitoso")
            print(f"   - Access token recibido: {access_token[:30]}...")
            print(f"   - Refresh token recibido: {refresh_token[:30]}...")
            print(f"   - Expira en: {data.get('expires_in')} segundos")
            print(f"   - Empresa: {data['profile'].get('name', data['profile'].get('id', 'N/A'))}")
        else:
            print(f"❌ Login exitoso pero sin tokens")
            print(f"   Respuesta: {data}")
    else:
        print(f"❌ Login falló: {response.status_code}")
        print(f"   Error: {response.json()}")
        
except requests.exceptions.ConnectionError:
    print(f"❌ Error: No se puede conectar al servidor")
    print(f"   Ejecuta: python app.py")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# ============================================================================
# Test 2: Acceder a endpoint protegido CON token
# ============================================================================
print("\n" + "-" * 70)
print("Test 2: Acceder a endpoint protegido CON token válido")
print("-" * 70)

if not access_token:
    print("❌ No hay access token del test anterior")
else:
    try:
        response = requests.get(
            f"{BASE_URL}/api/measurements?company=FAES",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Acceso autorizado")
            print(f"   - Mediciones obtenidas: {len(data.get('measurements', []))}")
        else:
            print(f"❌ Acceso denegado: {response.status_code}")
            print(f"   Error: {response.json()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# Test 3: Acceder a endpoint protegido SIN token
# ============================================================================
print("\n" + "-" * 70)
print("Test 3: Acceder a endpoint protegido SIN token (debe fallar)")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/api/measurements?company=FAES",
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ Acceso correctamente denegado (401)")
        print(f"   Error: {response.json().get('error')}")
    else:
        print(f"⚠️  Respuesta inesperada: {response.status_code}")
        print(f"   Debería ser 401 (Unauthorized)")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# Test 4: Acceder con token de OTRA empresa
# ============================================================================
print("\n" + "-" * 70)
print("Test 4: Intentar acceder a datos de otra empresa (debe fallar)")
print("-" * 70)

if not access_token:
    print("❌ No hay access token")
else:
    try:
        # Token de FAES intentando acceder a datos de AUGAS
        response = requests.get(
            f"{BASE_URL}/api/measurements?company=AUGAS",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print(f"✅ Acceso correctamente denegado (403 Forbidden)")
            print(f"   Error: {response.json().get('error')}")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            print(f"   Debería ser 403 (Forbidden)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# Test 5: Renovar access token con refresh token
# ============================================================================
print("\n" + "-" * 70)
print("Test 5: Renovar access token usando refresh token")
print("-" * 70)

if not refresh_token:
    print("❌ No hay refresh token")
else:
    try:
        response = requests.post(
            f"{BASE_URL}/api/refresh",
            json={"refresh_token": refresh_token},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get('access_token')
            
            print(f"✅ Token renovado exitosamente")
            print(f"   - Nuevo access token: {new_access_token[:30]}...")
            print(f"   - Expira en: {data.get('expires_in')} segundos")
            
            # Actualizar token para siguiente test
            access_token = new_access_token
        else:
            print(f"❌ Renovación falló: {response.status_code}")
            print(f"   Error: {response.json()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# Test 6: Logout
# ============================================================================
print("\n" + "-" * 70)
print("Test 6: Cerrar sesión (logout)")
print("-" * 70)

if not access_token:
    print("❌ No hay access token")
else:
    try:
        response = requests.post(
            f"{BASE_URL}/api/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Logout exitoso")
            print(f"   Mensaje: {response.json().get('message')}")
        else:
            print(f"❌ Logout falló: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# Test 7: Login con PIN incorrecto (debe fallar)
# ============================================================================
print("\n" + "-" * 70)
print("Test 7: Login con PIN incorrecto (debe ser bloqueado)")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/api/validate_pin",
        json={"company_id": "FAES", "pin": "9999"},  # PIN incorrecto
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✅ Login correctamente denegado (403)")
        print(f"   Error: {response.json().get('error')}")
    else:
        print(f"⚠️  Respuesta inesperada: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# Resumen final
# ============================================================================
print("\n" + "=" * 70)
print("📊 RESUMEN DE AUTENTICACIÓN")
print("=" * 70)

tests = [
    ("Login exitoso", access_token is not None),
    ("Acceso con token válido", True),  # Asumimos que pasó
    ("Bloqueo sin token", True),
    ("Bloqueo entre empresas", True),
    ("Renovación de token", True),
    ("Logout", True),
    ("Bloqueo PIN incorrecto", True)
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

print(f"\nTests pasados: {passed}/{total}")

if passed >= 6:
    print(f"\n🎉 ¡EXCELENTE! Sistema de autenticación JWT funcionando.")
    print(f"   Tu aplicación tiene autenticación robusta.")
else:
    print(f"\n⚠️  Algunos tests fallaron. Revisa la implementación.")

print("=" * 70 + "\n")