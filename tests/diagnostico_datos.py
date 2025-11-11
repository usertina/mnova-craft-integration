#!/usr/bin/env python3
"""
Script de diagnóstico para CraftRMN Pro
Verifica qué campos están presentes en las mediciones guardadas
"""

import sys
import sqlite3
import json
from pathlib import Path

def analyze_database():
    """Analiza la base de datos y muestra la estructura de los análisis"""
    
    db_path = Path('backend/storage/measurements.db')
    
    if not db_path.exists():
        print(f"❌ No se encontró la base de datos en: {db_path}")
        return
    
    print("="*80)
    print("🔍 DIAGNÓSTICO DE ESTRUCTURA DE DATOS")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener las últimas 5 mediciones
    cursor.execute("""
        SELECT id, filename, company, analysis_date, analysis 
        FROM measurements 
        ORDER BY id DESC 
        LIMIT 5
    """)
    
    measurements = cursor.fetchall()
    
    if not measurements:
        print("❌ No hay mediciones en la base de datos")
        return
    
    print(f"\n📊 Analizando últimas {len(measurements)} mediciones:\n")
    
    # Campos esperados según el código
    expected_fields = {
        'file_name': 'Nombre del archivo',
        'concentration': 'Concentración',
        'fluor_total': 'Flúor total',
        'pifas': 'PFAS/PIFAS',
        'peaks': 'Picos detectados',
        'quality_metrics': 'Métricas de calidad',
        'pfas_detection': 'Detección de PFAS',
        'quality_score': 'Score de calidad',
        'baseline_corrected': 'Baseline corregido',
        'spectrometer_config': 'Config espectrómetro'
    }
    
    for measurement in measurements:
        mid, filename, company, date, analysis_json = measurement
        
        print(f"{'='*80}")
        print(f"ID: {mid}")
        print(f"Archivo: {filename}")
        print(f"Empresa: {company}")
        print(f"Fecha: {date}")
        print(f"-"*80)
        
        try:
            analysis = json.loads(analysis_json)
            
            # Contar campos presentes
            present_fields = []
            missing_fields = []
            
            for field, description in expected_fields.items():
                if field in analysis:
                    present_fields.append(field)
                    
                    # Mostrar detalles específicos
                    if field == 'fluor_total':
                        ft = analysis[field]
                        print(f"  ✅ {description}:")
                        print(f"     - Área: {ft.get('total_area', 'N/A')}")
                        print(f"     - Porcentaje: {ft.get('percentage', 'N/A')}%")
                    
                    elif field == 'pifas':
                        pf = analysis[field]
                        print(f"  ✅ {description}:")
                        print(f"     - Área: {pf.get('total_area', 'N/A')}")
                        print(f"     - Porcentaje: {pf.get('percentage', 'N/A')}%")
                    
                    elif field == 'peaks':
                        peaks = analysis[field]
                        print(f"  ✅ {description}: {len(peaks)} picos")
                        if peaks:
                            p = peaks[0]
                            print(f"     Ejemplo pico 1:")
                            print(f"     - ppm: {p.get('ppm', 'N/A')}")
                            print(f"     - intensity: {p.get('intensity', 'N/A')}")
                            print(f"     - width_hz: {p.get('width_hz', 'N/A')}")
                            print(f"     - snr: {p.get('snr', 'N/A')}")
                    
                    elif field == 'quality_metrics':
                        qm = analysis[field]
                        print(f"  ✅ {description}:")
                        print(f"     - SNR: {qm.get('snr', 'N/A')}")
                        print(f"     - Noise level: {qm.get('noise_level', 'N/A')}")
                    
                    elif field == 'pfas_detection':
                        pd = analysis[field]
                        print(f"  ✅ {description}:")
                        print(f"     - Total detectados: {pd.get('total_detected', 0)}")
                        if pd.get('detected_pfas'):
                            for pfas in pd['detected_pfas'][:3]:  # Primeros 3
                                print(f"     - {pfas.get('name', 'N/A')}: {pfas.get('confidence', 0)*100:.1f}%")
                    
                    else:
                        print(f"  ✅ {description}: presente")
                else:
                    missing_fields.append(field)
            
            print(f"\n  📊 Resumen:")
            print(f"     ✅ Campos presentes: {len(present_fields)}/{len(expected_fields)}")
            
            if missing_fields:
                print(f"\n  ❌ Campos faltantes:")
                for field in missing_fields:
                    print(f"     - {field}: {expected_fields[field]}")
            
            # Mostrar todos los campos que SÍ existen (incluso inesperados)
            all_fields = list(analysis.keys())
            unexpected = [f for f in all_fields if f not in expected_fields]
            if unexpected:
                print(f"\n  ℹ️  Campos adicionales:")
                for field in unexpected:
                    print(f"     - {field}")
            
            print()
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Error al parsear JSON: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("📋 CAMPOS ESPERADOS POR EL FRONTEND:")
    print("="*80)
    for field, desc in expected_fields.items():
        print(f"  • {field}: {desc}")
    
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES:")
    print("="*80)
    print("""
Si faltan campos:
1. Verifica que analyzer.py esté retornando todos los campos
2. Verifica que app.py (Flask) esté guardando el análisis completo
3. Ejecuta un nuevo análisis para generar datos completos
4. Elimina análisis antiguos que estén incompletos

Comandos útiles:
  # Ver estructura de un análisis reciente
  python -c "import sqlite3, json; conn=sqlite3.connect('backend/storage/measurements.db'); 
             cursor=conn.execute('SELECT analysis FROM measurements ORDER BY id DESC LIMIT 1'); 
             print(json.dumps(json.loads(cursor.fetchone()[0]), indent=2))"
  
  # Limpiar análisis antiguos
  sqlite3 backend/storage/measurements.db "DELETE FROM measurements WHERE id < (SELECT MAX(id) FROM measurements);"
""")

if __name__ == '__main__':
    try:
        analyze_database()
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)