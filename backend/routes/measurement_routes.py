"""
Rutas de gestión de mediciones (CRUD)
"""
from flask import Blueprint, jsonify, request
import logging

from auth import token_required
from company_data import COMPANY_PROFILES
from database import get_db

measurement_bp = Blueprint('measurement', __name__)
logger = logging.getLogger(__name__)

db = get_db()


@measurement_bp.route("/measurements", methods=["GET"])
@token_required
def get_measurements():
    """
    Obtener lista de mediciones filtrada por empresa
    Query Parameters: company, page, per_page
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        company_id = request.args.get('company')

        if not company_id:
            logger.warning("get_measurements without 'company' parameter")
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if company_id not in COMPANY_PROFILES:
            logger.warning(f"Invalid company_id: {company_id}")
            return jsonify({"error": f"Invalid company ID: '{company_id}'"}), 404

        # Verificar token
        token_company = request.jwt_payload.get('company_id')
        if token_company != company_id and token_company != 'ADMIN':
            logger.warning(f"⚠️ Access denied: {token_company} → {company_id}")
            return jsonify({"error": "No autorizado"}), 403
        
        logger.debug(f"Fetching measurements: {company_id}, page {page}")

        try:
            measurement_data = db.get_measurements(
                company_id=company_id,
                limit=per_page,
                offset=(page - 1) * per_page
            )
            total_count = db.count_measurements(company_id=company_id)
            total_pages = (total_count + per_page - 1) // per_page

        except Exception as db_err:
            logger.error(f"Database error: {db_err}", exc_info=True)
            return jsonify({"error": "Database query failed"}), 500

        logger.info(f"Returning {len(measurement_data.get('measurements',[]))} measurements")

        return jsonify({
            "measurements": measurement_data.get('measurements', []),
            "page": page,
            "per_page": per_page,
            "total_items": measurement_data.get('total', 0),
            "total_pages": measurement_data.get('total_pages', 0),
            "company_id_requested": company_id
        })

    except Exception as e:
        logger.error(f"❌ Error in get_measurements: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@measurement_bp.route("/measurements/<int:measurement_id>", methods=["GET"])
@token_required
def get_measurement(measurement_id):
    """Obtener medición específica por ID"""
    try:
        requesting_company_id = request.args.get('company')
        if not requesting_company_id:
            logger.warning(f"get_measurement {measurement_id} without 'company'")
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if requesting_company_id not in COMPANY_PROFILES:
            logger.warning(f"Invalid company_id: {requesting_company_id}")
            return jsonify({"error": f"Invalid company ID"}), 404

        # Verificar token
        token_company = request.jwt_payload.get('company_id')
        if token_company != requesting_company_id and token_company != 'ADMIN':
            logger.warning(f"⚠️ Token mismatch: {token_company} vs {requesting_company_id}")
            return jsonify({"error": "Token no autorizado"}), 403

        logger.debug(f"Fetching measurement {measurement_id} for {requesting_company_id}")

        try:
            measurement = db.get_measurement(measurement_id)
        except Exception as db_err:
            logger.error(f"Database error: {db_err}", exc_info=True)
            return jsonify({"error": "Database query failed"}), 500

        if not measurement:
            logger.warning(f"Measurement {measurement_id} not found")
            return jsonify({"error": "Measurement not found"}), 404

        # Verificar pertenencia
        actual_company_id = measurement.get('company_id')
        if requesting_company_id != 'ADMIN' and actual_company_id != requesting_company_id:
            logger.warning(f"Access denied: {requesting_company_id} → {actual_company_id}")
            return jsonify({"error": "Access denied"}), 403

        logger.info(f"Returning measurement {measurement_id}")
        return jsonify(measurement)

    except Exception as e:
        logger.error(f"❌ Error in get_measurement: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@measurement_bp.route("/measurements/<int:measurement_id>", methods=["DELETE"])
@token_required
def delete_measurement(measurement_id):
    """Eliminar medición específica"""
    try:
        requesting_company_id = request.args.get('company')
        
        if not requesting_company_id:
            logger.warning(f"delete_measurement {measurement_id} without 'company'")
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if requesting_company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company ID"}), 404
        
        # Verificar token
        token_company = request.jwt_payload.get('company_id')
        if token_company != requesting_company_id and token_company != 'ADMIN':
            logger.warning(f"⚠️ Delete denied: {token_company} vs {requesting_company_id}")
            return jsonify({"error": "Token no autorizado"}), 403

        logger.debug(f"Delete request: measurement {measurement_id} by {requesting_company_id}")
        
        success = db.delete_measurement(measurement_id, requesting_company_id)
        
        if success:
            logger.info(f"Measurement {measurement_id} deleted by {requesting_company_id}")
            return jsonify({
                "message": f"Measurement {measurement_id} deleted successfully"
            }), 200
        else:
            logger.warning(f"Measurement {measurement_id} not found or access denied")
            return jsonify({"error": "Measurement not found or access denied"}), 404
            
    except Exception as e:
        logger.error(f"Error deleting measurement {measurement_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to delete measurement: {str(e)}"}), 500


@measurement_bp.route("/measurements/clear-all", methods=["DELETE"])
def clear_all_measurements():
    """Eliminar todas las mediciones de una empresa"""
    try:
        company_id = request.args.get('company')
        
        if not company_id:
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company ID"}), 404
        
        logger.warning(f"Clear all measurements: {company_id}")
        
        deleted_count = db.delete_all_measurements(company_id)
        
        logger.info(f"Deleted {deleted_count} measurements for {company_id}")
        
        return jsonify({
            "message": f"Deleted {deleted_count} measurements",
            "deleted_count": deleted_count,
            "company_id": company_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing measurements: {e}", exc_info=True)
        return jsonify({"error": f"Failed to clear measurements: {str(e)}"}), 500