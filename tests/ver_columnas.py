import sys
from pathlib import Path

# Agrega el directorio raíz del proyecto al sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

print("🧩 Ruta raíz añadida a sys.path:", ROOT_DIR)

# Importa desde backend
from backend.database import get_db

# Ahora sí, prueba con la medición
db = get_db()
measurement = db.get_measurement(measurement_id=162)
print(measurement['analysis'])
