"""
Rutas de autenticación (login, logout, refresh)
"""
from flask import Blueprint, jsonify, request
import logging
import os

from extensions import limiter

from auth import auth_manager, token_required
from security import InputValidator, sanitize_error_message
from audit_logger import audit_logger, get_request_ip
from company_data import COMPANY_PROFILES
from config_manager import get_config_manager

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

config = get_config_manager()


@auth_bp.route("/validate_pin", methods=["POST"])

@limiter.limit("5 per minute")

def validate_company_pin():
    """
    Valida PIN de empresa y genera tokens JWT
    """
    ip = get_request_ip()
    
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        if 'company_id' not in data or 'pin' not in data:
            return jsonify({"error": "Faltan company_id o pin"}), 400

        company_id = data.get("company_id")
        provided_pin = data.get("pin")

        # Validar formato
        if not InputValidator.validate_company_id(company_id):
            logger.warning(f"⚠️ Invalid company_id format: {company_id}")
            audit_logger.log_security_event(
                'INVALID_LOGIN_FORMAT',
                {'company_id': company_id},
                ip,
                'WARNING'
            )
            return jsonify({"error": "Invalid format"}), 400

        if not InputValidator.validate_pin(provided_pin):
            logger.warning(f"⚠️ Invalid PIN format for: {company_id}")
            audit_logger.log_security_event(
                'INVALID_PIN_FORMAT',
                {'company_id': company_id},
                ip,
                'WARNING'
            )
            return jsonify({"error": "Invalid PIN format"}), 400

        # Verificar empresa
        profile = COMPANY_PROFILES.get(company_id)
        if not profile:
            logger.warning(f"⚠️ Login attempt for non-existent company: {company_id}")
            audit_logger.log_login(company_id, False, ip, "Company not found")
            return jsonify({"error": "Invalid credentials"}), 401

        # Verificar PIN
        correct_pin = profile.get("pin")
        if not correct_pin or str(provided_pin) != str(correct_pin):
            logger.warning(f"⚠️ Wrong PIN for company: {company_id}")
            audit_logger.log_login(company_id, False, ip, "Wrong PIN")
            return jsonify({"error": "Invalid credentials"}), 401

        # Generar tokens
        try:
            device_id = config.get_device_id()
            access_token = auth_manager.generate_access_token(company_id, device_id)
            refresh_token = auth_manager.generate_refresh_token(company_id)
            
            logger.info(f"✅ Login exitoso: {company_id}")
            audit_logger.log_login(company_id, True, ip)
            
            return jsonify({
                "success": True,
                "profile": profile,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": int(os.getenv('JWT_EXPIRATION_HOURS', 24)) * 3600
            })
            
        except Exception as token_err:
            logger.error(f"❌ Error generando tokens: {token_err}", exc_info=True)
            audit_logger.log_security_event(
                'TOKEN_GENERATION_ERROR',
                {'company_id': company_id, 'error': str(token_err)},
                ip,
                'ERROR'
            )
            return jsonify({"error": "Authentication failed"}), 500

    except Exception as e:
        logger.error(f"❌ Error en validate_pin: {str(e)}", exc_info=True)
        audit_logger.log_security_event(
            'LOGIN_ERROR',
            {'error': str(e)},
            ip,
            'ERROR'
        )
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh_access_token():
    """Renueva el access token usando el refresh token"""
    try:
        data = request.json
        if not data or 'refresh_token' not in data:
            return jsonify({"error": "Refresh token requerido"}), 400
        
        refresh_token = data.get("refresh_token")
        
        try:
            import jwt
            payload = auth_manager.verify_token(refresh_token)
            
            if payload.get('type') != 'refresh':
                return jsonify({"error": "Token inválido"}), 401
            
            company_id = payload['company_id']
            device_id = config.get_device_id()
            new_access_token = auth_manager.generate_access_token(company_id, device_id)
            
            logger.info(f"✅ Access token renovado para: {company_id}")
            
            return jsonify({
                "success": True,
                "access_token": new_access_token,
                "expires_in": int(os.getenv('JWT_EXPIRATION_HOURS', 24)) * 3600
            })
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Refresh token expirado")
            return jsonify({
                "error": "Refresh token expirado",
                "message": "Debes iniciar sesión de nuevo"
            }), 401
        except jwt.InvalidTokenError:
            logger.warning("⚠️ Refresh token inválido")
            return jsonify({"error": "Refresh token inválido"}), 401
            
    except Exception as e:
        logger.error(f"❌ Error renovando token: {e}", exc_info=True)
        return jsonify({"error": "Error renovando token"}), 500


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    """Cierra sesión del usuario autenticado"""
    try:
        company_id = request.jwt_payload['company_id']
        logger.info(f"✅ Logout: {company_id}")
        
        # TODO: En producción, añadir token a blacklist
        
        return jsonify({
            "success": True,
            "message": "Sesión cerrada correctamente"
        })
        
    except Exception as e:
        logger.error(f"❌ Error en logout: {e}", exc_info=True)
        return jsonify({"error": "Error cerrando sesión"}), 500