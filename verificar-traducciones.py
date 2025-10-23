#!/usr/bin/env python3
"""
Script de Verificación de Traducciones - CraftRMN Pro
Compara las claves en los archivos de traducción y reporta las faltantes
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set

def load_json(file_path: Path) -> Dict:
    """Carga un archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear {file_path}: {e}")
        sys.exit(1)

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
    print("🔍 VERIFICADOR DE TRADUCCIONES - CraftRMN Pro")
    print("="*70)
    
    # Cargar archivo de referencia (español)
    print(f"\n📖 Cargando archivo de referencia: {base_file.name}")
    base_data = load_json(base_file)
    base_keys = get_all_keys(base_data)
    print(f"   ✅ {len(base_keys)} claves encontradas en {base_file.name}")
    
    all_ok = True
    
    for target_file in target_files:
        print(f"\n🔎 Comparando con: {target_file.name}")
        target_data = load_json(target_file)
        target_keys = get_all_keys(target_data)
        
        # Encontrar claves faltantes
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

def main():
    # Ruta del proyecto (ajustar según sea necesario)
    i18n_dir = Path("frontend/i18n")
    
    if not i18n_dir.exists():
        print(f"❌ Error: No se encontró el directorio {i18n_dir}")
        print("   Ejecuta este script desde la raíz del proyecto.")
        sys.exit(1)
    
    # Archivos de traducción
    es_file = i18n_dir / "es.json"
    en_file = i18n_dir / "en.json"
    eu_file = i18n_dir / "eu.json"
    
    # Verificar que existan
    for f in [es_file, en_file, eu_file]:
        if not f.exists():
            print(f"❌ Error: No se encontró {f}")
            sys.exit(1)
    
    # Comparar (español es la referencia)
    compare_translations(es_file, [en_file, eu_file])

if __name__ == "__main__":
    main()