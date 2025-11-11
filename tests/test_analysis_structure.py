#!/usr/bin/env python3
"""
Test para verificar estructura de análisis
Ejecutar desde la raíz del proyecto
"""

import sys
from pathlib import Path
import json

# Agregar paths
sys.path.insert(0, str(Path('backend')))
sys.path.insert(0, str(Path('worker')))

print("="*80)
print("🧪 TEST DE ESTRUCTURA DE ANÁLISIS")
print("="*80)

try:
    print("\n📦 Importando módulos...")
    from analyzer import SpectrumAnalyzer
    print("✅ SpectrumAnalyzer importado")
except ImportError as e:
    print(f"❌ Error importando analyzer: {e}")
    print("\nVerifica que:")
    print("  - worker/analyzer.py existe")
    print("  - backend/pfas_detector_enhanced.py existe")
    print("  - backend/nmr_constants.py existe")
    sys.exit(1)

# Crear analyzer
print("\n🔧 Inicializando analyzer...")
try:
    analyzer = SpectrumAnalyzer(spectrometer_h1_freq_mhz=500.0)
    print("✅ Analyzer inicializado correctamente")
except Exception as e:
    print(f"❌ Error inicializando analyzer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Buscar archivo de ejemplo
print("\n🔍 Buscando archivo de prueba...")
possible_files = [
    Path('backend/storage/output/CSV PFOA 1.csv'),
    Path('backend/storage/output/CSV PFOA 2.csv'),
    Path('backend/storage/output/CSV PFOA 3.csv'),
    Path('backend/storage/output/MZ0031_PFOS.csv')
]

test_file = None
for f in possible_files:
    if f.exists():
        test_file = f
        print(f"✅ Encontrado: {f}")
        break

if not test_file:
    print("❌ No se encontró ningún archivo de prueba en:")
    for f in possible_files:
        print(f"   - {f}")
    print("\nColoca un archivo CSV en backend/storage/output/")
    sys.exit(1)

# Analizar
print(f"\n📊 Analizando {test_file.name}...")
print("-"*80)

try:
    results = analyzer.analyze_file(
        test_file,
        concentration=1.0,
        baseline_correction=True,
        baseline_method='polynomial'
    )
    print("✅ Análisis completado")
except Exception as e:
    print(f"❌ Error durante el análisis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verificar estructura
print("\n" + "="*80)
print("📋 VERIFICACIÓN DE CAMPOS REQUERIDOS")
print("="*80)

required_fields = {
    'file_name': 'Nombre del archivo',
    'concentration': 'Concentración de muestra',
    'fluor_total': 'Flúor total',
    'pifas': 'PFAS/PIFAS',
    'peaks': 'Picos detectados',
    'quality_metrics': 'Métricas de calidad',
    'pfas_detection': 'Detección de PFAS',
    'quality_score': 'Score de calidad',
    'quality_breakdown': 'Desglose de calidad',
    'baseline_corrected': 'Baseline corregido',
    'baseline_value': 'Valor de baseline',
    'spectrometer_config': 'Configuración del espectrómetro'
}

present = []
missing = []

for field, description in required_fields.items():
    if field in results:
        present.append(field)
        status = "✅"
    else:
        missing.append(field)
        status = "❌"
    
    print(f"{status} {field}: {description}")

# Mostrar detalles de campos importantes
print("\n" + "="*80)
print("📊 DETALLES DE CAMPOS PRESENTES")
print("="*80)

if 'fluor_total' in results:
    ft = results['fluor_total']
    print(f"\n💧 FLÚOR TOTAL:")
    print(f"   Área: {ft.get('total_area', 'N/A'):.2e}")
    print(f"   Porcentaje: {ft.get('percentage', 'N/A'):.2f}%")
    print(f"   Intensidad máxima: {ft.get('max_intensity', 'N/A'):.2e}")

if 'pifas' in results:
    pf = results['pifas']
    print(f"\n🧪 PFAS/PIFAS:")
    print(f"   Área: {pf.get('total_area', 'N/A'):.2e}")
    print(f"   Porcentaje: {pf.get('percentage', 'N/A'):.2f}%")
    print(f"   Intensidad máxima: {pf.get('max_intensity', 'N/A'):.2e}")

if 'peaks' in results:
    peaks = results['peaks']
    print(f"\n📍 PICOS DETECTADOS: {len(peaks)}")
    if peaks:
        print(f"   Primeros 3 picos:")
        for i, p in enumerate(peaks[:3], 1):
            print(f"   {i}. ppm: {p.get('ppm', 'N/A'):.2f}, "
                  f"intensity: {p.get('intensity', 'N/A'):.2e}, "
                  f"width_hz: {p.get('width_hz', 'N/A'):.1f}, "
                  f"snr: {p.get('snr', 'N/A'):.1f}")

if 'quality_metrics' in results:
    qm = results['quality_metrics']
    print(f"\n📈 CALIDAD:")
    print(f"   SNR: {qm.get('snr', 'N/A'):.1f}")
    print(f"   Nivel de ruido: {qm.get('noise_level', 'N/A'):.2e}")
    print(f"   Señal máxima: {qm.get('max_signal', 'N/A'):.2e}")

if 'pfas_detection' in results:
    pd = results['pfas_detection']
    print(f"\n🔬 DETECCIÓN DE PFAS:")
    print(f"   Total detectados: {pd.get('total_detected', 0)}")
    print(f"   Confianza promedio: {pd.get('confidence', 0)*100:.1f}%")
    
    if pd.get('detected_pfas'):
        print(f"   Compuestos detectados:")
        for pfas in pd['detected_pfas'][:5]:
            print(f"   • {pfas.get('name', 'N/A')}: {pfas.get('confidence', 0)*100:.1f}% "
                  f"({pfas.get('peaks_matched', 0)}/{pfas.get('peaks_expected', 0)} picos)")
    
    if pd.get('spectrometer_info'):
        si = pd['spectrometer_info']
        print(f"\n   Espectrómetro:")
        print(f"   • Frecuencia 19F: {si.get('frequency_mhz', 'N/A'):.1f} MHz")
        print(f"   • Tolerancia: {si.get('tolerance_ppm', 'N/A'):.4f} ppm "
              f"(~{si.get('tolerance_hz', 'N/A'):.1f} Hz)")

if 'quality_score' in results:
    print(f"\n⭐ SCORE DE CALIDAD: {results['quality_score']:.1f}/100")
    
    if 'quality_breakdown' in results:
        qb = results['quality_breakdown']
        print(f"   Desglose:")
        print(f"   • SNR: {qb.get('snr', 0):.1f}/100")
        print(f"   • Baseline: {qb.get('baseline', 0):.1f}/100")
        print(f"   • Picos: {qb.get('peaks', 0):.1f}/100")
        print(f"   • Resolución: {qb.get('resolution', 0):.1f}/100")

if 'spectrometer_config' in results:
    sc = results['spectrometer_config']
    print(f"\n🧲 CONFIGURACIÓN ESPECTRÓMETRO:")
    print(f"   1H: {sc.get('h1_frequency_mhz', 'N/A'):.1f} MHz")
    print(f"   19F: {sc.get('f19_frequency_mhz', 'N/A'):.1f} MHz")

# Resumen final
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

# Guardar JSON de ejemplo
output_file = Path('analysis_example.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
print(f"\n💾 Estructura completa guardada en: {output_file}")

# Veredicto
print("\n" + "="*80)
if n_present == total:
    print("✅ RESULTADO: PERFECTO - Todos los campos presentes")
    print("="*80)
    print("""
El analyzer está retornando todos los campos requeridos.
Si el frontend no muestra los datos, el problema está en:
  1. Cómo se guardan en la base de datos (app.py)
  2. Cómo se leen desde la API (endpoint /api/measurements)
  3. Cómo se muestran en el frontend (chartManager.js, uiComponents.js)

Próximos pasos:
  1. Hacer un nuevo análisis desde el frontend
  2. Verificar en la consola del navegador (F12) qué datos llegan
  3. Verificar con diagnostico_datos.py qué se guardó en la BD
""")
elif n_present >= total * 0.8:
    print("⚠️ RESULTADO: CASI COMPLETO - Faltan algunos campos")
    print("="*80)
    print(f"""
El analyzer está retornando {n_present}/{total} campos.
Faltan {n_missing} campos opcionales.

Esto puede ser suficiente si los campos faltantes son opcionales.
Revisa la lista arriba para ver cuáles faltan.
""")
else:
    print("❌ RESULTADO: INCOMPLETO - Faltan muchos campos críticos")
    print("="*80)
    print(f"""
El analyzer solo está retornando {n_present}/{total} campos.

CAUSA PROBABLE:
  - El analyzer.py no es la versión corregida
  - O hay un error durante el análisis que lo interrumpe

SOLUCIÓN:
  1. Verificar que worker/analyzer.py es la versión corregida
  2. Limpiar caché: Get-ChildItem -Recurse *.pyc | Remove-Item -Force
  3. Reiniciar Flask
  4. Ejecutar este script de nuevo
""")

print("="*80)