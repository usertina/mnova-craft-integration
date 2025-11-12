#!/usr/bin/env python3
"""
Reporte de calidad interactivo para mediciones
"""
import sqlite3
import json

# Configuración
db_path = '../backend/storage/measurements.db'
critical_fields = ['total_integral', 'signal_to_noise', 'pfas_detection']

# Conexión a la DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Leer todas las mediciones
cursor.execute("SELECT id, filename, raw_data FROM measurements ORDER BY id")
rows = cursor.fetchall()

if not rows:
    print("⚠️  No se encontraron mediciones en la base de datos.")
    conn.close()
    exit()

# Preguntar al usuario cuántas mediciones mostrar
while True:
    try:
        n = int(input(f"Hay {len(rows)} mediciones. ¿Cuántas quieres mostrar? "))
        if n <= 0:
            print("Debes ingresar un número mayor que 0.")
            continue
        break
    except ValueError:
        print("Por favor, ingresa un número válido.")

# Limitar el número de mediciones a mostrar
rows_to_show = rows[:n]

reporte = []

for mid, filename, raw_data in rows_to_show:
    entry = {'id': mid, 'filename': filename, 'status': '✅ Válida', 'issues': []}
    
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        entry['status'] = '❌ JSON inválido'
        reporte.append(entry)
        continue
    
    analysis = data.get('analysis', {})
    if not analysis:
        entry['status'] = '❌ Sin análisis'
        reporte.append(entry)
        continue
    
    # Validación de campos críticos
    for field in critical_fields:
        val = analysis.get(field)
        if val is None:
            entry['issues'].append(f"{field} NO ENCONTRADO")
        elif field == 'pfas_detection':
            if not isinstance(val, dict) or not val:
                entry['issues'].append(f"{field} vacío o inválido")
        else:
            if val <= 0:
                entry['issues'].append(f"{field} <= 0")
    
    if entry['issues']:
        entry['status'] = '⚠️ Problemas'
    
    reporte.append(entry)

# Mostrar reporte compacto
print(f"\n{'ID':>5} | {'Archivo':<30} | {'Estado':<15} | Problemas")
print("-"*80)
for e in reporte:
    issues = ", ".join(e['issues'])
    print(f"{e['id']:>5} | {e['filename']:<30} | {e['status']:<15} | {issues}")

conn.close()
