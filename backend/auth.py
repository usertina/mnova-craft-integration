"""
Sistema de Autenticación JWT para CraftRMN Pro
Gestiona tokens, login, logout y verificación de sesiones
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """Gestor de autenticación JWT"""
    
    def __init__(self):
        """Inicializar con configuración desde .env"""
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY no configurada en .env")
        
        self.algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.access_token_expiration = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
        self.refresh_token_expiration = int(os.getenv('REFRESH_TOKEN_DAYS', 7))
        
        logger.info("✅ AuthManager inicializado")
        logger.info(f"   - Algoritmo: {self.algorithm}")
        logger.info(f"   - Expiración access token: {self.access_token_expiration}h")
        logger.info(f"   - Expiración refresh token: {self.refresh_token_expiration} días")
    
    def generate_access_token(self, company_id: str, device_id: str = None) -> str:
        """
        Genera un token de acceso JWT
        
        Args:
            company_id: ID de la empresa autenticada
            device_id: ID del dispositivo (opcional)
        
        Returns:
            Token JWT como string
        """
        try:
            expiration = datetime.utcnow() + timedelta(hours=self.access_token_expiration)
            
            payload = {
                'company_id': company_id,
                'device_id': device_id,
                'exp': expiration,
                'iat': datetime.utcnow(),  # Issued at
                'type': 'access'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"✅ Access token generado para empresa: {company_id}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Error generando access token: {e}")
            raise
    
    def generate_refresh_token(self, company_id: str) -> str:
        """
        Genera un refresh token (duración más larga)
        
        Args:
            company_id: ID de la empresa
        
        Returns:
            Refresh token JWT
        """
        try:
            expiration = datetime.utcnow() + timedelta(days=self.refresh_token_expiration)
            
            payload = {
                'company_id': company_id,
                'exp': expiration,
                'iat': datetime.utcnow(),
                'type': 'refresh'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"✅ Refresh token generado para empresa: {company_id}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Error generando refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> dict:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
        
        Returns:
            Payload decodificado si es válido
        
        Raises:
            jwt.ExpiredSignatureError: Token expirado
            jwt.InvalidTokenError: Token inválido
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            logger.debug(f"✅ Token verificado para empresa: {payload.get('company_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token expirado")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Token inválido: {e}")
            raise
    
    def extract_token_from_request(self) -> str:
        """
        Extrae el token JWT del header Authorization de la petición
        
        Returns:
            Token JWT o None si no existe
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        # Formato esperado: "Bearer <token>"
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning("⚠️ Formato de Authorization header inválido")
            return None
        
        return parts[1]


# Instancia global del gestor de autenticación
auth_manager = AuthManager()


def token_required(f):
    """
    Decorador para proteger endpoints que requieren autenticación
    
    Uso:
        @app.route('/api/protected')
        @token_required
        def protected_endpoint():
            # El token ya está verificado
            # Acceder a datos con: request.jwt_payload
            company_id = request.jwt_payload['company_id']
            return jsonify({'message': 'Acceso autorizado'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = auth_manager.extract_token_from_request()
        
        if not token:
            logger.warning("⚠️ Acceso denegado: No se proporcionó token")
            return jsonify({
                'error': 'Token de autenticación requerido',
                'message': 'Debes iniciar sesión para acceder a este recurso'
            }), 401
        
        try:
            # Verificar token
            payload = auth_manager.verify_token(token)
            
            # Verificar que sea un access token (no refresh)
            if payload.get('type') != 'access':
                logger.warning("⚠️ Tipo de token incorrecto")
                return jsonify({
                    'error': 'Token inválido',
                    'message': 'Debes usar un access token'
                }), 401
            
            # Guardar payload en request para acceso en la función
            request.jwt_payload = payload
            
            # Log de acceso exitoso
            logger.info(f"✅ Acceso autorizado: {payload['company_id']} -> {request.path}")
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Acceso denegado: Token expirado")
            return jsonify({
                'error': 'Token expirado',
                'message': 'Tu sesión ha expirado. Por favor, inicia sesión de nuevo.'
            }), 401
            
        except jwt.InvalidTokenError:
            logger.warning("⚠️ Acceso denegado: Token inválido")
            return jsonify({
                'error': 'Token inválido',
                'message': 'Token de autenticación no válido'
            }), 401
            
        except Exception as e:
            logger.error(f"❌ Error verificando token: {e}")
            return jsonify({
                'error': 'Error de autenticación',
                'message': 'Error al verificar el token'
            }), 500
    
    return decorated


def optional_token(f):
    """
    Decorador para endpoints que OPCIONALMENTE aceptan token
    Si hay token válido, lo verifica. Si no, continúa sin autenticación.
    
    Uso:
        @app.route('/api/public-with-optional-auth')
        @optional_token
        def public_endpoint():
            if hasattr(request, 'jwt_payload'):
                # Usuario autenticado
                company_id = request.jwt_payload['company_id']
            else:
                # Usuario anónimo
                company_id = None
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = auth_manager.extract_token_from_request()
        
        if token:
            try:
                payload = auth_manager.verify_token(token)
                request.jwt_payload = payload
                logger.debug(f"✅ Token opcional verificado: {payload['company_id']}")
            except:
                # Token inválido pero endpoint es opcional
                logger.debug("⚠️ Token opcional inválido, continuando sin auth")
                pass
        
        return f(*args, **kwargs)
    
    return decorated