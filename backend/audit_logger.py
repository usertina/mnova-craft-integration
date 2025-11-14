"""
Sistema de auditoría y logging avanzado
Registra todas las acciones importantes para compliance y debug
"""

import logging
import json
from datetime import datetime
from pathlib import Path
import os

# Crear directorio de logs si no existe
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

# Logger principal
app_logger = logging.getLogger('craftrmn')
app_logger.setLevel(logging.DEBUG if os.getenv('FLASK_DEBUG') == 'true' else logging.INFO)

# Handler para archivo general
file_handler = logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)


# ============================================================================
# AUDIT LOGGER (eventos importantes)
# ============================================================================

class AuditLogger:
    """
    Logger especializado para eventos de auditoría.
    Registra en formato JSON para fácil análisis.
    """
    
    def __init__(self):
        self.enabled = os.getenv('AUDIT_LOG_ENABLED', 'true').lower() == 'true'
        self.log_file = LOG_DIR / (os.getenv('AUDIT_LOG_FILE', 'audit.log'))
        
        if self.enabled:
            # Crear logger de auditoría
            self.logger = logging.getLogger('audit')
            self.logger.setLevel(logging.INFO)
            
            # Handler para archivo de auditoría
            audit_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            audit_handler.setLevel(logging.INFO)
            
            # Formato JSON
            audit_formatter = logging.Formatter('%(message)s')
            audit_handler.setFormatter(audit_formatter)
            
            self.logger.addHandler(audit_handler)
            
            app_logger.info(f"✅ Audit logging enabled: {self.log_file}")
    
    def log_event(self, event_type, details, user='anonymous', ip='unknown', level='INFO'):
        """
        Registra un evento de auditoría.
        
        Args:
            event_type: Tipo de evento (login, analysis, export, etc.)
            details: Diccionario con detalles del evento
            user: Usuario o company_id
            ip: Dirección IP
            level: Nivel de log (INFO, WARNING, ERROR)
        """
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user': user,
            'ip': ip,
            'level': level,
            'details': details
        }
        
        log_line = json.dumps(event, ensure_ascii=False)
        
        if level == 'ERROR':
            self.logger.error(log_line)
        elif level == 'WARNING':
            self.logger.warning(log_line)
        else:
            self.logger.info(log_line)
    
    def log_login(self, company_id, success, ip, reason=None):
        """Registra intento de login"""
        self.log_event(
            event_type='LOGIN',
            details={
                'company_id': company_id,
                'success': success,
                'reason': reason
            },
            user=company_id if success else 'failed',
            ip=ip,
            level='INFO' if success else 'WARNING'
        )
    
    def log_analysis(self, company_id, filename, success, ip, error=None):
        """Registra análisis"""
        self.log_event(
            event_type='ANALYSIS',
            details={
                'filename': filename,
                'success': success,
                'error': error
            },
            user=company_id,
            ip=ip,
            level='INFO' if success else 'ERROR'
        )
    
    def log_export(self, company_id, export_type, format_type, ip):
        """Registra exportación"""
        self.log_event(
            event_type='EXPORT',
            details={
                'export_type': export_type,
                'format': format_type
            },
            user=company_id,
            ip=ip
        )
    
    def log_sync(self, measurement_id, success, attempts, error=None):
        """Registra sincronización"""
        self.log_event(
            event_type='SYNC',
            details={
                'measurement_id': measurement_id,
                'success': success,
                'attempts': attempts,
                'error': error
            },
            user='system',
            ip='localhost',
            level='INFO' if success else 'WARNING'
        )
    
    def log_security_event(self, event_type, details, ip, severity='WARNING'):
        """Registra eventos de seguridad"""
        self.log_event(
            event_type=f'SECURITY_{event_type}',
            details=details,
            user='system',
            ip=ip,
            level=severity
        )


# Instancia global
audit_logger = AuditLogger()


# ============================================================================
# HELPERS PARA INTEGRACIÓN
# ============================================================================

def get_request_ip():
    """Obtiene IP del request actual"""
    from flask import request
    return request.headers.get('X-Forwarded-For', request.remote_addr)


def log_request_audit(event_type, details, user='anonymous'):
    """Helper para loggear desde endpoints"""
    ip = get_request_ip()
    audit_logger.log_event(event_type, details, user, ip)