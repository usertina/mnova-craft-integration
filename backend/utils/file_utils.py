"""
Utilidades para procesamiento de archivos
"""
import os
import logging
import zipfile
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_and_find_data(file_path: Path) -> Path:
    """
    Extrae archivos ZIP y encuentra el directorio/archivo de datos NMR.
    
    Args:
        file_path: Ruta al archivo subido
    
    Returns:
        Path al archivo/directorio de datos a analizar
    """
    if file_path.suffix.lower() != '.zip':
        logger.debug(f"Archivo no es ZIP: {file_path.name}")
        return file_path
    
    logger.info(f"📦 Archivo ZIP detectado: {file_path.name}")
    
    extract_dir = file_path.parent / f"{file_path.stem}_extracted"
    
    if extract_dir.exists():
        logger.debug(f"Limpiando directorio previo: {extract_dir}")
        shutil.rmtree(extract_dir)
    
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        logger.info(f"   ✅ ZIP extraído a: {extract_dir}")
        
        # Buscar estructura Bruker
        for root, dirs, files in os.walk(extract_dir):
            root_path = Path(root)
            
            if 'fid' in files or 'ser' in files:
                logger.info(f"   🔍 Datos Bruker: {root_path}")
                return root_path
            
            for dir_name in dirs:
                if dir_name.isdigit():
                    exp_dir = root_path / dir_name
                    if (exp_dir / 'fid').exists() or (exp_dir / 'ser').exists():
                        logger.info(f"   🔍 Experimento Bruker: {exp_dir}")
                        return exp_dir
        
        # Buscar estructura Varian
        for root, dirs, files in os.walk(extract_dir):
            root_path = Path(root)
            if 'procpar' in files and 'fid' in files:
                logger.info(f"   🔍 Datos Varian: {root_path}")
                return root_path
        
        # Buscar archivos conocidos
        for root, dirs, files in os.walk(extract_dir):
            root_path = Path(root)
            for file in files:
                file_path_candidate = root_path / file
                ext = file_path_candidate.suffix.lower()
                
                if ext in ['.csv', '.txt', '.jdf', '.jdx', '.ft', '.ft1', '.ft2']:
                    logger.info(f"   🔍 Archivo encontrado: {file_path_candidate}")
                    return file_path_candidate
        
        logger.warning(f"   ⚠️ Estructura desconocida, usando raíz")
        return extract_dir
        
    except zipfile.BadZipFile:
        logger.error(f"   ❌ ZIP corrupto")
        raise ValueError("ZIP corrupto o inválido")
    except Exception as e:
        logger.error(f"   ❌ Error extrayendo ZIP: {e}")
        raise