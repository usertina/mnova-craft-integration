#!/usr/bin/env python3
"""
Script de Verificación de Datos en Base de Datos
=================================================

Este script te ayuda a:
1. Ver qué datos se están guardando en cada medición
2. Identificar mediciones con datos faltantes
3. Generar un reporte de la estructura de datos

Uso:
    python check_database.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def check_database(db_path='backend/measurements.db'):
    """Verifica el contenido de la base de datos"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Primero, verificar la estructura de la tabla
        cursor.execute("PRAGMA table_info(measurements)")
        columns_info = cursor.fetchall()
        
        if not columns_info:
            print("❌ No se encontró la tabla 'measurements' en la base de datos")
            return
        
        print("=" * 80)
        print("ESTRUCTURA DE LA TABLA 'measurements'")
        print("=" * 80)
        print("\nColumnas disponibles:")
        column_names = []
        for col in columns_info:
            col_id, name, col_type, not_null, default, pk = col
            column_names.append(name)
            print(f"  - {name} ({col_type})" + (" [PRIMARY KEY]" if pk else ""))
        print()
        
        # Construir query dinámicamente basado en las columnas disponibles
        # Buscar la columna que contiene los datos de análisis
        analysis_column = None
        for possible_name in ['analysis', 'analysis_data', 'data', 'results', 'analysis_json']:
            if possible_name in column_names:
                analysis_column = possible_name
                break
        
        if not analysis_column:
            print("⚠️  No se encontró una columna de análisis estándar.")
            print("Mostrando todas las columnas disponibles...\n")
            # Seleccionar todas las columnas
            cursor.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 10")
        else:
            print(f"✅ Usando columna '{analysis_column}' para datos de análisis\n")
            # Construir query con las columnas necesarias
            cursor.execute(f"SELECT id, filename, timestamp, {analysis_column} FROM measurements ORDER BY id DESC LIMIT 10")
        
        measurements = cursor.fetchall()
        
        if not measurements:
            print("❌ No se encontraron mediciones en la base de datos")
            return
        
        print("=" * 80)
        print("VERIFICACIÓN DE DATOS EN BASE DE DATOS")
        print("=" * 80)
        print(f"Mostrando las últimas {len(measurements)} mediciones:\n")
        
        for idx, row in enumerate(measurements, 1):
            if analysis_column:
                # Sabemos qué columnas esperamos
                mid, filename, timestamp, analysis_json = row
            else:
                # Mostrar todas las columnas disponibles
                print(f"\n{'=' * 80}")
                print(f"Medición: {row}")
                print(f"Columnas: {column_names}")
                continue
            
            print(f"\n{'=' * 80}")
            print(f"Medición #{mid}: {filename}")
            print(f"Timestamp: {timestamp}")
            print("-" * 80)
            
            if not analysis_json:
                print("❌ Esta medición no tiene datos de análisis guardados")
                continue
            
            try:
                analysis = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
                
                if not isinstance(analysis, dict):
                    print(f"⚠️  Datos de análisis en formato inesperado: {type(analysis)}")
                    continue
                
                # Verificar campos esenciales
                essential_fields = {
                    'total_integral': analysis.get('total_integral'),
                    'signal_to_noise': analysis.get('signal_to_noise'),
                    'fluor_percentage': analysis.get('fluor_percentage'),
                    'pfas_percentage': analysis.get('pfas_percentage', analysis.get('pifas_percentage')),
                    'pfas_detection': analysis.get('pfas_detection')
                }
                
                print("\n📊 CAMPOS ESENCIALES:")
                missing_count = 0
                for field, value in essential_fields.items():
                    if value is not None and value != 0:
                        if field == 'pfas_detection':
                            if isinstance(value, dict):
                                compounds = len(value.get('compounds', []))
                                print(f"  ✅ {field}: {compounds} compuestos detectados")
                            else:
                                print(f"  ✅ {field}: presente")
                        else:
                            print(f"  ✅ {field}: {value}")
                    elif value == 0:
                        print(f"  ⚠️  {field}: 0 (puede estar vacío)")
                        missing_count += 1
                    else:
                        print(f"  ❌ {field}: NO ENCONTRADO")
                        missing_count += 1
                
                # Mostrar todos los campos disponibles
                print(f"\n📋 TODOS LOS CAMPOS DISPONIBLES ({len(analysis)} campos):")
                for key in sorted(analysis.keys()):
                    if key not in ['pfas_detection', 'quality_breakdown', 'peaks', 'spectrum']:
                        value = analysis[key]
                        if isinstance(value, (int, float)):
                            print(f"  - {key}: {value}")
                        elif isinstance(value, str):
                            print(f"  - {key}: {value[:50]}..." if len(value) > 50 else f"  - {key}: {value}")
                        elif isinstance(value, list):
                            print(f"  - {key}: [lista con {len(value)} elementos]")
                        elif isinstance(value, dict):
                            print(f"  - {key}: [objeto con {len(value)} campos]")
                        else:
                            print(f"  - {key}: [tipo: {type(value).__name__}]")
                
                if missing_count > 0:
                    print(f"\n⚠️  Esta medición tiene {missing_count} campos faltantes o vacíos")
                else:
                    print(f"\n✅ Esta medición tiene todos los campos esenciales")
                
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON de {analysis_column}: {e}")
            except Exception as e:
                print(f"❌ Error procesando medición: {e}")
                import traceback
                traceback.print_exc()
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("RESUMEN:")
        print("=" * 80)
        
        if not analysis_column:
            print("""
⚠️  No se encontró una columna estándar de análisis en tu base de datos.

Esto puede significar que:
1. La estructura de tu base de datos es diferente a la esperada
2. Necesitas actualizar este script para tu caso específico
3. Los datos se guardan en otra tabla

Revisa la estructura de tu base de datos y actualiza el script según sea necesario.
            """)
        else:
            print("""
Si ves muchos campos con "NO ENCONTRADO" o "0", significa que:

1. ❌ Las mediciones fueron guardadas ANTES de aplicar la corrección
   → Solución: Re-analizar las muestras importantes

2. ❌ El analizador no está generando esos datos  
   → Solución: Revisar analyzer.py

3. ❌ El backend no los está guardando correctamente
   → Solución: Verificar que app.py esté actualizado y reiniciar el servidor

Para NUEVAS mediciones (después de la corrección del backend), 
todos los campos deberían mostrar ✅ y tener valores numéricos > 0.

PRÓXIMOS PASOS:
1. Aplica las correcciones en app.py (backend) y app.js (frontend)
2. Reinicia el servidor Flask
3. Analiza un espectro NUEVO
4. Vuelve a ejecutar este script y verifica la última medición
            """)
        
    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
    except FileNotFoundError:
        print(f"❌ No se encontró la base de datos en: {db_path}")
        print("Verifica la ruta de tu base de datos.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


def check_single_measurement(db_path, measurement_id):
    """Verifica una medición específica con detalle completo"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Primero verificar qué columnas tiene la tabla
        cursor.execute("PRAGMA table_info(measurements)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Buscar columna de análisis
        analysis_column = None
        for possible_name in ['analysis', 'analysis_data', 'data', 'results', 'analysis_json']:
            if possible_name in column_names:
                analysis_column = possible_name
                break
        
        cursor.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ No se encontró la medición con ID {measurement_id}")
            return
        
        measurement = dict(zip(column_names, row))
        
        print("=" * 80)
        print(f"DETALLE COMPLETO - MEDICIÓN #{measurement_id}")
        print("=" * 80)
        
        for key, value in measurement.items():
            if key == analysis_column and value:
                print(f"\n{key}:")
                try:
                    analysis = json.loads(value) if isinstance(value, str) else value
                    print(json.dumps(analysis, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"  [No se pudo parsear: {e}]")
            elif key in ['spectrum', 'peaks'] and value:
                try:
                    data = json.loads(value) if isinstance(value, str) else value
                    if isinstance(data, dict):
                        print(f"\n{key}: [objeto con {len(data)} campos]")
                    elif isinstance(data, list):
                        print(f"\n{key}: [lista con {len(data)} elementos]")
                    else:
                        print(f"\n{key}: {type(data)}")
                except:
                    print(f"\n{key}: [datos complejos]")
            else:
                if isinstance(value, str) and len(value) > 100:
                    print(f"{key}: {value[:100]}... [truncado]")
                else:
                    print(f"{key}: {value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # Rutas comunes donde puede estar la base de datos
    possible_paths = [
        'backend/measurements.db',
        'measurements.db',
        '../backend/measurements.db',
        'backend/storage/measurements.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if Path(path).exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ No se encontró la base de datos.")
        print("Rutas buscadas:")
        for path in possible_paths:
            print(f"  - {path}")
        print("\nEspecifica la ruta manualmente:")
        print("  python check_database.py /ruta/a/measurements.db")
        sys.exit(1)
    
    print(f"📂 Base de datos encontrada: {db_path}\n")
    
    # Si se pasó un ID como argumento, mostrar solo esa medición
    if len(sys.argv) > 1:
        try:
            mid = int(sys.argv[1])
            check_single_measurement(db_path, mid)
        except ValueError:
            # Si no es un número, asumir que es una ruta
            check_database(sys.argv[1])
    else:
        check_database(db_path)