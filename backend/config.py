"""
Configuración centralizada de la aplicación
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# ============================================================================
# PATHS
# ============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "storage" / "output"
ANALYSIS_DIR = SCRIPT_DIR / "storage" / "analysis"
CRAFT_EXPORTS_DIR = SCRIPT_DIR / "storage" / "craft_exports"

# Crear directorios
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
CRAFT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    raise ValueError("❌ FLASK_SECRET_KEY no configurada en .env")

GOOGLE_SCRIPT_URL = os.getenv(
    'GOOGLE_SCRIPT_URL',
    'https://script.google.com/macros/s/AKfycbynodLTTvLqqjCNhyN2y-O2U1sd7RrwaXaP-_yHGlyILXSwJoU1U6pbjlEf2DU433Js/exec'
)

ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5000'
).split(',')

# Rate Limiting
RATE_LIMIT_PER_DAY = os.getenv('RATE_LIMIT_PER_DAY', '200')
RATE_LIMIT_PER_HOUR = os.getenv('RATE_LIMIT_PER_HOUR', '50')
LOGIN_RATE_LIMIT = os.getenv('LOGIN_RATE_LIMIT', '5')
ANALYSIS_RATE_LIMIT = os.getenv('ANALYSIS_RATE_LIMIT', '20')
DOWNLOAD_RATE_LIMIT = os.getenv('DOWNLOAD_RATE_LIMIT', '30')

# JWT
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
REFRESH_TOKEN_DAYS = int(os.getenv('REFRESH_TOKEN_DAYS', 7))

# Flask
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))