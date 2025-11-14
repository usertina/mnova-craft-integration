#!/usr/bin/env python3
"""
Script de Verificación de Traducciones (Optimizado)
Compara las claves en los archivos de traducción y reporta las faltantes.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_header(title):
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}🧪 TEST: {title.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET} | {message}")

def print_fail(message):
    print(f"{Colors.RED}❌ FAIL{Colors.RESET} | {message}")

def print_warn(message):
    print(f"{Colors.YELLOW}⚠️  WARN{Colors.RESET} | {message}")

def load_json(file_path: Path) -> Dict:
    """Carga un archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print_fail(f"No se encontró {file_path}")
        return None
    except json.JSONDecodeError as e:
        print_fail(f"Error al parsear {file_path}: {e}")
        return None

def get_all_keys(d: Dict, parent_key: str = '') -> Set[str]:
    """Extrae todas las claves de forma recursiva"""
    keys = set()
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        keys.add(new_key)
        if isinstance(v, dict):
            keys.update(get_all_keys(v, new_key))
    return keys

def compare_translations(base_file: Path, target_files: list) -> bool:
    """Compara el archivo base con los archivos objetivo. Devuelve True si todo OK."""
    print_header(f"Comparando traducciones (Referencia: {base_file.name})")
    
    base_data = load_json(base_file)
    if base_data is None:
        print_fail(f"No se pudo cargar la referencia {base_file}, se omite la comparación.\n")
        return False
    
    base_keys = get_all_keys(base_data)
    print(f"   {Colors.CYAN}ℹ️  {len(base_keys)} claves encontradas en {base_file.name}{Colors.RESET}")
    
    global_ok = True
    
    for target_file in target_files:
        print(f"\n--- Comparando con: {target_file.name} ---")
        target_data = load_json(target_file)
        if target_data is None:
            global_ok = False
            continue
            
        target_keys = get_all_keys(target_data)
        
        missing_keys = base_keys - target_keys
        extra_keys = target_keys - base_keys
        
        if missing_keys:
            global_ok = False
            print_fail(f"Faltan {len(missing_keys)} claves:")
            for key in sorted(missing_keys):
                print(f"      - {key}")
        else:
            print_pass(f"Todas las claves de referencia están presentes ({len(target_keys)} claves)")
        
        if extra_keys:
            print_warn(f"{len(extra_keys)} claves adicionales (no están en la referencia):")
            for key in sorted(extra_keys):
                print(f"      + {key}")
    
    return global_ok

def main():
    ROOT_DIR = Path(__file__).resolve().parent.parent
    results = {}

    # --- BACKEND ---
    backend_dir = ROOT_DIR / "backend" / "i18n"
    backend_ref = backend_dir / "es.json"
    backend_targets = [f for f in backend_dir.glob("*.json") if f != backend_ref]
    
    if backend_ref.exists():
        results['Backend'] = compare_translations(backend_ref, backend_targets)
    else:
        print_fail(f"No se encontró el archivo de referencia de backend: {backend_ref}")
        results['Backend'] = False

    # --- FRONTEND ---
    frontend_dir = ROOT_DIR / "frontend" / "js" / "i18n" / "translations"
    frontend_ref = frontend_dir / "es.json"
    frontend_targets = [f for f in frontend_dir.glob("*.json") if f != frontend_ref]
    
    if frontend_ref.exists():
        results['Frontend'] = compare_translations(frontend_ref, frontend_targets)
    else:
        print_fail(f"No se encontró el archivo de referencia de frontend: {frontend_ref}")
        results['Frontend'] = False

    # --- Resumen Final ---
    print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}📊 RESUMEN FINAL DE TRADUCCIONES{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    
    all_passed = all(results.values())
    
    for test_name, result in results.items():
        if result:
            print(f"{Colors.GREEN}✅ {test_name}: PASÓ{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ {test_name}: FALLÓ{Colors.RESET}")
            
    if all_passed:
        print(f"\n{Colors.GREEN}🎉 ¡EXCELENTE! Todas las traducciones están sincronizadas.{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}⚠️  ATENCIÓN: Faltan claves en algunos archivos de traducción.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())