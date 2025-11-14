"""
Rutas de configuración (activate, get/update config)
"""
from flask import Blueprint, jsonify, request
import logging

from config_manager import get_config_manager, LicenseValidator
from company_data import COMPANY_PROFILES

config_bp = Blueprint('config', __name__)
logger = logging.getLogger(__name__)

config = get_config_manager()


@config_bp.route("/activate", methods=["POST"])
def activate_device():
    """Activa el dispositivo usando licencia de ADMIN"""
    try:
        data = request.json
        if not data or 'license_key' not in data:
            return jsonify({"error": "Missing 'license_key'"}), 400

        license_key = data.get("license_key", "").strip()
        if not license_key:
            return jsonify({"error": "No license key provided"}), 400

        logger.debug(f"Activation request: {license_key[:15]}...")

        validator = LicenseValidator()
        device_id = config.get_device_id()

        if validator.validate_license(license_key, device_id):
            logger.info("Admin license validated")
            success = config.activate_device(license_key)

            if success:
                logger.info(f"Device {device_id} activated")
                return jsonify({
                    "message": "Device activated successfully",
                    "device_id": device_id
                })
            else:
                logger.error("Failed to save activation state")
                return jsonify({"error": "Failed to save activation"}), 500
        else:
            logger.warning(f"Invalid license for device {device_id}")
            return jsonify({"error": "Invalid license key"}), 403

    except Exception as e:
        logger.error(f"❌ Error during activation: {str(e)}", exc_info=True)
        return jsonify({"error": f"Activation failed: {str(e)}"}), 500


@config_bp.route("/config", methods=["GET"])
def get_config():
    """Obtener configuración del dispositivo"""
    try:
        visible_companies = [
            profile for key, profile in COMPANY_PROFILES.items() if key != 'ADMIN'
        ]

        if not isinstance(visible_companies, list):
            logger.error(f"visible_companies is not a list: {type(visible_companies)}")
            visible_companies = []

        logger.debug(f"Config: activated={config.is_activated()}, companies={len(visible_companies)}")

        return jsonify({
            "device_id": config.get_device_id(),
            "activated": config.is_activated(),
            "analysis_params": config.get_analysis_params(),
            "available_companies": visible_companies
        })
    except Exception as e:
        logger.error(f"❌ Error getting config: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to get configuration: {str(e)}"}), 500


@config_bp.route("/config", methods=["POST"])
def update_config():
    """Actualizar parámetros de configuración"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400

        updated_any = False
        response_config = {}

        if 'analysis_params' in data and isinstance(data['analysis_params'], dict):
            config.update_analysis_params(data['analysis_params'])
            logger.info(f"Analysis parameters updated: {data['analysis_params']}")
            response_config['analysis_params'] = config.get_analysis_params()
            updated_any = True

        if not updated_any:
            return jsonify({"message": "No valid parameters to update"}), 400

        return jsonify({
            "message": "Configuration updated successfully",
            "updated_config": response_config
        })

    except Exception as e:
        logger.error(f"❌ Error updating config: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to update configuration: {str(e)}"}), 500


@config_bp.route("/company_profile", methods=["GET"])
def get_company_profile():
    """Obtiene perfil de empresa específico por ID"""
    company_id = request.args.get('id')
    if not company_id:
        logger.warning("get_company_profile without 'id' parameter")
        return jsonify({"error": "Missing 'id' parameter"}), 400

    profile = COMPANY_PROFILES.get(company_id)

    if not profile:
        logger.warning(f"Company profile not found: {company_id}")
        return jsonify({"error": "Company profile not found"}), 404

    logger.debug(f"Returning profile for: {company_id}")
    return jsonify(profile)