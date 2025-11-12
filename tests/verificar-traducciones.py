#!/usr/bin/env python3
"""
Script de Verificación de Traducciones - CraftRMN Pro
Compara las claves en los archivos de traducción y reporta las faltantes
Soporta backend y frontend
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set

# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------
def load_json(file_path: Path) -> Dict:
    """Carga un archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encontró {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear {file_path}: {e}")
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

def compare_translations(base_file: Path, target_files: list) -> None:
    """Compara el archivo base con los archivos objetivo"""
    print("="*70)
    print(f"🔍 Comparando traducciones con referencia {base_file.name}")
    print("="*70)
    
    base_data = load_json(base_file)
    if base_data is None:
        print(f"❌ No se pudo cargar la referencia {base_file}, se omite la comparación.\n")
        return
    
    base_keys = get_all_keys(base_data)
    print(f"   ✅ {len(base_keys)} claves encontradas en {base_file.name}")
    
    all_ok = True
    
    for target_file in target_files:
        print(f"\n🔎 Comparando con: {target_file}")
        target_data = load_json(target_file)
        if target_data is None:
            print(f"❌ No se pudo cargar {target_file}, se omite.\n")
            all_ok = False
            continue
        target_keys = get_all_keys(target_data)
        
        missing_keys = base_keys - target_keys
        extra_keys = target_keys - base_keys
        
        if missing_keys:
            all_ok = False
            print(f"   ❌ Faltan {len(missing_keys)} claves:")
            for key in sorted(missing_keys):
                print(f"      - {key}")
        else:
            print(f"   ✅ Todas las claves presentes ({len(target_keys)} claves)")
        
        if extra_keys:
            print(f"   ⚠️  {len(extra_keys)} claves adicionales (no en referencia):")
            for key in sorted(extra_keys):
                print(f"      + {key}")
    
    print("\n" + "="*70)
    if all_ok:
        print("✅ TODAS LAS TRADUCCIONES ESTÁN COMPLETAS")
    else:
        print("❌ FALTAN TRADUCCIONES - Ver reporte arriba")
    print("="*70 + "\n")

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    # Detectar ruta raíz del proyecto (padre de tests/)
    ROOT_DIR = Path(__file__).resolve().parent.parent

    # ---------------- BACKEND ----------------
    backend_dir = ROOT_DIR / "backend" / "i18n"
    backend_ref = backend_dir / "es.json"
    backend_targets = [backend_dir / f for f in ["en.json","eu.json","gl.json"]]
    
    print("\n=== BACKEND ===")
    print("="*70)
    if not backend_ref.exists():
        print(f"❌ No se encontró {backend_ref}")
    compare_translations(backend_ref, backend_targets)

    # ---------------- FRONTEND ----------------
    frontend_dir = ROOT_DIR / "frontend" / "js" / "i18n" / "translations"
    frontend_ref = frontend_dir / "es.json"
    frontend_targets = [frontend_dir / f for f in ["en.json","eu.json","gl.json"]]
    
    print("\n=== FRONTEND ===")
    print("="*70)
    if not frontend_ref.exists():
        print(f"❌ No se encontró {frontend_ref}")
    compare_translations(frontend_ref, frontend_targets)

if __name__ == "__main__":
    main()
