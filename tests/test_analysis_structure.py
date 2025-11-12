#!/usr/bin/env python3
"""
Test para verificar estructura de análisis
Ejecutar desde la carpeta tests o desde la raíz del proyecto.
"""

import sys
from pathlib import Path
import json

# Detectar ruta raíz automáticamente (funciona incluso si se ejecuta desde /tests)
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
WORKER_DIR = ROOT_DIR / "worker"

# Agregar paths al sys.path
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKER_DIR))

print("="*80)
print("🧪 TEST DE ESTRUCTURA DE ANÁLISIS")
print("="*80)
print(f"📂 Ruta raíz detectada: {ROOT_DIR}")
print(f"📂 Ruta backend: {BACKEND_DIR}")
print(f"📂 Ruta worker: {WORKER_DIR}\n")

# ----------------------------------------------------------------------
# IMPORTAR ANALYZER
# ----------------------------------------------------------------------
try:
    print("📦 Importando módulos...")
    from analyzer import SpectrumAnalyzer
    print("✅ SpectrumAnalyzer importado correctamente")
except ImportError as e:
    print(f"❌ Error importando analyzer: {e}")
    print("\nVerifica que existen los archivos:")
    print("  - worker/analyzer.py")
    print("  - backend/pfas_detector_enhanced.py")
    print("  - backend/nmr_constants.py")
    sys.exit(1)

# ----------------------------------------------------------------------
# INICIALIZAR ANALYZER
# ----------------------------------------------------------------------
print("\n🔧 Inicializando analyzer...")
try:
    analyzer = SpectrumAnalyzer(spectrometer_h1_freq_mhz=500.0)
    print("✅ Analyzer inicializado correctamente")
except Exception as e:
    print(f"❌ Error inicializando analyzer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ----------------------------------------------------------------------
# BUSCAR ARCHIVO DE PRUEBA AUTOMÁTICAMENTE
# ----------------------------------------------------------------------
print("\n🔍 Buscando archivo CSV de prueba...")

output_dir = BACKEND_DIR / "storage" / "output"
csv_files = sorted(output_dir.glob("*.csv"))

if not csv_files:
    print(f"❌ No se encontró ningún archivo CSV en {output_dir}")
    print("Por favor, coloca un archivo CSV en esa carpeta y vuelve a ejecutar.")
    sys.exit(1)

test_file = csv_files[0]
print(f"✅ Archivo de prueba detectado: {test_file.name}\n")

# ----------------------------------------------------------------------
# ANALIZAR ARCHIVO
# ----------------------------------------------------------------------
print(f"📊 Analizando archivo: {test_file.name}")
print("-"*80)

try:
    results = analyzer.analyze_file(
        test_file,
        concentration=1.0,
        baseline_correction=True,
        baseline_method='polynomial'
    )
    print("✅ Análisis completado correctamente")
except Exception as e:
    print(f"❌ Error durante el análisis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ----------------------------------------------------------------------
# VERIFICACIÓN DE CAMPOS
# ----------------------------------------------------------------------
print("\n" + "="*80)
print("📋 VERIFICACIÓN DE CAMPOS REQUERIDOS")
print("="*80)

required_fields = {
    'spectrum': 'Datos espectrales',
    'file_name': 'Nombre del archivo (principal)',
    'filename': 'Nombre del archivo (alternativo)',
    'concentration': 'Concentración nominal',
    'sample_concentration': 'Concentración de muestra',
    'peaks': 'Picos detectados',
    'peaks_count': 'Número de picos',
    'quality_metrics': 'Métricas de calidad',
    'signal_to_noise': 'Relación señal/ruido (S/N)',
    'snr': 'SNR duplicado (validación)',
    'fluor_total': 'Datos de flúor total',
    'fluor_percentage': 'Porcentaje de flúor total',
    'fluor_area': 'Área de flúor total',
    'pifas': 'Datos de PIFAS',
    'pifas_percentage': 'Porcentaje PIFAS',
    'pfas_percentage': 'Porcentaje PFAS',
    'pifas_area': 'Área PIFAS',
    'pfas_area': 'Área PFAS',
    'pifas_concentration': 'Concentración PIFAS',
    'pfas_concentration': 'Concentración PFAS',
    'total_integral': 'Integral total',
    'baseline_corrected': 'Baseline corregido',
    'baseline_value': 'Valor del baseline',
    'spectrometer_config': 'Configuración del espectrómetro',
    'pfas_detection': 'Detección de PFAS',
    'quality_score': 'Score de calidad global',
    'quality_breakdown': 'Desglose de calidad'
}    

present = []
missing = []

for field, description in required_fields.items():
    if field in results:
        present.append(field)
        print(f"✅ {field}: {description}")
    else:
        missing.append(field)
        print(f"❌ {field}: {description}")

# ----------------------------------------------------------------------
# GUARDAR RESULTADOS
# ----------------------------------------------------------------------
output_json = CURRENT_DIR / "analysis_example.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

# ----------------------------------------------------------------------
# RESUMEN FINAL
# ----------------------------------------------------------------------
print("\n" + "="*80)
print("📊 RESUMEN FINAL")
print("="*80)

total = len(required_fields)
n_present = len(present)
n_missing = len(missing)
print(f"\n✅ Campos presentes: {n_present}/{total} ({n_present/total*100:.1f}%)")

if missing:
    print(f"\n❌ Campos faltantes ({n_missing}):")
    for field in missing:
        print(f"   - {field}: {required_fields[field]}")

print(f"\n💾 Resultado completo guardado en: {output_json}")

print("\n" + "="*80)
if n_present == total:
    print("✅ RESULTADO: PERFECTO - Todos los campos presentes")
else:
    print("⚠️ RESULTADO: PARCIAL - Faltan algunos campos")
print("="*80)
