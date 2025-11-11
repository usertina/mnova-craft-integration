#!/usr/bin/env python3
"""
Script Simple de Inspección de Base de Datos
=============================================

Uso: python inspect_db.py [ruta_a_db]
"""

import sqlite3
import json
from pathlib import Path

def inspect_database(db_path):
    """Inspecciona la estructura de la base de datos"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print(f"INSPECCIÓN DE BASE DE DATOS: {db_path}")
        print("=" * 80)
        
        # Listar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 TABLAS ENCONTRADAS ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Inspeccionar la tabla 'measurements'
        if any(t[0] == 'measurements' for t in tables):
            print("\n" + "=" * 80)
            print("ESTRUCTURA DE LA TABLA 'measurements'")
            print("=" * 80)
            
            cursor.execute("PRAGMA table_info(measurements)")
            columns = cursor.fetchall()
            
            print("\n📊 COLUMNAS:")
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                pk_text = " 🔑 [PRIMARY KEY]" if pk else ""
                not_null_text = " ⚠️  [NOT NULL]" if not_null else ""
                default_text = f" [DEFAULT: {default}]" if default else ""
                print(f"  {col_id}. {name}")
                print(f"     Tipo: {col_type}{pk_text}{not_null_text}{default_text}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM measurements")
            count = cursor.fetchone()[0]
            print(f"\n📈 TOTAL DE MEDICIONES: {count}")
            
            if count > 0:
                # Obtener una muestra
                cursor.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                column_names = [col[1] for col in columns]
                
                print("\n" + "=" * 80)
                print("MUESTRA DE LA ÚLTIMA MEDICIÓN")
                print("=" * 80)
                
                for col_name, value in zip(column_names, row):
                    if value is None:
                        print(f"\n{col_name}: NULL")
                    elif isinstance(value, str) and len(value) > 200:
                        # Intentar parsear como JSON
                        try:
                            parsed = json.loads(value)
                            if isinstance(parsed, dict):
                                print(f"\n{col_name}: [JSON Object con {len(parsed)} campos]")
                                # Mostrar primeros 5 campos
                                for i, key in enumerate(list(parsed.keys())[:5]):
                                    val = parsed[key]
                                    if isinstance(val, (dict, list)):
                                        print(f"  - {key}: [{type(val).__name__}]")
                                    else:
                                        print(f"  - {key}: {val}")
                                if len(parsed) > 5:
                                    print(f"  ... y {len(parsed) - 5} campos más")
                            elif isinstance(parsed, list):
                                print(f"\n{col_name}: [JSON Array con {len(parsed)} elementos]")
                        except:
                            print(f"\n{col_name}: [String largo - {len(value)} caracteres]")
                    else:
                        print(f"\n{col_name}: {value}")
                
                # Buscar columna con datos de análisis
                print("\n" + "=" * 80)
                print("ANÁLISIS DE DATOS DE ANÁLISIS")
                print("=" * 80)
                
                analysis_candidates = ['analysis', 'analysis_data', 'data', 'results', 'analysis_json']
                found = False
                
                for col_name in analysis_candidates:
                    if col_name in column_names:
                        idx = column_names.index(col_name)
                        value = row[idx]
                        
                        if value:
                            print(f"\n✅ Encontrada columna de análisis: '{col_name}'")
                            try:
                                analysis = json.loads(value) if isinstance(value, str) else value
                                if isinstance(analysis, dict):
                                    print(f"\n📦 Campos en el análisis ({len(analysis)}):")
                                    for key in sorted(analysis.keys()):
                                        val = analysis[key]
                                        if isinstance(val, dict):
                                            print(f"  - {key}: [dict con {len(val)} campos]")
                                        elif isinstance(val, list):
                                            print(f"  - {key}: [lista con {len(val)} elementos]")
                                        elif isinstance(val, (int, float)):
                                            print(f"  - {key}: {val}")
                                        else:
                                            print(f"  - {key}: {type(val).__name__}")
                                    
                                    # Verificar campos críticos
                                    print(f"\n🔍 CAMPOS CRÍTICOS:")
                                    critical = ['total_integral', 'signal_to_noise', 'fluor_percentage', 
                                               'pfas_percentage', 'pifas_percentage', 'pfas_detection']
                                    for field in critical:
                                        if field in analysis:
                                            val = analysis[field]
                                            if val is None:
                                                print(f"  ⚠️  {field}: NULL")
                                            elif val == 0:
                                                print(f"  ⚠️  {field}: 0 (vacío)")
                                            else:
                                                print(f"  ✅ {field}: presente")
                                        else:
                                            print(f"  ❌ {field}: NO ENCONTRADO")
                                
                                found = True
                                break
                            except Exception as e:
                                print(f"❌ Error parseando: {e}")
                
                if not found:
                    print("\n❌ No se encontró una columna de análisis estándar")
                    print("Los datos pueden estar en una estructura diferente")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("FIN DE LA INSPECCIÓN")
        print("=" * 80)
        
    except sqlite3.Error as e:
        print(f"❌ Error de SQLite: {e}")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {db_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # Rutas comunes
    possible_paths = [
        'backend/storage/measurements.db',
        'backend/measurements.db',
        'measurements.db',
        '../backend/measurements.db',
        'storage/measurements.db'
    ]
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = None
        for path in possible_paths:
            if Path(path).exists():
                db_path = path
                break
        
        if not db_path:
            print("❌ No se encontró la base de datos.")
            print("\nRutas buscadas:")
            for path in possible_paths:
                print(f"  - {path}")
            print("\nUso: python inspect_db.py <ruta_a_la_base_de_datos>")
            sys.exit(1)
    
    if not Path(db_path).exists():
        print(f"❌ No existe el archivo: {db_path}")
        sys.exit(1)
    
    inspect_database(db_path)