#!/usr/bin/env python3
"""
Script Mejorado de Inspección de Base de Datos (Optimizado)
=========================================================
Inspecciona la estructura de la BD y muestra la última medición.

Uso: python inspect_db.py [ruta_a_db]
"""

import sqlite3
import json
from pathlib import Path
import sys

# --- Configuración de Rutas ---
BASE_DIR = Path(__file__).parent.parent
POSSIBLE_DB_PATHS = [
    BASE_DIR / "backend" / "storage" / "measurements.db",
    BASE_DIR / "backend" / "measurements.db",
]
# -----------------------------

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title, level=1):
    if level == 1:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD} INSPECCIÓN: {title.upper()}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    else:
        print(f"\n{Colors.CYAN}{'-' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}{title}{Colors.RESET}")
        print(f"{Colors.CYAN}{'-' * 80}{Colors.RESET}")

def inspect_database(db_path):
    """Inspecciona la estructura de la base de datos"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print_header(f"{db_path.name}")
        
        # --- 1. Estructura de la Tabla 'measurements' ---
        print_header("Estructura de la Tabla 'measurements'", 2)
        try:
            cursor.execute("PRAGMA table_info(measurements)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                pk_text = f" {Colors.YELLOW}[PK]{Colors.RESET}" if pk else ""
                print(f"  - {Colors.BOLD}{name}{Colors.RESET} ({col_type}){pk_text}")
        except sqlite3.OperationalError:
            print(f"{Colors.RED}❌ ERROR: No se encontró la tabla 'measurements'.{Colors.RESET}")
            return

        # --- 2. Conteo de Mediciones ---
        cursor.execute("SELECT COUNT(*) FROM measurements")
        count = cursor.fetchone()[0]
        print(f"\n{Colors.CYAN}Total de Mediciones: {count}{Colors.RESET}")
        
        if count == 0:
            print(f"{Colors.YELLOW}La base de datos está vacía. No hay mediciones para mostrar.{Colors.RESET}")
            conn.close()
            return
            
        # --- 3. Muestra de la Última Medición ---
        print_header(f"Muestra de la Última Medición (ID MÁS ALTO)", 2)
        cursor.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        analysis_data = None
        analysis_col_name = None

        for col_name, value in zip(column_names, row):
            print(f"\n{Colors.BOLD}[{col_name}]{Colors.RESET}")
            
            if value is None:
                print("  NULL")
                continue
            
            # Intentar decodificar JSON en columnas de texto
            if isinstance(value, str) and value.startswith(("{", "[")):
                try:
                    parsed = json.loads(value)
                    print(f"  {Colors.GREEN}[JSON Decodificado]{Colors.RESET}")
                    
                    # Guardar datos de análisis para el resumen final
                    if col_name == 'analysis':
                        analysis_data = parsed
                        analysis_col_name = col_name
                    elif col_name == 'raw_data' and isinstance(parsed, dict) and 'analysis' in parsed:
                         analysis_data = parsed['analysis']
                         analysis_col_name = f"{col_name} -> analysis"

                    # Mostrar resumen de JSON
                    if isinstance(parsed, dict):
                        keys = list(parsed.keys())
                        print(f"  Tipo: Objeto ({len(keys)} campos)")
                        print(f"  Campos de ejemplo: {keys[:5]}...")
                    elif isinstance(parsed, list):
                        print(f"  Tipo: Array ({len(parsed)} elementos)")
                except json.JSONDecodeError:
                    print(f"  Tipo: String (Largo: {len(value)})")
                    print(f"  Valor: {value[:100]}...") # No es JSON válido
            else:
                 print(f"  Tipo: {type(value).__name__}")
                 print(f"  Valor: {str(value)[:100]}")

        # --- 4. Resumen de Campos Críticos (si se encontraron) ---
        if analysis_data:
            print_header(f"Resumen de Campos Críticos (de '{analysis_col_name}')", 2)
            
            critical_fields = [
                'quality_score', 'signal_to_noise', 'fluor_percentage', 
                'pfas_percentage', 'pifas_percentage', 'pfas_concentration', 
                'pifas_concentration', 'total_integral', 'pfas_detection'
            ]
            
            for field in critical_fields:
                value = analysis_data.get(field)
                if value is not None:
                    if field == 'pfas_detection' and isinstance(value, dict):
                        detected_count = len(value.get('detected_pfas', []))
                        print(f"  {Colors.GREEN}✅ {field}:{Colors.RESET} {detected_count} compuestos detectados")
                    else:
                        print(f"  {Colors.GREEN}✅ {field}:{Colors.RESET} {value}")
                else:
                    print(f"  {Colors.RED}❌ {field}: NO ENCONTRADO{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  No se encontró una columna 'analysis' o 'raw_data' con JSON válido.{Colors.RESET}")

        conn.close()
        
    except sqlite3.Error as e:
        print(f"{Colors.RED}❌ Error de SQLite: {e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error inesperado: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_path_arg = Path(sys.argv[1])
        if not db_path_arg.exists():
            print(f"❌ No existe el archivo: {db_path_arg}")
            sys.exit(1)
        db_path = db_path_arg
    else:
        db_path = None
        for path in POSSIBLE_DB_PATHS:
            if path.exists():
                db_path = path
                break
        if not db_path:
            print(f"{Colors.RED}❌ No se encontró la base de datos automáticamente.{Colors.RESET}")
            print("Rutas buscadas:")
            for path in POSSIBLE_DB_PATHS:
                print(f"  - {path}")
            sys.exit(1)
    
    inspect_database(db_path)