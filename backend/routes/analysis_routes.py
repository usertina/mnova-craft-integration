"""
Rutas de análisis (analyze, history)
"""
from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
from datetime import datetime
import json
import logging
import threading

from auth import token_required
from security import FileValidator, InputValidator, sanitize_error_message
from audit_logger import audit_logger, get_request_ip
from company_data import COMPANY_PROFILES
from database import get_db
from config_manager import get_config_manager
from pfas_database import get_molecule_visualization
from utils.file_utils import extract_and_find_data
from utils.sync_utils import push_to_google_cloud
import config as app_config

analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)

db = get_db()
config = get_config_manager()


@analysis_bp.route("/analyze", methods=["POST"])
@token_required
def analyze_spectrum():
    """
    Analizar espectro con validación exhaustiva
    REQUIERE: 'file' y 'company_id' en multipart/form-data
    """
    from app import NumpyJSONEncoder, SpectrumAnalyzer
    
    ip = get_request_ip()
    
    try:
        # Validar archivo
        if "file" not in request.files:
            return jsonify({"error": "No 'file' provided"}), 400
        
        file = request.files["file"]
        
        is_valid, error_msg = FileValidator.validate_file(file)
        if not is_valid:
            logger.warning(f"⚠️ File validation failed: {error_msg}")
            audit_logger.log_security_event(
                'INVALID_FILE_UPLOAD',
                {'filename': file.filename, 'reason': error_msg},
                ip,
                'WARNING'
            )
            return jsonify({"error": error_msg}), 400
        
        # Validar company_id
        company_id = request.form.get("company_id")
        if not company_id:
            return jsonify({"error": "No 'company_id' provided"}), 400
        
        if not InputValidator.validate_company_id(company_id):
            logger.warning(f"⚠️ Invalid company_id: {company_id}")
            audit_logger.log_security_event(
                'INVALID_COMPANY_ID',
                {'company_id': company_id},
                ip,
                'WARNING'
            )
            return jsonify({"error": "Invalid company_id format"}), 400
        
        if company_id not in COMPANY_PROFILES:
            logger.warning(f"⚠️ Unknown company_id: {company_id}")
            return jsonify({"error": f"Invalid company_id: '{company_id}'"}), 400
        
        # Autorización
        token_company = request.jwt_payload.get('company_id')
        if token_company != company_id and token_company != 'ADMIN':
            logger.warning(f"⚠️ Unauthorized: {token_company} → {company_id}")
            audit_logger.log_security_event(
                'UNAUTHORIZED_ANALYSIS',
                {'token_company': token_company, 'requested_company': company_id},
                ip,
                'ERROR'
            )
            return jsonify({"error": "No autorizado"}), 403

        # Guardar archivo
        safe_filename = Path(file.filename).name
        file_path = app_config.OUTPUT_DIR / safe_filename
        file.save(file_path)
        logger.debug(f"File saved: {file_path}")

        file_path = extract_and_find_data(file_path)
        logger.debug(f"Data path: {file_path}")

        # Validar parámetros
        parameters = {}
        if "parameters" in request.form:
            try:
                parameters = json.loads(request.form["parameters"])
                
                if 'concentration' in parameters:
                    conc = float(parameters['concentration'])
                    if conc <= 0 or conc > 1000:
                        return jsonify({"error": "Invalid concentration"}), 400
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ Invalid parameters: {e}")
                return jsonify({"error": "Invalid parameters format"}), 400

        # Análisis
        analyzer = SpectrumAnalyzer()
        analysis_params = config.get_analysis_params()

        logger.info(f"📊 Analyzing: {file.filename} for {company_id}")
        results = analyzer.analyze_file(
            file_path,
            fluor_range=parameters.get("fluor_range", analysis_params.get('fluor_range')),
            pifas_range=parameters.get("pifas_range", analysis_params.get('pifas_range')),
            concentration=parameters.get("concentration", analysis_params.get('default_concentration'))
        )
        
        if not results or not isinstance(results, dict):
            logger.error("❌ Analyzer returned no results")
            audit_logger.log_analysis(company_id, file.filename, False, ip, "Invalid results")
            return jsonify({"error": "Analyzer returned no results"}), 500

        # Enriquecimiento 3D/2D
        if 'pfas_detection' in results and 'detected_pfas' in results['pfas_detection']:
            for compound in results['pfas_detection']['detected_pfas']:
                if 'confidence' in compound:
                    compound['confidence'] = round(compound['confidence'] * 100, 2)
                
                cas_number = compound.get('cas')
                molecule_viz = get_molecule_visualization(cas_number)
                
                compound['file_3d'] = molecule_viz.get('file_3d')
                compound['image_2d'] = molecule_viz.get('image_2d')

        # Guardar JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(file.filename).stem}_{company_id}_analysis_{timestamp}.json"
        result_path = app_config.ANALYSIS_DIR / result_filename
        
        try:
            with open(result_path, "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)
            logger.info(f"💾 Analysis JSON saved: {result_filename}")
        except Exception as json_err:
            logger.error(f"Failed to save JSON: {json_err}")

        # Guardar en BD
        measurement_data = {
            'device_id': config.get_device_id(),
            'company_id': company_id,
            'filename': file.filename,
            'timestamp': datetime.now().isoformat(),
            'analysis': results.copy(),
            'quality_score': results.get('quality_score'),
            'fluor_percentage': results.get('fluor_percentage'),
            'pfas_percentage': results.get('pfas_percentage'),
            'pifas_percentage': results.get('pifas_percentage'),
            'spectrum': results.get('spectrum', {}),
            'peaks': results.get('peaks', []),
            'quality_metrics': results.get('quality_metrics', {}),
        }

        measurement_id = db.save_measurement(measurement_data)
        logger.info(f"📊 Measurement saved: ID {measurement_id}")
        
        audit_logger.log_analysis(company_id, file.filename, True, ip)

        # Sincronización
        measurement_data['measurement_id_local'] = measurement_id
        
        try:
            sync_thread = threading.Thread(
                target=push_to_google_cloud,
                args=(app_config.GOOGLE_SCRIPT_URL, measurement_data, NumpyJSONEncoder, measurement_id, db)
            )
            sync_thread.start()
            logger.debug(f"🚀 Cloud sync started for {measurement_id}")
        except Exception as thread_err:
            logger.error(f"❌ Failed to start sync: {thread_err}")

        # Respuesta
        results['measurement_id'] = measurement_id
        results['result_file'] = result_filename
        results['saved_company_id'] = company_id

        return jsonify(results)

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}", exc_info=True)
        
        audit_logger.log_analysis(
            request.form.get("company_id", "unknown"),
            file.filename if 'file' in locals() else "unknown",
            False,
            ip,
            str(e)
        )
        
        return jsonify({
            "error": "Analysis failed",
            "message": sanitize_error_message(str(e))
        }), 500


@analysis_bp.route("/history", methods=["GET"])
def get_history():
    """
    Obtener historial de mediciones para una empresa
    Query Parameters: company_id, page, page_size, search
    """
    try:
        company_id = request.args.get('company_id')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        search_term = request.args.get('search', '').strip()

        if not company_id:
            return jsonify({
                "error": "Missing 'company_id' parameter",
                "measurements": [],
                "page": 1,
                "total_pages": 0,
                "total_items": 0
            }), 400

        if company_id not in COMPANY_PROFILES:
            return jsonify({
                "error": f"Invalid company_id: '{company_id}'",
                "measurements": [],
                "page": 1,
                "total_pages": 0,
                "total_items": 0
            }), 404

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        offset = (page - 1) * page_size

        if search_term:
            measurement_data = db.get_measurements_with_search(
                company_id=company_id,
                search_term=search_term,
                limit=page_size,
                offset=offset
            )
            total_count = db.count_measurements_with_search(
                company_id=company_id,
                search_term=search_term
            )
        else:
            measurement_data = db.get_measurements(
                company_id=company_id,
                limit=page_size,
                offset=offset
            )
            total_count = db.count_measurements(company_id=company_id)

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        measurements = measurement_data.get('measurements', [])

        return jsonify({
            "measurements": measurements,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_items": total_count,
            "company_id": company_id
        }), 200

    except Exception as e:
        logger.error(f"❌ Error in get_history: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Database error occurred",
            "measurements": [],
            "page": 1,
            "total_pages": 0,
            "total_items": 0
        }), 200