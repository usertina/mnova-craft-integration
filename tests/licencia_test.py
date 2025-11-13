import os
from dotenv import load_dotenv


# Cargar .env
load_dotenv()

# Verificar claves
print("=" * 60)
print("VERIFICACIÓN DE .ENV")
print("=" * 60)
print(f"FLASK_SECRET_KEY: {'✅ SÍ' if os.getenv('FLASK_SECRET_KEY') else '❌ NO'}")
print(f"CRAFTRMN_MASTER_KEY: {'✅ SÍ' if os.getenv('CRAFTRMN_MASTER_KEY') else '❌ NO'}")
print(f"JWT_SECRET_KEY: {'✅ SÍ' if os.getenv('JWT_SECRET_KEY') else '❌ NO'}")
print(f"PASSWORD_SALT: {'✅ SÍ' if os.getenv('PASSWORD_SALT') else '❌ NO'}")

# Mostrar primeros caracteres
key = os.getenv('CRAFTRMN_MASTER_KEY')
if key:
    print(f"\nCRAFTRMN_MASTER_KEY: {key[:10]}... ({len(key)} caracteres)")

print("=" * 60)

# Ahora probar config_manager
print("\nPROBANDO CONFIG_MANAGER:")
print("=" * 60)

from config_manager import LicenseValidator

try:
    validator = LicenseValidator()
    print("✅ SUCCESS: License validator funciona correctamente")
    print("   La clave se cargó desde .env")
except Exception as e:
    print(f"❌ ERROR: {e}")

exit()