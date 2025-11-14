"""
Utilidades de sincronización con Google Sheets
"""
import json
import logging
import requests
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


def push_to_google_cloud(
    url: str,
    payload: dict,
    encoder: Any,
    measurement_id: int,
    db_instance: Any,
    retries: int = 3,
    delay: int = 5,
    timeout: float = 30.0
):
    """
    Envía datos a Google Apps Script con reintentos.
    
    Args:
        url: URL del Google Apps Script
        payload: Datos a enviar
        encoder: JSON encoder (NumpyJSONEncoder)
        measurement_id: ID de la medición
        db_instance: Instancia de Database
        retries: Número de reintentos
        delay: Segundos entre reintentos
        timeout: Timeout de la request
    """
    def _push():
        json_payload = json.dumps(payload, cls=encoder)

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    url,
                    data=json_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=timeout
                )
                response.raise_for_status()

                # Marcar como sincronizado
                if db_instance.mark_as_synced(measurement_id):
                    logger.info(f"☁️ ✅ Measurement {measurement_id} synced (Attempt {attempt})")
                    return True
                else:
                    logger.error(f"❌ Error marcando {measurement_id} como sincronizado")
                    return False

            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Sync attempt {attempt}/{retries} failed for ID {measurement_id}: {e}")

                if attempt < retries:
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Failed to sync measurement {measurement_id} after {retries} attempts")
                    return False

    # Ejecutar en thread separado
    thread = threading.Thread(target=_push)
    thread.daemon = True
    thread.start()


def automatic_retry_job(db_instance: Any, google_script_url: str, encoder: Any):
    """
    Job del scheduler para reintentar sincronizaciones pendientes.
    
    Args:
        db_instance: Instancia de Database
        google_script_url: URL del Google Apps Script
        encoder: JSON encoder
    """
    logger.info("⚙️ [Scheduler] Ejecutando trabajo de reintento automático...")
    
    try:
        pending = db_instance.get_pending_sync(limit=20)
        
        if not pending:
            logger.info("⚙️ [Scheduler] No hay mediciones pendientes.")
            return

        logger.warning(f"⚙️ [Scheduler] {len(pending)} mediciones pendientes. Reintentando...")
        
        for measurement in pending:
            measurement['measurement_id_local'] = measurement['id']
            
            thread = threading.Thread(
                target=push_to_google_cloud,
                args=(google_script_url, measurement, encoder, measurement['id'], db_instance)
            )
            thread.start()
            time.sleep(1)  # Evitar saturación
    
    except Exception as e:
        logger.error(f"❌ [Scheduler] Error en reintento: {e}", exc_info=True)