#!/usr/bin/env python3
"""
Script de verificación de la integración SQLite + Multi-empresa
Ejecutar desde la carpeta raíz del proyecto
"""

import requests
import json
from pathlib import Path
import sys

# Configuración
BASE_URL = "http://localhost:5000"
TEST_FILE = "test_spectrum.txt"  # Ajusta esto a un archivo real que tengas

def test_health():
    """Verificar que el servidor responde"""
    print("1️⃣  Verificando servidor...")
    try:
        resp = requests.get(f"{BASE_URL}/api/health")
        if resp.status_code == 200:
            print("   ✅ Servidor funcionando")
            return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   ⚠️  Asegúrate de que el servidor está corriendo: python backend/app.py")
        return False
    return False

def test_config():
    """Verificar configuración del dispositivo"""
    print("\n2️⃣  Verificando configuración...")
    try:
        resp = requests.get(f"{BASE_URL}/api/config")
        if resp.status_code == 200:
            config = resp.json()
            print(f"   ✅ Device ID: {config.get('device_id')}")
            print(f"   ✅ Company ID: {config.get('company_id')}")
            print(f"   ✅ Company Name: {config.get('company_name')}")
            print(f"   ✅ Sync Enabled: {config.get('sync_enabled')}")
            return config
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return None

def test_set_company():
    """Configurar empresa de prueba"""
    print("\n3️⃣  Configurando empresa de prueba...")
    try:
        data = {
            "company_id": "empresa_prueba_001",
            "company_name": "Empresa de Prueba S.A.",
            "sync_enabled": True,
            "sync_interval": 300
        }
        resp = requests.post(f"{BASE_URL}/api/config", json=data)
        if resp.status_code == 200:
            print("   ✅ Empresa configurada correctamente")
            config = resp.json()['config']
            print(f"      • Company: {config['company_name']}")
            print(f"      • ID: {config['company_id']}")
            return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return False

def test_database_endpoints():
    """Verificar endpoints de base de datos"""
    print("\n4️⃣  Verificando endpoints SQLite...")
    
    # Obtener mediciones
    try:
        resp = requests.get(f"{BASE_URL}/api/measurements?page=1&per_page=5")
        if resp.status_code == 200:
            data = resp.json()
            count = len(data.get('measurements', []))
            print(f"   ✅ Endpoint mediciones funciona")
            print(f"      • Mediciones en BD: {count}")
            
            if count > 0:
                # Probar obtener una medición específica
                first_id = data['measurements'][0]['id']
                resp2 = requests.get(f"{BASE_URL}/api/measurements/{first_id}")
                if resp2.status_code == 200:
                    print(f"   ✅ Endpoint medición individual funciona")
                    print(f"      • Medición ID {first_id} recuperada")
        else:
            print(f"   ⚠️  No hay mediciones aún (normal si es primera vez)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_analysis_with_db():
    """Verificar que el análisis guarda en SQLite"""
    print("\n5️⃣  Probando análisis con guardado en BD...")
    
    # Crear archivo de prueba
    test_content = """Ejemplo de espectro de prueba
-150 0.5
-140 0.8
-130 0.9
-120 1.2
-110 1.5
-100 1.8
-90 2.1
-80 1.9
-70 1.6
-60 1.3"""
    
    test_path = Path("test_spectrum.txt")
    test_path.write_text(test_content)
    
    try:
        # Enviar archivo para análisis
        with open(test_path, 'rb') as f:
            files = {'file': ('test_spectrum.txt', f, 'text/plain')}
            params = {
                'parameters': json.dumps({
                    'fluor_range': {'min': -150, 'max': -50},
                    'pifas_range': {'min': -60, 'max': -130},
                    'concentration': 1.0
                })
            }
            
            resp = requests.post(f"{BASE_URL}/api/analyze", 
                                files=files, 
                                data=params)
            
            if resp.status_code == 200:
                result = resp.json()
                print("   ✅ Análisis completado")
                
                if 'measurement_id' in result:
                    print(f"   ✅ Guardado en SQLite con ID: {result['measurement_id']}")
                else:
                    print("   ⚠️  No se encontró measurement_id en respuesta")
                
                if 'result_file' in result:
                    print(f"   ✅ Guardado en JSON: {result['result_file']}")
                
                # Mostrar resumen del análisis
                if 'analysis' in result:
                    analysis = result['analysis']
                    print(f"\n   📊 Resultados del análisis:")
                    print(f"      • Fluoruro: {analysis.get('fluor_percentage', 'N/A')}%")
                    print(f"      • PFAS: {analysis.get('pifas_percentage', 'N/A')}%")
                    print(f"      • Concentración: {analysis.get('pifas_concentration', 'N/A')} ppm")
                
                return result.get('measurement_id')
            else:
                print(f"   ❌ Error en análisis: {resp.status_code}")
                print(f"      {resp.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        # Limpiar archivo de prueba
        if test_path.exists():
            test_path.unlink()
    
    return None

def verify_database_file():
    """Verificar que el archivo de base de datos existe"""
    print("\n6️⃣  Verificando archivo de base de datos...")
    
    db_path = Path("storage/measurements.db")
    if db_path.exists():
        size = db_path.stat().st_size / 1024  # KB
        print(f"   ✅ Base de datos existe: {db_path}")
        print(f"      • Tamaño: {size:.2f} KB")
        return True
    else:
        print(f"   ❌ No se encuentra la base de datos en: {db_path}")
        print(f"      • Verifica que database.py se está ejecutando correctamente")
        return False

def main():
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE INTEGRACIÓN SQLite + Multi-empresa")
    print("=" * 60)
    
    # Verificar que el servidor está corriendo
    if not test_health():
        print("\n⚠️  El servidor no está corriendo.")
        print("Ejecuta en otra terminal: python backend/app.py")
        return
    
    # Verificar configuración
    config = test_config()
    
    # Configurar empresa si no está configurada
    if config and (not config.get('company_id') or config.get('company_id') == 'default'):
        test_set_company()
    
    # Verificar base de datos
    verify_database_file()
    
    # Verificar endpoints de BD
    test_database_endpoints()
    
    # Hacer análisis de prueba
    measurement_id = test_analysis_with_db()
    
    if measurement_id:
        print(f"\n✅ INTEGRACIÓN EXITOSA")
        print(f"   La medición {measurement_id} se guardó en SQLite")
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    print("""
    Si todo muestra ✅, tu sistema está funcionando correctamente con:
    • SQLite integrado
    • Sistema multi-empresa
    • Guardado dual (JSON + BD)
    • Nuevos endpoints funcionando
    
    Próximos pasos:
    1. Revisa los datos en storage/measurements.db
    2. Configura diferentes empresas con /api/config
    3. Usa /api/measurements para consultar el historial
    4. Actualiza tu frontend para usar los nuevos endpoints
    """)

if __name__ == "__main__":
    main()