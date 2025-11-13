"""
Test de Path Traversal - Verificar que los ataques son bloqueados
"""
import requests

BASE_URL = "http://localhost:5000"

# Intentos de ataque que DEBEN ser bloqueados
malicious_attempts = [
    "../../../.env",
    "..\\..\\..\\config_manager.py",
    "....//....//etc/passwd",
    "../storage/measurements.db",
    "test;rm -rf /",
    "archivo|cat /etc/passwd",
    "file`whoami`.txt",
    "/etc/passwd",
    "~/.ssh/id_rsa",
    "file\x00.txt",
]

print("\n" + "=" * 70)
print("🔒 TEST DE PATH TRAVERSAL - Verificación de Seguridad")
print("=" * 70)
print("\n⚠️  IMPORTANTE: El servidor debe estar corriendo (python app.py)\n")

blocked = 0
failed = 0

for i, attempt in enumerate(malicious_attempts, 1):
    try:
        response = requests.get(
            f"{BASE_URL}/api/download/{attempt}",
            timeout=2
        )
        
        if response.status_code in [400, 403, 404]:
            print(f"✅ Test {i:2d}/10: BLOQUEADO - {attempt[:40]}")
            blocked += 1
        elif response.status_code == 200:
            print(f"🔴 Test {i:2d}/10: ¡VULNERABLE! - {attempt[:40]}")
            print(f"    ⚠️ El servidor permitió acceso a: {attempt}")
            failed += 1
        else:
            print(f"⚠️  Test {i:2d}/10: Respuesta inesperada ({response.status_code})")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: No se puede conectar al servidor")
        print(f"   Ejecuta: python app.py")
        break
    except Exception as e:
        print(f"❌ Test {i:2d}/10: Error - {e}")

print("\n" + "=" * 70)
print(f"📊 RESULTADOS:")
print(f"   ✅ Ataques bloqueados: {blocked}/10")
print(f"   🔴 Vulnerabilidades: {failed}/10")

if failed == 0:
    print(f"\n🎉 ¡EXCELENTE! Todos los ataques fueron bloqueados.")
    print(f"   Tu aplicación está protegida contra Path Traversal.")
else:
    print(f"\n⚠️  ATENCIÓN: Se detectaron {failed} vulnerabilidades.")
    print(f"   Revisa la implementación de download_input_file()")

print("=" * 70 + "\n")