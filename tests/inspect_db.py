#!/usr/bin/env python3
"""
Script Mejorado de Inspección de Base de Datos
=============================================

Detecta automáticamente las columnas de análisis, espectro y picos,
y muestra una muestra de los datos junto con información crítica.

Uso: python inspect_db.py [ruta_a_db]
"""

import sqlite3
import json
from pathlib import Path

# Ajusta según tu estructura de proyecto
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent  # carpeta raíz 'mnova-integration'
POSSIBLE_DB_PATHS = [
    BASE_DIR / "backend" / "storage" / "measurements.db",
    BASE_DIR / "backend" / "measurements.db",
    BASE_DIR / "storage" / "measurements.db",
    BASE_DIR / "measurements.db",
]

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
                # Obtener última medición
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
                        try:
                            parsed = json.loads(value)
                            if isinstance(parsed, dict):
                                print(f"\n{col_name}: [JSON Object con {len(parsed)} campos]")
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
                
                # --- ANÁLISIS DE DATOS COMPLETOS ---
                print("\n" + "=" * 80)
                print("ANÁLISIS DE DATOS DE ANÁLISIS Y PICOS")
                print("=" * 80)
                
                analysis_candidates = ['analysis', 'analysis_data', 'data', 'results', 'analysis_json', 'raw_data']
                spectrum_candidates = ['spectrum_data']
                peaks_candidates = ['peaks_data']
                
                def parse_json_column(name, value):
                    try:
                        return json.loads(value) if isinstance(value, str) else value
                    except Exception as e:
                        print(f"❌ Error parseando '{name}': {e}")
                        return None
                
                # Analizar columna de análisis
                found_analysis = False
                for col_name in analysis_candidates:
                    if col_name in column_names:
                        idx = column_names.index(col_name)
                        value = row[idx]
                        if value:
                            raw_json = parse_json_column(col_name, value)
                            if col_name == 'raw_data' and isinstance(raw_json, dict):
                                analysis = raw_json.get('analysis', {})
                            else:
                                analysis = raw_json
                            if isinstance(analysis, dict):
                                print(f"\n✅ Columna de análisis encontrada: '{col_name}'")
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
                                # Campos críticos
                                print(f"\n🔍 CAMPOS CRÍTICOS:")
                                critical = ['total_integral', 'signal_to_noise', 'fluor_percentage', 
                                           'pfas_percentage', 'pifas_percentage', 'pfas_detection']
                                for field in critical:
                                    if field in analysis:
                                        val = analysis[field]
                                        if val in [None, 0]:
                                            print(f"  ⚠️  {field}: {val}")
                                        else:
                                            print(f"  ✅ {field}: presente")
                                    else:
                                        print(f"  ❌ {field}: NO ENCONTRADO")
                                found_analysis = True
                                break
                if not found_analysis:
                    print("❌ No se encontró columna de análisis estándar")
                
                # Analizar columna de espectro
                for col_name in spectrum_candidates:
                    if col_name in column_names:
                        idx = column_names.index(col_name)
                        value = row[idx]
                        spectrum = parse_json_column(col_name, value)
                        if isinstance(spectrum, dict):
                            print(f"\n📊 Columna de espectro encontrada: '{col_name}'")
                            for key in spectrum:
                                val = spectrum[key]
                                if isinstance(val, list):
                                    print(f"  - {key}: lista con {len(val)} elementos")
                                else:
                                    print(f"  - {key}: {type(val).__name__}")
                
                # Analizar columna de picos
                for col_name in peaks_candidates:
                    if col_name in column_names:
                        idx = column_names.index(col_name)
                        value = row[idx]
                        peaks = parse_json_column(col_name, value)
                        if isinstance(peaks, list):
                            print(f"\n⛰️  Columna de picos encontrada: '{col_name}'")
                            print(f"  Total de picos: {len(peaks)}")
                            for peak in peaks[:5]:
                                print(f"   - ppm: {peak.get('ppm')}, int: {peak.get('intensity')}, area: {peak.get('area')}, region: {peak.get('region')}")
                            if len(peaks) > 5:
                                print(f"   ... y {len(peaks) - 5} picos más")
                
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
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = None
        for path in POSSIBLE_DB_PATHS:
            if path.exists():
                db_path = path
                break
        if not db_path:
            print("❌ No se encontró la base de datos automáticamente.")
            print("Rutas buscadas:")
            for path in POSSIBLE_DB_PATHS:
                print(f"  - {path}")
            print("\nUso: python inspect_db.py <ruta_a_la_base_de_datos>")
            sys.exit(1)
    
    if not Path(db_path).exists():
        print(f"❌ No existe el archivo: {db_path}")
        sys.exit(1)
    
    inspect_database(db_path)
