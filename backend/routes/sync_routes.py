"""
Rutas de sincronización (admin only)
(VERSIÓN CORREGIDA - Usa db.get_connection())
"""
from flask import Blueprint, jsonify, request
import logging
import json
import threading

from auth import token_required
from database import get_db
from utils.sync_utils import push_to_google_cloud
import config as app_config

sync_bp = Blueprint('sync', __name__)
logger = logging.getLogger(__name__)

db = get_db()


@sync_bp.route("/sync/status", methods=["GET"])
@token_required
def sync_status():
    """
    Muestra estado de sincronización (admin only)
    """
    # --- INICIO DE LA CORRECCIÓN ---
    conn = None # Inicializa la conexión como nula
    try:
        if request.jwt_payload.get('company_id') != 'ADMIN':
            return jsonify({"error": "Solo admin puede ver estado"}), 403
        
        # 1. Obtener una conexión desde el objeto db
        conn = db.get_connection()
        cursor = conn.cursor()
    # --- FIN DE LA CORRECCIÓN (parcial) ---
        
        # Total
        cursor.execute("SELECT COUNT(*) FROM measurements")
        total = cursor.fetchone()[0]
        
        # Sincronizados
        cursor.execute("SELECT COUNT(*) FROM measurements WHERE synced = 1")
        synced = cursor.fetchone()[0]
        
        pending = total - synced
        
        # Última sincronización (tu corrección anterior ya estaba bien)
        cursor.execute("""
            SELECT last_sync_attempt FROM measurements 
            WHERE synced = 1 
            ORDER BY last_sync_attempt DESC 
            LIMIT 1
        """)
        last_sync_row = cursor.fetchone()
        last_sync = last_sync_row[0] if last_sync_row else None
        
        # Pendientes por empresa
        cursor.execute("""
            SELECT company_id, COUNT(*) as count
            FROM measurements
            WHERE synced = 0
            GROUP BY company_id
        """)
        pending_by_company = {row[0]: row[1] for row in cursor.fetchall()}
        
        return jsonify({
            "total_measurements": total,
            "synced": synced,
            "pending": pending,
            "sync_rate": f"{(synced/total*100):.1f}%" if total > 0 else "0%",
            "last_sync": last_sync,
            "pending_by_company": pending_by_company
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
    # --- INICIO DE LA CORRECCIÓN (final) ---
    finally:
        # 2. Asegurarse de cerrar la conexión
        if conn:
            conn.close()
    # --- FIN DE LA CORRECCIÓN ---


@sync_bp.route("/sync/retry", methods=["POST"])
@token_required
def retry_sync():
    """
    Reintenta sincronizar mediciones pendientes (admin only)
    """
    from app import NumpyJSONEncoder
    
    try:
        if request.jwt_payload.get('company_id') != 'ADMIN':
            return jsonify({"error": "Solo admin puede forzar sync"}), 403
        
        # Esta función usa el método de alto nivel db.get_pending_sync(),
        # que ya maneja su propia conexión, así que está bien.
        pending = db.get_pending_sync(limit=50) 
        
        if not pending:
            return jsonify({
                "message": "No hay mediciones pendientes",
                "synced_count": 0
            })
        
        # Reintentar cada una
        success_count = 0
        for measurement in pending:
            # Esta lógica está bien
            measurement_data = {
                'device_id': measurement['device_id'],
                'company_id': measurement['company_id'],
                'filename': measurement['filename'],
                'timestamp': measurement['timestamp'],
                'analysis': measurement.get('analysis', {}), # Usar .get() para seguridad
                'spectrum': measurement.get('spectrum', {}),
                'peaks': measurement.get('peaks', []),
                'quality_score': measurement.get('quality_score'),
                'fluor_percentage': measurement.get('fluor_percentage'),
                'pfas_percentage': measurement.get('pfas_percentage'),
                'quality_metrics': measurement.get('analysis', {}).get('quality_metrics', {}), # Extraer de analysis
                'measurement_id_local': measurement['id']
            }
            
            thread = threading.Thread(
                target=push_to_google_cloud,
                args=(app_config.GOOGLE_SCRIPT_URL, measurement_data, NumpyJSONEncoder, measurement['id'], db)
            )
            thread.start()
            success_count += 1
        
        return jsonify({
            "message": f"Sincronización iniciada para {success_count} mediciones",
            "synced_count": success_count,
            "pending_count": len(pending)
        })
        
    except Exception as e:
        logger.error(f"❌ Error en retry_sync: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500