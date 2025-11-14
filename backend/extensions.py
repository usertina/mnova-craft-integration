from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

"""
Inicializa extensiones de Flask para evitar importaciones circulares.
"""

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True
)