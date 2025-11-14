"""
Rutas del frontend (static files, health check)
"""
from flask import Blueprint, jsonify, send_from_directory
from datetime import datetime
import logging

frontend_bp = Blueprint('frontend', __name__)
logger = logging.getLogger(__name__)


@frontend_bp.route('/')
def home():
    """Servir index.html (Portal de Login)"""
    from flask import current_app
    return send_from_directory(current_app.static_folder, "index.html")


@frontend_bp.route('/app.html')
def main_app():
    """Servir app.html (Aplicación principal)"""
    from flask import current_app
    return send_from_directory(current_app.static_folder, "app.html")


@frontend_bp.route('/<path:path>')
def static_proxy(path):
    """Servir archivos estáticos (JS, CSS, imágenes)"""
    from flask import current_app
    
    if path in ["index.html", "app.html"]:
        return home()
    
    try:
        return send_from_directory(current_app.static_folder, path)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


@frontend_bp.route("/api/health", methods=["GET"])
def health_check():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "ok",
        "message": "CraftRMN Analysis Server Running (Multi-Empresa)",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })