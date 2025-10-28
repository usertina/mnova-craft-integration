"""
Script de utilidad para generar la licencia de ADMINISTRADOR
del dispositivo.
"""
from config_manager import get_config_manager, LicenseValidator
from database import get_db
import logging
import sys

# Activar logs para ver el hash_input
logging.getLogger().setLevel(logging.DEBUG)

print("Iniciando generador de licencia de ADMIN...")

# 1. Cargar la configuración y la base de datos
try:
    db = get_db()
    config = get_config_manager()
except Exception as e:
    print(f"\n❌ Error: No se pudo cargar la base de datos.")
    print(f"Asegúrate de que 'storage/measurements.db' existe.")
    print(f"Si no existe, ejecuta 'python backend/app.py' una vez para crearla.")
    sys.exit(1)


# 2. Obtener el Device ID real de la base de datos
device_id = config.get_device_id()
if not device_id or device_id == "unknown":
    print("❌ Error: No se pudo encontrar un device_id en la base de datos.")
    sys.exit(1)

print(f"Device ID encontrado en la BD: {device_id}\n")
print(f"Generando licencia de ADMINISTRADOR para este dispositivo...")

# 3. Generar la licencia de ADMIN
validator = LicenseValidator()
license_key = validator.generate_admin_license(
    device_id=device_id
)

print("\n" + "="*50)
print("  ¡LICENCIA DE ADMIN GENERADA CON ÉXITO!")
print("  Usa esta clave para activar el dispositivo llamando a /api/activate:\n")
print(f"  {license_key}")
print("="*50 + "\n")

