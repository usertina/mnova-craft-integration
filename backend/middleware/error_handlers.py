"""
Error handlers centralizados
"""
from flask import jsonify
import logging
from security import sanitize_error_message

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Registra todos los error handlers en la app"""
    
    @app.errorhandler(400)
    def bad_request(error):  # type: ignore
        return jsonify({
            "error": "Bad request",
            "message": sanitize_error_message(str(error))
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):  # type: ignore
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication required"
        }), 401

    @app.errorhandler(403)
    def forbidden(error):  # type: ignore
        return jsonify({
            "error": "Forbidden",
            "message": "Access denied"
        }), 403

    @app.errorhandler(404)
    def not_found(error):  # type: ignore
        return jsonify({
            "error": "Not found",
            "message": "Resource not found"
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):  # type: ignore
        return jsonify({
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": error.description
        }), 429

    @app.errorhandler(500)
    def internal_error(error):  # type: ignore
        logger.error(f"Internal error: {error}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }), 500