#!/usr/bin/env python3
"""
Descargador Completo de Estructuras PFAS (Solo PubChem)
========================================================

Script que descarga estructuras PFAS directamente desde PubChem
para TODOS los compuestos de la base de datos (30+ compuestos).

VENTAJAS:
- No requiere instalación de librerías químicas pesadas
- Solo usa requests (librería estándar de Python)
- Descarga directamente archivos 3D y 2D desde PubChem

USO:
----
    pip install requests
    python download_pfas_complete.py

RESULTADO:
----------
    frontend/assets/molecules/
        ├── pfoa.sdf (archivo 3D)
        ├── pfoa_2d.png (imagen 2D)
        └── ... (60+ archivos para 30+ compuestos)
"""

import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, Optional


# ============================================================================
# BASE DE DATOS COMPLETA DE PFAS (30+ COMPUESTOS)
# ============================================================================

PFAS_DATABASE = {
    # ========================================================================
    # ÁCIDOS PERFLUOROALCANOICOS (PFCAs) - 14 compuestos
    # ========================================================================
    "PFBA": {
        "name": "Ácido Perfluorobutanoico",
        "cas": "375-22-4",
        "pubchem_cid": "9395",
        "category": "PFCA"
    },
    "PFPeA": {
        "name": "Ácido Perfluoropentanoico",
        "cas": "2706-90-3",
        "pubchem_cid": "9554",
        "category": "PFCA"
    },
    "PFHxA": {
        "name": "Ácido Perfluorohexanoico",
        "cas": "307-24-4",
        "pubchem_cid": "67818",
        "category": "PFCA"
    },
    "PFHpA": {
        "name": "Ácido Perfluoroheptanoico",
        "cas": "375-85-9",
        "pubchem_cid": "66457",
        "category": "PFCA"
    },
    "PFOA": {
        "name": "Ácido Perfluorooctanoico",
        "cas": "335-67-1",
        "pubchem_cid": "9554",
        "category": "PFCA"
    },
    "PFNA": {
        "name": "Ácido Perfluorononanoico",
        "cas": "375-95-1",
        "pubchem_cid": "67406",
        "category": "PFCA"
    },
    "PFDA": {
        "name": "Ácido Perfluorodecanoico",
        "cas": "335-76-2",
        "pubchem_cid": "67813",
        "category": "PFCA"
    },
    "PFUnDA": {
        "name": "Ácido Perfluoroundecanoico",
        "cas": "2058-94-8",
        "pubchem_cid": "67814",
        "category": "PFCA"
    },
    "PFDoDA": {
        "name": "Ácido Perfluorododecanoico",
        "cas": "307-55-1",
        "pubchem_cid": "67815",
        "category": "PFCA"
    },
    "PFTrDA": {
        "name": "Ácido Perfluorotridecanoico",
        "cas": "72629-94-8",
        "pubchem_cid": "67816",
        "category": "PFCA"
    },
    "PFTeDA": {
        "name": "Ácido Perfluorotetradecanoico",
        "cas": "376-06-7",
        "pubchem_cid": "67817",
        "category": "PFCA"
    },
    
    # ========================================================================
    # SULFONATOS PERFLUOROALCÁNICOS (PFSAs) - 8 compuestos
    # ========================================================================
    "PFPrS": {
        "name": "Sulfonato de Perfluoropropano",
        "cas": "423-41-6",
        "pubchem_cid": "16212366",
        "category": "PFSA"
    },
    "PFBS": {
        "name": "Sulfonato de Perfluorobutano",
        "cas": "375-73-5",
        "pubchem_cid": "67628",
        "category": "PFSA"
    },
    "PFPeS": {
        "name": "Sulfonato de Perfluoropentano",
        "cas": "2706-91-4",
        "pubchem_cid": "158401",
        "category": "PFSA"
    },
    "PFHxS": {
        "name": "Sulfonato de Perfluorohexano",
        "cas": "355-46-4",
        "pubchem_cid": "67734",
        "category": "PFSA"
    },
    "PFHpS": {
        "name": "Sulfonato de Perfluoroheptano",
        "cas": "375-92-8",
        "pubchem_cid": "129626779",
        "category": "PFSA"
    },
    "PFOS": {
        "name": "Sulfonato de Perfluorooctano",
        "cas": "1763-23-1",
        "pubchem_cid": "74483",
        "category": "PFSA"
    },
    "PFNS": {
        "name": "Sulfonato de Perfluorononano",
        "cas": "68259-12-1",
        "pubchem_cid": "158586",
        "category": "PFSA"
    },
    "PFDS": {
        "name": "Sulfonato de Perfluorodecano",
        "cas": "335-77-3",
        "pubchem_cid": "129626780",
        "category": "PFSA"
    },
    
    # ========================================================================
    # PFAS DE NUEVA GENERACIÓN (Polyether) - 4 compuestos
    # ========================================================================
    "GenX": {
        "name": "HFPO-DA (GenX)",
        "cas": "13252-13-6",
        "pubchem_cid": "138683",
        "category": "Ether-PFCA"
    },
    "ADONA": {
        "name": "4,8-Dioxa-3H-perfluorononanoato",
        "cas": "919005-14-4",
        "pubchem_cid": "129610805",
        "category": "Ether-PFCA"
    },
    "HFPO-TA": {
        "name": "Ácido Perfluoro-2-propoxipropanoico",
        "cas": "13252-13-6",  # Mismo que GenX (isómero)
        "pubchem_cid": "138683",  # Usar mismo que GenX
        "category": "Ether-PFCA"
    },
    "F-53B": {
        "name": "Cl-PFESA (F-53B)",
        "cas": "73606-19-6",
        "pubchem_cid": "129618826",
        "category": "Chlorinated-PFSA"
    },
    
    # ========================================================================
    # FLUOROTELÓMEROS ALCOHOLES (FTOHs) - 3 compuestos
    # ========================================================================
    "6:2_FTOH": {
        "name": "6:2 Fluorotelomer Alcohol",
        "cas": "647-42-7",
        "pubchem_cid": "9300",
        "category": "FTOH"
    },
    "8:2_FTOH": {
        "name": "8:2 Fluorotelomer Alcohol",
        "cas": "678-39-7",
        "pubchem_cid": "62406",
        "category": "FTOH"
    },
    "10:2_FTOH": {
        "name": "10:2 Fluorotelomer Alcohol",
        "cas": "865-86-1",
        "pubchem_cid": "158401",
        "category": "FTOH"
    },
    
    # ========================================================================
    # FLUOROTELÓMEROS ÁCIDOS (FTCAs) - 2 compuestos
    # ========================================================================
    "6:2_FTCA": {
        "name": "6:2 Fluorotelomer Carboxylic Acid",
        "cas": "53826-13-4",
        "pubchem_cid": "520192",
        "category": "FTCA"
    },
    "8:2_FTCA": {
        "name": "8:2 Fluorotelomer Carboxylic Acid",
        "cas": "27854-31-5",
        "pubchem_cid": "3034285",
        "category": "FTCA"
    },
    
    # ========================================================================
    # DERIVADOS Y PRECURSORES - 6 compuestos
    # ========================================================================
    "Iso-PFOS": {
        "name": "Branched PFOS isomers",
        "cas": "Various",
        "pubchem_cid": "74483",  # Usar estructura lineal como referencia
        "category": "PFSA-branched"
    },
    "PFECHS": {
        "name": "Perfluoroethylcyclohexane sulfonate",
        "cas": "67584-42-3",
        "pubchem_cid": "137623888",
        "category": "PFSA-cyclic"
    },
    "PFOSA": {
        "name": "Perfluorooctane sulfonamide",
        "cas": "754-91-6",
        "pubchem_cid": "9578",
        "category": "PFSA-derivative"
    },
    "N-EtFOSA": {
        "name": "N-Ethyl perfluorooctane sulfonamide",
        "cas": "4151-50-2",
        "pubchem_cid": "9301",
        "category": "PFSA-derivative"
    },
    "N-MeFOSA": {
        "name": "N-Methyl perfluorooctane sulfonamide",
        "cas": "31506-32-8",
        "pubchem_cid": "67814",
        "category": "PFSA-derivative"
    },
    "FOSA": {
        "name": "Perfluorooctane sulfonamide",
        "cas": "754-91-6",
        "pubchem_cid": "9578",  # Mismo que PFOSA
        "category": "PFSA-derivative"
    }
}


# ============================================================================
# FUNCIONES DE DESCARGA
# ============================================================================

def download_file(url: str, output_path: Path, description: str = "archivo") -> bool:
    """Descarga un archivo desde una URL."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"   ✅ {description} descargado: {output_path.name}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"   ⚠️  {description} no disponible en PubChem")
        else:
            print(f"   ❌ Error HTTP {e.response.status_code}")
        return False
        
    except Exception as e:
        print(f"   ❌ Error descargando {description}: {e}")
        return False


def download_sdf_3d(cid: str, output_path: Path) -> bool:
    """Descarga archivo SDF 3D desde PubChem."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF?record_type=3d"
    return download_file(url, output_path, "SDF 3D")


def download_image_2d(cid: str, output_path: Path, size: int = 400) -> bool:
    """Descarga imagen 2D desde PubChem."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size={size}x{size}"
    return download_file(url, output_path, "Imagen 2D")


def sanitize_filename(name: str) -> str:
    """Convierte nombre a formato válido para archivo."""
    # Reemplazar caracteres especiales
    name = name.replace(":", "-")
    name = name.replace(" ", "_")
    return name.lower()


# ============================================================================
# DESCARGADOR PRINCIPAL
# ============================================================================

def download_all_structures(output_dir: Path, categories_filter: list = None):
    """
    Descarga todas las estructuras PFAS desde PubChem.
    
    Args:
        output_dir: Directorio donde guardar los archivos
        categories_filter: Lista de categorías a descargar (None = todas)
    """
    
    # Crear directorio
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filtrar por categorías si se especifica
    compounds_to_download = PFAS_DATABASE
    if categories_filter:
        compounds_to_download = {
            k: v for k, v in PFAS_DATABASE.items()
            if v.get("category") in categories_filter
        }
    
    print("\n" + "="*70)
    print("🔬 DESCARGADOR COMPLETO DE ESTRUCTURAS PFAS")
    print("="*70)
    print(f"\n📁 Directorio de salida: {output_dir}")
    print(f"🔬 Compuestos totales en base de datos: {len(PFAS_DATABASE)}")
    print(f"📥 Compuestos a descargar: {len(compounds_to_download)}")
    print(f"📡 Fuente: PubChem Database")
    
    if categories_filter:
        print(f"🏷️  Categorías seleccionadas: {', '.join(categories_filter)}")
    
    # Estadísticas por categoría
    categories_count = {}
    for data in compounds_to_download.values():
        cat = data.get("category", "Unknown")
        categories_count[cat] = categories_count.get(cat, 0) + 1
    
    print("\n📊 Distribución por categoría:")
    for cat, count in sorted(categories_count.items()):
        print(f"   • {cat}: {count} compuestos")
    
    print("\n" + "="*70)
    
    stats = {
        "total": len(compounds_to_download),
        "sdf_success": 0,
        "sdf_failed": 0,
        "png_success": 0,
        "png_failed": 0,
        "by_category": {}
    }
    
    # Procesar cada compuesto
    for i, (compound_id, data) in enumerate(compounds_to_download.items(), 1):
        name = data.get("name", compound_id)
        cas = data.get("cas", "N/A")
        cid = data["pubchem_cid"]
        category = data.get("category", "Unknown")
        
        print(f"\n[{i}/{len(compounds_to_download)}] 📊 {compound_id}")
        print(f"   Nombre: {name}")
        print(f"   CAS: {cas}")
        print(f"   PubChem CID: {cid}")
        print(f"   Categoría: {category}")
        
        # Generar nombres de archivo
        safe_name = sanitize_filename(compound_id)
        sdf_path = output_dir / f"{safe_name}.sdf"
        png_path = output_dir / f"{safe_name}_2d.png"
        
        # Estadísticas por categoría
        if category not in stats["by_category"]:
            stats["by_category"][category] = {"success": 0, "failed": 0}
        
        # Descargar SDF 3D
        print(f"   🔹 Descargando estructura 3D...")
        if download_sdf_3d(cid, sdf_path):
            stats["sdf_success"] += 1
            stats["by_category"][category]["success"] += 1
        else:
            stats["sdf_failed"] += 1
            stats["by_category"][category]["failed"] += 1
        
        # Descargar imagen 2D
        print(f"   🔹 Descargando imagen 2D...")
        if download_image_2d(cid, png_path, size=400):
            stats["png_success"] += 1
        else:
            stats["png_failed"] += 1
        
        # Pausa para no saturar el servidor
        time.sleep(0.5)
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE DESCARGA")
    print("="*70)
    print(f"\n🔬 Total de compuestos procesados: {stats['total']}")
    print(f"\n✅ Estructuras 3D exitosas: {stats['sdf_success']}/{stats['total']} ({stats['sdf_success']/stats['total']*100:.1f}%)")
    print(f"❌ Estructuras 3D fallidas: {stats['sdf_failed']}/{stats['total']}")
    print(f"\n✅ Imágenes 2D exitosas: {stats['png_success']}/{stats['total']} ({stats['png_success']/stats['total']*100:.1f}%)")
    print(f"❌ Imágenes 2D fallidas: {stats['png_failed']}/{stats['total']}")
    
    # Resumen por categoría
    print(f"\n📊 Resultados por categoría:")
    for cat, cat_stats in sorted(stats["by_category"].items()):
        total_cat = cat_stats["success"] + cat_stats["failed"]
        print(f"   • {cat}: {cat_stats['success']}/{total_cat} exitosos")
    
    print(f"\n📁 Archivos guardados en: {output_dir}")
    
    # Listar archivos creados
    files = sorted(output_dir.glob("*"))
    if files:
        print(f"\n📄 Archivos creados: {len(files)} archivos")
        print(f"   • {len(list(output_dir.glob('*.sdf')))} archivos SDF (3D)")
        print(f"   • {len(list(output_dir.glob('*.png')))} imágenes PNG (2D)")
        
        print(f"\n📋 Muestra de archivos:")
        for f in files[:10]:  # Mostrar primeros 10
            print(f"   • {f.name}")
        if len(files) > 10:
            print(f"   ... y {len(files) - 10} más")
    
    if stats['sdf_failed'] > 0 or stats['png_failed'] > 0:
        print(f"\n⚠️  NOTA: Algunos archivos no se pudieron descargar")
        print(f"   • Esto es normal si PubChem no tiene estructura 3D disponible")
        print(f"   • Algunos compuestos pueden no estar en PubChem")
        print(f"   • Verifica los CIDs si es necesario")
    
    print("\n" + "="*70)
    
    return stats


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def list_categories():
    """Lista todas las categorías disponibles."""
    categories = set()
    for data in PFAS_DATABASE.values():
        categories.add(data.get("category", "Unknown"))
    
    print("\n📊 CATEGORÍAS DISPONIBLES:")
    print("="*70)
    for i, cat in enumerate(sorted(categories), 1):
        count = sum(1 for d in PFAS_DATABASE.values() if d.get("category") == cat)
        print(f"{i}. {cat} ({count} compuestos)")
    print("="*70)


def verify_pubchem_ids():
    """Verifica que todos los compuestos tengan PubChem CID."""
    missing = []
    for compound_id, data in PFAS_DATABASE.items():
        if "pubchem_cid" not in data:
            missing.append(compound_id)
    
    if missing:
        print(f"\n⚠️  ADVERTENCIA: {len(missing)} compuestos sin PubChem CID:")
        for comp in missing:
            print(f"   • {comp}")
    else:
        print(f"\n✅ Todos los compuestos tienen PubChem CID")
    
    return len(missing) == 0


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal."""
    print("="*70)
    print("🔬 Descargador Completo de Estructuras PFAS")
    print("   Base de datos: 30+ compuestos PFAS")
    print("   Fuente: PubChem Database")
    print("="*70)
    
    # Verificar requests
    try:
        import requests
    except ImportError:
        print("\n❌ Error: 'requests' no está instalado")
        print("   Instala con: pip install requests")
        sys.exit(1)
    
    # Verificar PubChem IDs
    print("\n🔍 Verificando base de datos...")
    verify_pubchem_ids()
    
    # Mostrar categorías
    list_categories()
    
    # Determinar directorio de salida
    script_dir = Path(__file__).parent
    
    # Buscar directorio frontend
    frontend_dir = script_dir.parent / "frontend" / "assets" / "molecules"
    
    if frontend_dir.parent.parent.exists():
        output_dir = frontend_dir
    else:
        output_dir = script_dir / "molecules"
        print(f"\n⚠️  No se encontró directorio frontend")
        print(f"   Usando: {output_dir}")
    
    print(f"\n📂 Directorio de salida: {output_dir}")
    
    # Opciones de descarga
    print("\n📥 OPCIONES DE DESCARGA:")
    print("1. Descargar TODOS los compuestos (30+)")
    print("2. Descargar por categoría")
    print("3. Salir")
    
    choice = input("\nSelecciona opción (1-3): ").strip()
    
    if choice == "1":
        response = input("\n¿Descargar TODOS los compuestos? (s/n): ").lower()
        if response != 's':
            print("⏸️  Descarga cancelada")
            return
        
        # Descargar todo
        download_all_structures(output_dir)
        
    elif choice == "2":
        list_categories()
        selected = input("\nIngresa categoría(s) separadas por coma: ").strip()
        categories = [cat.strip() for cat in selected.split(",")]
        
        # Descargar categorías seleccionadas
        download_all_structures(output_dir, categories_filter=categories)
        
    elif choice == "3":
        print("👋 Adiós!")
        return
    else:
        print("❌ Opción inválida")
        return
    
    print("\n✅ Proceso completado")
    print(f"\n📁 Revisa los archivos en: {output_dir}")
    print(f"\n💡 Próximos pasos:")
    print(f"   1. Verifica que los archivos se descargaron correctamente")
    print(f"   2. Los archivos SDF son para visualización 3D")
    print(f"   3. Los archivos PNG son para visualización 2D")
    print(f"   4. Reinicia tu aplicación Flask")
    print(f"   5. Las visualizaciones deberían funcionar automáticamente")


if __name__ == "__main__":
    main()