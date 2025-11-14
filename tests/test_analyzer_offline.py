#!/usr/bin/env python3
"""
Test Unitario del Analyzer (Offline)
=====================================
Verifica que el SpectrumAnalyzer:
1. Se importa correctamente.
2. Analiza un archivo CSV.
3. Devuelve la estructura de datos (JSON) completa.

Ejecutar desde la carpeta 'tests' o la raíz del proyecto.
"""

import sys
from pathlib import Path
import json

# --- Configuración de Rutas ---
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
WORKER_DIR = ROOT_DIR / "worker"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKER_DIR))

print("="*80)
print("🧪 TEST UNITARIO: SpectrumAnalyzer (Offline)")
print("="*80)
print(f"📂 Raíz del proyecto: {ROOT_DIR}")

# ----------------------------------------------------------------------
# IMPORTAR ANALYZER
# ----------------------------------------------------------------------
try:
    print("\n📦 Importando SpectrumAnalyzer desde 'worker'...")
    from analyzer import SpectrumAnalyzer
    print("✅ SpectrumAnalyzer importado correctamente")
except ImportError as e:
    print(f"❌ Error importando analyzer: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# INICIALIZAR Y ANALIZAR
# ----------------------------------------------------------------------
analyzer = SpectrumAnalyzer(spectrometer_h1_freq_mhz=500.0)
print("✅ Analyzer inicializado")

print("\n🔍 Buscando archivo CSV de prueba en 'backend/storage/output'...")
output_dir = BACKEND_DIR / "storage" / "output"
csv_files = sorted(output_dir.glob("*.csv"))

if not csv_files:
    print(f"❌ No se encontró ningún archivo CSV en {output_dir}")
    sys.exit(1)

test_file = csv_files[0]
print(f"✅ Usando archivo: {test_file.name}\n")

print(f"📊 Analizando {test_file.name}...")
try:
    results = analyzer.analyze_file(
        test_file,
        concentration=1.0,
        baseline_correction=True,
    )
    print("✅ Análisis completado")
except Exception as e:
    print(f"❌ Error durante el análisis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ----------------------------------------------------------------------
# VERIFICACIÓN DE CAMPOS (Fusionado de test_analysis_structure.py)
# ----------------------------------------------------------------------
print("\n" + "="*80)
print("📋 VERIFICACIÓN DE ESTRUCTURA DE DATOS (JSON)")
print("="*80)

required_fields = [
    'spectrum', 'file_name', 'filename', 'concentration', 'sample_concentration',
    'peaks', 'peaks_count', 'quality_metrics', 'signal_to_noise', 'snr',
    'fluor_total', 'fluor_percentage', 'fluor_area', 'pifas', 'pifas_percentage',
    'pfas_percentage', 'pifas_area', 'pfas_area', 'pifas_concentration',
    'pfas_concentration', 'total_integral', 'baseline_corrected', 'baseline_value',
    'spectrometer_config', 'pfas_detection', 'quality_score', 'quality_breakdown'
]    

present = []
missing = []

if not isinstance(results, dict):
    print(f"❌ ERROR: El resultado no es un diccionario, es: {type(results).__name__}")
    sys.exit(1)

print("✅ El resultado es un diccionario.")
for field in required_fields:
    if field in results:
        present.append(field)
    else:
        missing.append(field)

print(f"\nCampos presentes: {len(present)}/{len(required_fields)}")

if missing:
    print(f"\n❌ CAMPOS FALTANTES ({len(missing)}):")
    for field in missing:
        print(f"   - {field}")
else:
    print("✅ ¡Perfecto! Todos los campos requeridos están presentes.")
    
# ----------------------------------------------------------------------
# REVISIÓN DE DATOS (Fusionado de revisar_analyzer_output.py)
# ----------------------------------------------------------------------
print("\n" + "="*80)
print("📦 RESUMEN DEL JSON DEVUELTO (primeros 3000 caracteres):")
print("="*80)
print(json.dumps(results, indent=2, ensure_ascii=False, default=str)[:3000])
print("...")

output_json = CURRENT_DIR / "analysis_example.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print(f"\n💾 Resultado completo guardado en: {output_json}")

print("\n" + "="*80)
if missing:
    print("⚠️  RESULTADO: PARCIAL - Faltan campos clave en el analizador.")
else:
    print("✅ RESULTADO: ÉXITO - El analizador funciona y devuelve la estructura completa.")
print("="*80)