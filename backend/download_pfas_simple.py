#!/usr/bin/env python3
"""
Descargador Simple de Estructuras PFAS (Solo PubChem)
======================================================

Script simplificado que descarga estructuras PFAS directamente desde
PubChem SIN necesidad de instalar RDKit.

VENTAJAS:
- No requiere instalación de librerías químicas pesadas
- Solo usa requests (librería estándar de Python)
- Descarga directamente archivos 3D y 2D desde PubChem

USO:
----
    pip install requests
    python download_pfas_simple.py

RESULTADO:
----------
    frontend/assets/molecules/
        ├── pfoa.sdf (archivo 3D)
        ├── pfoa_2d.png (imagen 2D)
        └── ...
"""

import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, Optional


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PFAS_DATABASE = {
    # === Ácidos Perfluoroalcanoicos (PFCAs) ===
    "PFBA": {"cas": "375-22-4", "pubchem_cid": "9395"},
    "PFPeA": {"cas": "2706-90-3", "pubchem_cid": "9554"},
    "PFHxA": {"cas": "307-24-4", "pubchem_cid": "67818"},
    "PFHpA": {"cas": "375-85-9", "pubchem_cid": "66457"},
    "PFOA": {"cas": "335-67-1", "pubchem_cid": "9554"},
    "PFNA": {"cas": "375-95-1", "pubchem_cid": "67406"},
    "PFDA": {"cas": "335-76-2", "pubchem_cid": "67813"},
    "PFUnDA": {"cas": "2058-94-8", "pubchem_cid": "67814"},
    "PFDoDA": {"cas": "307-55-1", "pubchem_cid": "67815"},
    
    # === Sulfonatos (PFSAs) ===
    "PFBS": {"cas": "375-73-5", "pubchem_cid": "67628"},
    "PFPeS": {"cas": "2706-91-4", "pubchem_cid": "158401"},
    "PFHxS": {"cas": "355-46-4", "pubchem_cid": "67734"},
    "PFHpS": {"cas": "375-92-8", "pubchem_cid": "67816"},
    "PFOS": {"cas": "1763-23-1", "pubchem_cid": "74483"},
    "PFNS": {"cas": "68259-12-1", "pubchem_cid": "158586"},
    "PFDS": {"cas": "335-77-3", "pubchem_cid": "67817"},
    
    # === Emergentes ===
    "GenX": {"cas": "13252-13-6", "pubchem_cid": "138683"},
    "ADONA": {"cas": "919005-14-4", "pubchem_cid": "129610805"},
    "F-53B": {"cas": "73606-19-6", "pubchem_cid": "129618826"},
    
    # === Fluorotelómeros ===
    "6:2 FTOH": {"cas": "647-42-7", "pubchem_cid": "9300"},
    "8:2 FTOH": {"cas": "678-39-7", "pubchem_cid": "62406"},
    "10:2 FTOH": {"cas": "865-86-1", "pubchem_cid": "158401"},
    "6:2 FTCA": {"cas": "53826-13-4", "pubchem_cid": "520192"},
    "8:2 FTCA": {"cas": "27854-31-5", "pubchem_cid": "3034285"},
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

def download_all_structures(output_dir: Path):
    """Descarga todas las estructuras PFAS desde PubChem."""
    
    # Crear directorio
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🔬 DESCARGADOR DE ESTRUCTURAS PFAS")
    print("="*70)
    print(f"\n📁 Directorio de salida: {output_dir}")
    print(f"🔬 Compuestos a descargar: {len(PFAS_DATABASE)}")
    print(f"📡 Fuente: PubChem Database")
    print("\n" + "="*70)
    
    stats = {
        "total": len(PFAS_DATABASE),
        "sdf_success": 0,
        "sdf_failed": 0,
        "png_success": 0,
        "png_failed": 0
    }
    
    # Procesar cada compuesto
    for name, data in PFAS_DATABASE.items():
        cas = data["cas"]
        cid = data["pubchem_cid"]
        
        print(f"\n📊 Descargando: {name}")
        print(f"   CAS: {cas}")
        print(f"   PubChem CID: {cid}")
        
        # Generar nombres de archivo
        safe_name = sanitize_filename(name)
        sdf_path = output_dir / f"{safe_name}.sdf"
        png_path = output_dir / f"{safe_name}_2d.png"
        
        # Descargar SDF 3D
        print(f"   🔹 Descargando estructura 3D...")
        if download_sdf_3d(cid, sdf_path):
            stats["sdf_success"] += 1
        else:
            stats["sdf_failed"] += 1
        
        # Descargar imagen 2D
        print(f"   🔹 Descargando imagen 2D...")
        if download_image_2d(cid, png_path, size=400):
            stats["png_success"] += 1
        else:
            stats["png_failed"] += 1
        
        # Pausa para no saturar el servidor
        time.sleep(0.5)
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE DESCARGA")
    print("="*70)
    print(f"\n✅ Estructuras 3D exitosas: {stats['sdf_success']}/{stats['total']}")
    print(f"❌ Estructuras 3D fallidas: {stats['sdf_failed']}/{stats['total']}")
    print(f"✅ Imágenes 2D exitosas: {stats['png_success']}/{stats['total']}")
    print(f"❌ Imágenes 2D fallidas: {stats['png_failed']}/{stats['total']}")
    
    print(f"\n📁 Archivos guardados en: {output_dir}")
    
    # Listar archivos creados
    files = sorted(output_dir.glob("*"))
    if files:
        print(f"\n📄 Archivos creados ({len(files)}):")
        for f in files[:10]:  # Mostrar primeros 10
            print(f"   • {f.name}")
        if len(files) > 10:
            print(f"   ... y {len(files) - 10} más")
    
    if stats['sdf_failed'] > 0 or stats['png_failed'] > 0:
        print(f"\n⚠️  Algunos archivos no se pudieron descargar")
        print(f"   Esto puede ser normal si PubChem no tiene estructura 3D disponible")
    
    print("\n" + "="*70)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal."""
    print("="*70)
    print("🔬 Descargador Simple de Estructuras PFAS")
    print("   Fuente: PubChem Database")
    print("="*70)
    
    # Verificar requests
    try:
        import requests
    except ImportError:
        print("\n❌ Error: 'requests' no está instalado")
        print("   Instala con: pip install requests")
        sys.exit(1)
    
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
    
    # Confirmar
    response = input("\n¿Iniciar descarga? (s/n): ").lower()
    if response != 's':
        print("⏸️  Descarga cancelada")
        return
    
    # Descargar
    download_all_structures(output_dir)
    
    print("\n✅ Proceso completado")
    print(f"\n📁 Revisa los archivos en: {output_dir}")
    print(f"\n💡 Próximos pasos:")
    print(f"   1. Verifica que los archivos se descargaron correctamente")
    print(f"   2. Reinicia tu aplicación Flask")
    print(f"   3. Las visualizaciones deberían funcionar automáticamente")


if __name__ == "__main__":
    main()