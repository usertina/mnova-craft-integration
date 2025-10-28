"""
CraftRMN Pro - Gestor de Configuración del Dispositivo
CAMBIO: Ahora solo gestiona el estado del dispositivo (activado/no activado)
y la configuración de análisis. La gestión de empresas se
mueve a app.py.
"""

import hashlib
from typing import Dict, Optional
from datetime import datetime
import logging
import uuid 
import json

from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Gestiona la configuración del dispositivo (ID, estado de activación,
    parámetros de análisis).
    """
    
    def __init__(self):
        self.db = get_db()
        self._init_default_config()

    def _init_default_config(self):
        """
        Asegura que la configuración por defecto exista en la BD
        en la primera ejecución.
        """
        if self.db.get_config("device_id") is None:
            logger.info("Primera ejecución: Creando configuración por defecto en la BD...")
            
            device_uuid = str(uuid.uuid4())[:8].upper()
            new_id = f"RMN-{datetime.now().year}-{device_uuid}" 
            
            default_config = {
                'device_id': new_id,
                'activated': 'false', # Activado por el admin
                'activation_date': 'null',
                'license_key': 'null', # Licencia del admin
                'sync_enabled': 'true',
                'sync_interval': '300',
                'analysis_params': json.dumps({
                    'fluor_range': {'min': -150.0, 'max': -50.0},
                    'pifas_range': {'min': -130.0, 'max': -60.0},
                    'default_concentration': 1.0
                })
            }
            
            for key, value in default_config.items():
                self.db.set_config(key, value)
    
    # ==================== ESTADO DEL DISPOSITIVO ====================
    
    def is_activated(self) -> bool:
        """Verifica si el dispositivo está activado POR EL ADMIN"""
        return self.db.get_config('activated') == 'true'
    
    def get_device_id(self) -> str:
        """Obtiene el ID del dispositivo"""
        return self.db.get_config('device_id') or 'unknown'
    
    # ==================== ACTIVACIÓN (ADMIN) ====================
    
    def activate_device(self, license_key: str) -> bool:
        """Activa el dispositivo (para el admin)"""
        try:
            self.db.set_config('license_key', license_key)
            self.db.set_config('activated', 'true')
            self.db.set_config('activation_date', datetime.now().isoformat())
            logger.info(f"Dispositivo activado por el administrador.")
            return True
        except Exception as e:
            logger.error(f"Error en activación del dispositivo: {e}")
            return False
    
    # ==================== SINCRONIZACIÓN ====================
    
    def get_sync_enabled(self) -> bool:
        return self.db.get_config('sync_enabled') == 'true'
    
    def set_sync_enabled(self, enabled: bool):
        self.db.set_config('sync_enabled', 'true' if enabled else 'false')

    def get_sync_interval(self) -> int:
        return int(self.db.get_config('sync_interval') or 300)
    
    def set_sync_interval(self, interval: int):
        self.db.set_config('sync_interval', str(interval))

    # ==================== ANÁLISIS ====================
    
    def get_analysis_params(self) -> Dict:
        params_str = self.db.get_config('analysis_params')
        try:
            return json.loads(params_str) if params_str else {}
        except json.JSONDecodeError:
            return {}
    
    def update_analysis_params(self, params: Dict):
        current_params = self.get_analysis_params()
        current_params.update(params)
        self.db.set_config('analysis_params', json.dumps(current_params))


class LicenseValidator:
    """Valida la licencia del dispositivo (del admin)"""
    
    def __init__(self, master_key: str = "CRAFTRMN_SECRET_KEY_2025"):
        self.master_key = master_key
    
    def generate_admin_license(self, device_id: str) -> str:
        """Genera una clave de licencia de ADMIN"""
        
        ### ======================================================
        ### LA CORRECCIÓN ESTÁ AQUÍ
        ### ======================================================
        # Antes era "CRAFTRMN_ADMIN", ahora es "ADMIN"
        admin_id = "ADMIN"
        ### ======================================================
        
        data = f"{admin_id}:{device_id}"
        
        hash_input = f"{data}:{self.master_key}"
        logger.debug(f"[generate_license] Hash input: {hash_input}")
        
        signature = hashlib.sha256(hash_input.encode()).hexdigest()[:12].upper()
        
        return f"ADMIN-{device_id}-{signature}"
    
    def validate_license(self, license_key: str, device_id: str) -> bool:
        """Valida una clave de licencia (debe ser de ADMIN)"""
        try:
            logger.debug(f"[validate_license] Validando clave: {license_key}")
            logger.debug(f"[validate_license] Device ID del servidor: {device_id}")

            parts = license_key.split('-')
            if len(parts) < 3 or parts[0] != "ADMIN":
                logger.warning(f"Formato de licencia inválido o no es ADMIN: {license_key}")
                return False
            
            provided_signature = parts[-1]
            admin_id = parts[0] # "ADMIN"
            lic_device_id = "-".join(parts[1:-1])

            logger.debug(f"[validate_license] ID (licencia): {admin_id}")
            logger.debug(f"[validate_license] ID device (licencia): {lic_device_id}")
            
            if lic_device_id != device_id:
                logger.warning(f"Licencia NO corresponde al dispositivo: {device_id} (servidor) vs {lic_device_id} (licencia)")
                return False
            
            data = f"{admin_id}:{lic_device_id}"
            hash_input = f"{data}:{self.master_key}"
            logger.debug(f"[generate_license] Hash input: {hash_input}")

            expected_signature = hashlib.sha256(hash_input.encode()).hexdigest()[:12].upper()
            
            logger.debug(f"[validate_license] Firma esperada: {expected_signature}")
            logger.debug(f"[validate_license] Firma proporcionada: {provided_signature}")
            
            is_valid = (provided_signature == expected_signature)
            
            if is_valid:
                logger.info("Licencia de ADMIN validada correctamente")
            else:
                logger.warning("Firma de licencia ADMIN inválida")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validando licencia: {e}")
            return False

# Instancia global
_config_instance = None

def get_config_manager() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance