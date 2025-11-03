#!/usr/bin/env python3
"""
Ver contenido de raw_data
"""
import sqlite3
import json

db_path = 'backend/storage/measurements.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, filename, raw_data FROM measurements ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()

if row:
    mid, filename, raw_data = row
    print(f"Medición #{mid}: {filename}")
    print("=" * 80)
    
    data = json.loads(raw_data)
    print("\nContenido de raw_data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if 'analysis' in data:
        print("\n" + "=" * 80)
        print("Contenido de raw_data['analysis']:")
        print("=" * 80)
        analysis = data['analysis']
        
        print("\nCampos disponibles:")
        for key in sorted(analysis.keys()):
            val = analysis[key]
            if isinstance(val, dict):
                print(f"  - {key}: [dict con {len(val)} campos]")
            elif isinstance(val, list):
                print(f"  - {key}: [lista con {len(val)} elementos]")
            else:
                print(f"  - {key}: {val}")
        
        print("\n🔍 Verificando campos críticos:")
        critical = ['total_integral', 'signal_to_noise', 'pfas_detection']
        for field in critical:
            if field in analysis:
                val = analysis[field]
                if val:
                    print(f"  ✅ {field}: {val if not isinstance(val, dict) else 'presente'}")
                else:
                    print(f"  ⚠️  {field}: {val} (vacío)")
            else:
                print(f"  ❌ {field}: NO ENCONTRADO")

conn.close()