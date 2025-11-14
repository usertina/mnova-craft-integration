"""
CraftRMN Pro - Aplicación Principal
"""
import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np

from extensions import limiter

# Configuración
import config

# Componentes locales
from database import get_db
from config_manager import get_config_manager
from auth import auth_manager
from security import add_security_headers, log_request, check_csrf_token
from middleware.error_handlers import register_error_handlers
from utils.sync_utils import automatic_retry_job

# Importar analizador
try:
    sys.path.append(str(Path(__file__).parent.parent / "worker"))
    from analyzer import SpectrumAnalyzer
except ImportError:
    logging.error("No se pudo importar SpectrumAnalyzer")
    class SpectrumAnalyzer:
        def analyze_file(self, *args, **kwargs):
            return {"error": "Analyzer module not found"}

# ============================================================================
# CONFIGURACIÓN LOGGING
# ============================================================================
logging.getLogger().setLevel(logging.DEBUG)

# ============================================================================
# JSON ENCODER
# ============================================================================
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, np.bool_): return bool(obj)
        return super().default(obj)

# ============================================================================
# INICIALIZAR FLASK
# ============================================================================
app = Flask(__name__, static_folder="../frontend")
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.json_encoder = NumpyJSONEncoder

# Componentes globales
db = get_db()
config_manager = get_config_manager()

# ============================================================================
# MIDDLEWARE
# ============================================================================
@app.before_request
def security_checks():
    """Checks de seguridad antes de cada request"""
    log_request()
    check_csrf_token()

@app.after_request
def apply_security_headers_middleware(response):
    """Aplica headers de seguridad"""
    return add_security_headers(response)

# Registrar error handlers
register_error_handlers(app)

# ============================================================================
# CORS
# ============================================================================
CORS(app, resources={
    r"/api/*": {
        "origins": config.ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600,
        "supports_credentials": True
    }
})

logging.info(f"✅ CORS configurado: {config.ALLOWED_ORIGINS}")

# ============================================================================
# RATE LIMITING
# ============================================================================
limiter.init_app(app) # Inicializa el limiter con la app

logging.info("✅ Rate Limiting configurado")

# ============================================================================
# REGISTRAR BLUEPRINTS
# ============================================================================
from routes.frontend_routes import frontend_bp
from routes.auth_routes import auth_bp
from routes.analysis_routes import analysis_bp
from routes.config_routes import config_bp
from routes.measurement_routes import measurement_bp
from routes.export_routes import export_bp
from routes.sync_routes import sync_bp

app.register_blueprint(frontend_bp)
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(analysis_bp, url_prefix='/api')
app.register_blueprint(config_bp, url_prefix='/api')
app.register_blueprint(measurement_bp, url_prefix='/api')
app.register_blueprint(export_bp, url_prefix='/api')
app.register_blueprint(sync_bp, url_prefix='/api')

logging.info("✅ Blueprints registrados")

# ============================================================================
# SERVIDOR WERKZEUG - OCULTAR INFO
# ============================================================================
try:
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.server_version = "CraftRMN"
    WSGIRequestHandler.sys_version = "2.0"
    logging.info("✅ Server header personalizado")
except Exception as e:
    logging.warning(f"⚠️ No se pudo personalizar Server header: {e}")

# ============================================================================
# SCHEDULER
# ============================================================================
def init_scheduler():
    """Inicializa el scheduler para reintentos automáticos"""
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        lambda: automatic_retry_job(db, config.GOOGLE_SCRIPT_URL, NumpyJSONEncoder),
        'interval',
        hours=6
    )
    scheduler.start()
    logging.info("✅ Scheduler iniciado (cada 6 horas)")

# ============================================================================
# STARTUP
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CraftRMN Analysis Server (Multi-Empresa)")
    print("=" * 60)
    print(f"📊 Version: 2.0.0 (Security Enhanced)")
    print(f"🌐 Running on: http://localhost:{config.FLASK_PORT}")
    print(f"📁 Storage: {config.SCRIPT_DIR / 'storage'}")
    print("=" * 60)
    
    # Iniciar scheduler (solo en modo producción o main process)
    if not config.FLASK_DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_scheduler()
    
    # Validar configuración
    if config.FLASK_DEBUG and config.FLASK_ENV == 'production':
        raise ValueError("No se puede usar debug=True en producción")
    
    # Iniciar servidor
    if config.FLASK_ENV == 'production':
        logging.info("🚀 Modo PRODUCCIÓN")
        try:
            from waitress import serve
            serve(app, host=config.FLASK_HOST, port=config.FLASK_PORT, threads=4)
        except ImportError:
            logging.warning("⚠️ Waitress no instalado, usando Werkzeug")
            app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
    else:
        logging.info("🔧 Modo DESARROLLO")
        app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)