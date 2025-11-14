"""
Security middleware y utilidades
Implementa headers de seguridad, validación de inputs, y protecciones varias
"""

from flask import request, abort
from functools import wraps
import re
import logging
from pathlib import Path

# ============================================================================
# SECURITY HEADERS
# ============================================================================

def add_security_headers(response):
    """
    Añade headers de seguridad a todas las respuestas.
    Debe ser registrado como @app.after_request
    """
    # Prevenir clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevenir MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection (aunque CSP es mejor)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy (no enviar info sensible en referer)
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    # NOTA: Ajustar según necesidades del frontend
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.plot.ly",
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
        "img-src 'self' data: https: blob:",
        "font-src 'self' https://cdnjs.cloudflare.com",
        "connect-src 'self' https://script.google.com",
        "frame-ancestors 'self'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    
    # HSTS (HTTP Strict Transport Security) - Solo si usas HTTPS
    # Descomentar cuando tengas SSL configurado
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Permissions Policy (Feature Policy deprecated)
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=(), '
        'payment=(), usb=(), magnetometer=(), gyroscope=()'
    )
    
    return response


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Validadores de entrada para diferentes tipos de datos"""
    
    @staticmethod
    def validate_company_id(company_id):
        """
        Valida que el company_id sea seguro.
        Solo permite letras, números, y guiones bajos.
        """
        if not company_id:
            return False
        
        # Longitud razonable
        if len(company_id) > 50:
            return False
        
        # Solo caracteres seguros
        if not re.match(r'^[A-Z0-9_]+$', company_id):
            return False
        
        return True
    
    @staticmethod
    def validate_filename(filename):
        """
        Valida que el nombre de archivo sea seguro.
        Previene path traversal y caracteres peligrosos.
        """
        if not filename:
            return False
        
        # Longitud razonable
        if len(filename) > 255:
            return False
        
        # Caracteres peligrosos
        dangerous_chars = ['..', '/', '\\', '\x00', '~', '$', '&', '|', ';', '`', '<', '>']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Solo caracteres seguros (letras, números, guiones, puntos, espacios)
        if not re.match(r'^[a-zA-Z0-9._\-\s]+$', filename):
            return False
        
        return True
    
    @staticmethod
    def validate_pin(pin):
        """
        Valida formato de PIN.
        Debe ser 4-8 dígitos.
        """
        if not pin:
            return False
        
        # Convertir a string si es número
        pin_str = str(pin)
        
        # Longitud correcta
        if len(pin_str) < 4 or len(pin_str) > 8:
            return False
        
        # Solo dígitos
        if not pin_str.isdigit():
            return False
        
        return True
    
    @staticmethod
    def validate_page_number(page):
        """
        Valida número de página para paginación.
        """
        try:
            page_int = int(page)
            if page_int < 1:
                return False
            if page_int > 10000:  # Límite razonable
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_limit(limit):
        """
        Valida límite para queries.
        """
        try:
            limit_int = int(limit)
            if limit_int < 1:
                return False
            if limit_int > 1000:  # Máximo razonable
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_search_term(search_term):
        """
        Sanitiza términos de búsqueda.
        Elimina caracteres SQL peligrosos.
        """
        if not search_term:
            return ""
        
        # Eliminar caracteres peligrosos
        dangerous_chars = ['%', '_', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = str(search_term)
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limitar longitud
        sanitized = sanitized[:100]
        
        return sanitized.strip()


# ============================================================================
# FILE UPLOAD VALIDATION
# ============================================================================

class FileValidator:
    """Validación de archivos subidos"""
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {
        '.csv', '.txt', '.jdf', '.jdx', '.ft', '.ft1', '.ft2', '.zip',
        'fid', 'ser', 'acqus', 'procs', ''  # Archivos sin extensión (Bruker)
    }
    
    # Tipos MIME permitidos
    ALLOWED_MIME_TYPES = {
        'text/csv',
        'text/plain',
        'application/zip',
        'application/x-zip-compressed',
        'application/octet-stream',  # Para archivos binarios (fid, ser)
        'chemical/x-jcamp-dx'  # Para archivos JDF
    }
    
    # Tamaño máximo (100 MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    @classmethod
    def validate_file(cls, file):
        """
        Valida un archivo subido.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        if not file.filename:
            return False, "Empty filename"
        
        # 1. Validar nombre de archivo
        if not InputValidator.validate_filename(file.filename):
            return False, "Invalid filename"
        
        # 2. Validar extensión
        file_path = Path(file.filename)
        extension = file_path.suffix.lower()
        filename_lower = file.filename.lower()
        
        # Permitir archivos sin extensión si son conocidos (fid, ser, etc.)
        if extension == '' and filename_lower not in ['fid', 'ser', 'acqus', 'procs']:
            if extension not in cls.ALLOWED_EXTENSIONS:
                return False, f"File extension not allowed: {extension}"
        elif extension not in cls.ALLOWED_EXTENSIONS:
            return False, f"File extension not allowed: {extension}"
        
        # 3. Validar tipo MIME
        mime_type = file.content_type
        if mime_type and mime_type not in cls.ALLOWED_MIME_TYPES:
            logging.warning(f"Unusual MIME type: {mime_type} for {file.filename}")
            # No rechazar, solo advertir (algunos navegadores envían MIMEs incorrectos)
        
        # 4. Validar tamaño (leer y verificar)
        file.seek(0, 2)  # Ir al final
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > cls.MAX_FILE_SIZE:
            return False, f"File too large: {file_size} bytes (max: {cls.MAX_FILE_SIZE})"
        
        if file_size == 0:
            return False, "Empty file"
        
        return True, None


# ============================================================================
# CSRF PROTECTION
# ============================================================================

def csrf_exempt(f):
    """
    Decorador para eximir endpoints de CSRF protection.
    Usar solo para APIs públicas o con autenticación alternativa.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    decorated_function._csrf_exempt = True
    return decorated_function


def check_csrf_token():
    """
    Verifica token CSRF en requests POST/PUT/DELETE.
    
    NOTA: Para simplificar, verificamos que el Origin header
    coincida con el host esperado. Más adelante implementar
    CSRF tokens en formularios si es necesario.
    """
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        # Verificar que la petición viene del origen correcto
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        host = request.headers.get('Host')
        
        # Si no hay Origin ni Referer, rechazar (posible CSRF)
        if not origin and not referer:
            # Excepción: Permitir si es un endpoint API con JWT
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logging.warning(f"⚠️ Possible CSRF attack: No Origin/Referer in {request.method} to {request.path}")
                # En desarrollo, solo advertir. En producción, rechazar:
                # abort(403, "CSRF token missing")
        
        # Si hay Origin, verificar que coincida
        if origin:
            allowed_origins = [
                'http://localhost:5000',
                'http://127.0.0.1:5000',
                f'http://{host}'
            ]
            
            if origin not in allowed_origins:
                logging.warning(f"⚠️ CSRF: Origin {origin} not in allowed list")
                # En producción, descomentar:
                # abort(403, "Invalid origin")


# ============================================================================
# RATE LIMITING HELPERS
# ============================================================================

def get_user_identifier():
    """
    Obtiene identificador único del usuario para rate limiting.
    Combina IP + JWT (si existe) para límites más precisos.
    """
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Si hay JWT, incluir company_id
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            # Extraer company_id del token (sin verificarlo completamente)
            import jwt
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            company_id = payload.get('company_id', 'unknown')
            return f"{ip}:{company_id}"
        except:
            pass
    
    return ip


# ============================================================================
# REQUEST LOGGING
# ============================================================================

def log_request():
    """
    Log de todas las requests para auditoría.
    """
    # Información básica
    method = request.method
    path = request.path
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Información de autenticación
    auth_header = request.headers.get('Authorization', '')
    company_id = 'anonymous'
    
    if auth_header.startswith('Bearer '):
        try:
            import jwt
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            company_id = payload.get('company_id', 'unknown')
        except:
            pass
    
    # Log en formato estructurado
    logging.info(
        f"[REQUEST] {method} {path} | IP: {ip} | User: {company_id} | UA: {user_agent[:50]}"
    )


# ============================================================================
# SANITIZACIÓN DE RESPUESTAS
# ============================================================================

def sanitize_error_message(error_msg):
    """
    Sanitiza mensajes de error para no exponer información sensible.
    """
    # No exponer rutas del sistema
    sanitized = str(error_msg).replace(str(Path.cwd()), '[SYSTEM]')
    
    # No exponer detalles de SQL
    sql_keywords = ['sqlite3', 'database', 'table', 'column', 'SELECT', 'INSERT']
    for keyword in sql_keywords:
        if keyword.lower() in sanitized.lower():
            return "Database error occurred"
    
    # Limitar longitud
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    
    return sanitized