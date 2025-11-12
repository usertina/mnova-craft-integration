"""
diagnostico_datos.py - Diagnóstico completo de mediciones en la base de datos
Versión corregida para usar la estructura completa de raw_data['analysis']
"""
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

print("🧩 Ruta raíz añadida a sys.path:", ROOT_DIR)

from backend.database import get_db



# Lista de campos esperados en cada análisis
EXPECTED_FIELDS = [
    "file_name",
    "concentration",
    "fluor_total",
    "pifas",
    "pfas_detection",
    "baseline_corrected",
    "spectrometer_config",
    "peaks",
    "quality_metrics",
    "fluor_percentage",
    "pifas_percentage",
    "pifas_concentration",
]

def diagnostico():
    db = get_db()
    
    # Obtener todas las mediciones
    data = db.get_measurements(company_id="admin", limit=1000)
    measurements = data.get("measurements", [])
    
    if not measurements:
        print("No se encontraron mediciones en la base de datos.")
        return
    
    for m in measurements:
        print("="*60)
        print(f"ID: {m['id']} | Empresa: {m['company_id']} | Archivo: {m['filename']}")
        
        analysis = m.get("analysis", {})
        missing_fields = [f for f in EXPECTED_FIELDS if f not in analysis]
        
        if missing_fields:
            print(f"⚠ Campos faltantes en analysis: {missing_fields}")
        else:
            print("✅ Todos los campos esperados presentes en analysis.")
        
        # Resumen rápido de valores
        print(f"   Fluor %: {analysis.get('fluor_percentage')}")
        print(f"   PFAS %: {analysis.get('pifas_percentage')}")
        print(f"   PFAS Concentration: {analysis.get('pifas_concentration')}")
        print(f"   Concentration: {analysis.get('concentration')}")
        print(f"   Peaks detectados: {len(analysis.get('peaks', []))}")
        pfas_detected = analysis.get('pfas_detection', {}).get('total_detected', 0)
        print(f"   PFAS detectados: {pfas_detected}")
    
    print("="*60)
    print(f"Total de mediciones analizadas: {len(measurements)}")


if __name__ == "__main__":
    diagnostico()
