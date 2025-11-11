#!/usr/bin/env python3
"""
Muestra lo que devolvió el analyzer en el test
"""

import json
from pathlib import Path

print("="*80)
print("🔍 REVISANDO QUÉ DEVOLVIÓ EL ANALYZER")
print("="*80)

json_file = Path('analysis_example.json')

if not json_file.exists():
    print(f"\n❌ No se encontró {json_file}")
    print("Ejecuta primero: python test_analysis_structure.py")
    exit(1)

print(f"\n📄 Leyendo {json_file}...")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n" + "="*80)
print("📦 CONTENIDO DEVUELTO POR EL ANALYZER:")
print("="*80)

print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])

print("\n" + "="*80)
print("📊 ESTRUCTURA:")
print("="*80)

if isinstance(data, dict):
    print(f"\n✅ Es un diccionario con {len(data)} campos:")
    for key in data.keys():
        value = data[key]
        if isinstance(value, dict):
            print(f"  • {key}: dict con {len(value)} campos")
        elif isinstance(value, list):
            print(f"  • {key}: lista con {len(value)} items")
        else:
            print(f"  • {key}: {type(value).__name__}")
    
    # Verificar campos críticos
    print("\n📋 Verificación de campos críticos:")
    critical_fields = ['file_name', 'peaks', 'pfas_detection', 'fluor_total', 'pifas']
    for field in critical_fields:
        if field in data:
            print(f"  ✅ {field}: presente")
        else:
            print(f"  ❌ {field}: FALTA")
else:
    print(f"\n❌ NO es un diccionario, es: {type(data).__name__}")
    print(f"Contenido: {str(data)[:500]}")

print("\n" + "="*80)
print("🔧 DIAGNÓSTICO:")
print("="*80)

if not data or (isinstance(data, dict) and len(data) == 0):
    print("""
❌ EL ANALYZER ESTÁ DEVOLVIENDO UN OBJETO VACÍO

CAUSA PROBABLE:
1. El método analyze_file() no está retornando nada (return None implícito)
2. O está retornando {} vacío
3. O hay una excepción que se está tragando silenciosamente

SOLUCIÓN:
1. Abre worker/analyzer.py
2. Busca el método analyze_file()
3. Verifica que al final tenga un return con todos los campos
4. Verifica que no haya un try-except que trague excepciones

EJEMPLO DE CÓMO DEBE SER EL FINAL DE analyze_file():

    return {
        'file_name': filename,
        'concentration': concentration,
        'fluor_total': fluor_data,
        'pifas': pifas_data,
        'peaks': peaks_list,
        'quality_metrics': quality_metrics,
        'pfas_detection': pfas_detection,
        'quality_score': quality_score,
        'quality_breakdown': quality_breakdown,
        'baseline_corrected': baseline_corrected,
        'baseline_value': baseline_value,
        'spectrometer_config': spectrometer_config
    }
""")
elif isinstance(data, dict) and len(data) > 0:
    missing = []
    critical = ['file_name', 'peaks', 'pfas_detection', 'fluor_total', 'pifas']
    for field in critical:
        if field not in data:
            missing.append(field)
    
    if missing:
        print(f"""
⚠️ EL ANALYZER DEVUELVE ALGUNOS DATOS PERO FALTAN CAMPOS CRÍTICOS

Campos que faltan: {', '.join(missing)}

POSIBLE CAUSA:
El método analyze_file() no está construyendo el diccionario completo.
Puede que esté devolviendo resultados parciales.

SOLUCIÓN:
1. Abre worker/analyzer.py
2. Busca dónde se construye el diccionario de retorno
3. Verifica que incluya todos los campos necesarios
4. Compara con la versión corregida de analyzer.py
""")
    else:
        print("""
✅ EL ANALYZER ESTÁ DEVOLVIENDO DATOS

Pero el test_analysis_structure.py no los detectó.
Esto puede ser un problema con cómo el test valida los campos.
""")

print("\n" + "="*80)