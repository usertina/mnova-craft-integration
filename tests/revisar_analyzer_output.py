#!/usr/bin/env python3
"""
Muestra de manera clara lo que devolvió el analyzer en el test
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
print("📦 CONTENIDO DEVUELTO POR EL ANALYZER (resumen):")
print("="*80)

# Mostrar los primeros 5000 caracteres del JSON completo
print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])

print("\n" + "="*80)
print("📊 ESTRUCTURA DETALLADA:")
print("="*80)

if isinstance(data, dict):
    print(f"\n✅ Es un diccionario con {len(data)} campos:")
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"  • {key}: dict con {len(value)} campos")
        elif isinstance(value, list):
            print(f"  • {key}: lista con {len(value)} items")
        else:
            print(f"  • {key}: {type(value).__name__}")

    # Campos críticos
    critical_fields = ['file_name', 'peaks', 'pfas_detection', 'fluor_total', 'pifas']
    missing_critical = [f for f in critical_fields if f not in data]

    print("\n📋 Verificación de campos críticos:")
    for f in critical_fields:
        if f in data:
            print(f"  ✅ {f}: presente")
        else:
            print(f"  ❌ {f}: FALTA")

    # Mensaje final
    print("\n" + "="*80)
    print("🔧 DIAGNÓSTICO FINAL:")
    print("="*80)

    if missing_critical:
        print(f"⚠️ Faltan campos críticos: {', '.join(missing_critical)}")
        print("Revisa el método analyze_file() en worker/analyzer.py para asegurarte de que construya y devuelva todos los campos requeridos.")
    else:
        print("✅ Todos los campos críticos están presentes.")
        print("✅ El analyzer parece estar funcionando correctamente y devolviendo todos los datos necesarios.")

else:
    print(f"\n❌ NO es un diccionario, es: {type(data).__name__}")
    print(f"Contenido parcial: {str(data)[:500]}")

print("\n" + "="*80)
