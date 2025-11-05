import csv
from fileinput import filename
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from pathlib import Path
import os
import json
import sys
from datetime import datetime
from io import BytesIO, StringIO
import traceback
from export_utils import ReportExporter
import numpy as np
import logging
import requests
import threading

from pfas_database import get_molecule_visualization

# Importar dependencias locales
from database import get_db
from config_manager import get_config_manager, LicenseValidator
from company_data import COMPANY_PROFILES # Importar perfiles de empresa

# Configurar logging (activar DEBUG para ver todo)
logging.getLogger().setLevel(logging.DEBUG)


# Inicializar componentes
db = get_db()
config = get_config_manager()

# Importar el analizador (asumiendo que está en ../worker)
try:
    sys.path.append(str(Path(__file__).parent.parent / "worker"))
    from analyzer import SpectrumAnalyzer
except ImportError:
    logging.error("No se pudo importar SpectrumAnalyzer desde ../worker. Asegúrate de que la ruta es correcta.")
    # Podrías definir una clase 'dummy' o salir si es crítico
    class SpectrumAnalyzer: # Dummy class para evitar errores si no se encuentra
        def analyze_file(self, *args, **kwargs):
            logging.error("SpectrumAnalyzer real no encontrado.")
            return {"error": "Analyzer module not found"}

# ============================================================================
# Codificador JSON para NumPy
# ============================================================================
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, np.bool_): return bool(obj)
        else: return super(NumpyJSONEncoder, self).default(obj)

# ============================================================================
# Configuración de Flask
# ============================================================================
app = Flask(__name__, static_folder="../frontend")
CORS(app)
app.json_encoder = NumpyJSONEncoder

# Anclar las rutas de almacenamiento al directorio de este script
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "storage" / "output"
ANALYSIS_DIR = SCRIPT_DIR / "storage" / "analysis"
CRAFT_EXPORTS_DIR = SCRIPT_DIR / "storage" / "craft_exports"

# Crear directorios si no existen
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
CRAFT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Mensaje de inicio
print("=" * 60)
print("🚀 CraftRMN Analysis Server (Multi-Empresa)")
print("=" * 60)
print(f"📊 Version: 2.0.0") # Versión actualizada
print(f"🌐 Running on: http://localhost:5000")
print(f"📁 Storage Base: {SCRIPT_DIR / 'storage'}")
print(f"   Output: {OUTPUT_DIR}")
print(f"   Analysis: {ANALYSIS_DIR}")
print(f"   Craft Exports: {CRAFT_EXPORTS_DIR}")
print("=" * 60)

# ============================================================================
# FRONTEND - Servir archivos estáticos (index.html, app.html, js/, styles/, etc.)
# ============================================================================

@app.route('/')
def home():
    # Servir index.html (Portal de Activación/Login)
    return send_from_directory(app.static_folder, "index.html")

@app.route('/app.html') # Ruta específica para la app principal
def main_app():
     return send_from_directory(app.static_folder, "app.html")

@app.route('/<path:path>')
def static_proxy(path):
    # Servir cualquier otro archivo estático (JS, CSS, imágenes)
    # Evitar que sirva index.html en rutas desconocidas si queremos separar app.html
    if path == "index.html" or path == "app.html":
        # Redirigir a la raíz si intentan acceder directamente
        # o manejar según prefieras
        return home() # Opcional: redirigir a '/' siempre
    try:
        # Servir el archivo solicitado (ej: styles/main.css, js/app.js)
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
         # Si no se encuentra, podrías devolver un 404 o redirigir
         # Devolver 404 es más estándar para APIs RESTful
         return jsonify({"error": "File not found"}), 404
         # O redirigir a home si prefieres comportamiento SPA tradicional
         # return home()

# ============================================================================
# API - Health Check
# ============================================================================
@app.route("/api/health", methods=["GET"])
def health_check():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "ok",
        "message": "CraftRMN Analysis Server Running (Multi-Empresa)",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# FUNCIÓN DE SINCRONIZACIÓN EN LA NUBE
# ============================================================================

def push_to_google_cloud(url, payload, encoder):
    """
    Intenta enviar datos a la URL de Google Apps Script en un hilo separado
    y comprueba la respuesta para asegurar que fue exitosa.
    """
    try:
        # Convertimos los datos a JSON usando el codificador de Numpy
        json_payload = json.dumps(payload, cls=encoder)
        
        # Hacemos el POST. timeout=10.0 (10 segundos)
        response = requests.post(
            url, 
            data=json_payload, 
            headers={'Content-Type': 'application/json'}, 
            timeout=10.0
        )
        
        # --- ¡LA MEJORA CLAVE ESTÁ AQUÍ! ---
        # Esto revisará si la respuesta de Google fue un error (como 403, 404, 500)
        # Si fue un error, saltará automáticamente al 'except' de abajo.
        response.raise_for_status()
        
        # Si llegamos aquí, la respuesta fue exitosa (ej. 200 OK)
        logging.info(f"  ☁️  Measurement pushed to Google Cloud successfully. (Status: {response.status_code})")
    
    except requests.exceptions.HTTPError as http_err:
        # Captura errores específicos de HTTP (ej. 403 Prohibido, 404 No Encontrado)
        # Esto es lo que te pasó a ti (HTTP 403)
        logging.error(f"  ❌  HTTP Error pushing to cloud. Google respondió: {http_err}")
        
    except Exception as cloud_err:
        # Captura otros errores (ej. sin internet, timeout, URL mal escrita)
        logging.warning(f"  ⚠️  Failed to push measurement to cloud (Network/Timeout): {str(cloud_err)}")

# ============================================================================
# API - Análisis de Espectros
# ============================================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_spectrum():
    """
    Analizar un único espectro.
    REQUIERE: 'file' y 'company_id' en el formulario multipart/form-data.
    """
    try:
        # Verificar archivo
        if "file" not in request.files:
            return jsonify({"error": "No 'file' provided in the request"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # Verificar company_id
        company_id = request.form.get("company_id")
        if not company_id:
            return jsonify({"error": "No 'company_id' provided in the form data"}), 400
        if company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company_id: '{company_id}'"}), 400

        logging.debug(f"Received analysis request for company: {company_id}, file: {file.filename}")

        # Guardar archivo temporalmente
        file_path = OUTPUT_DIR / file.filename
        file.save(file_path)
        logging.debug(f"File saved temporarily to: {file_path}")

        # Obtener parámetros opcionales
        parameters = {}
        if "parameters" in request.form:
            try:
                parameters = json.loads(request.form["parameters"])
            except json.JSONDecodeError:
                logging.warning("Invalid JSON in 'parameters' field.")
                # Seguir con parámetros por defecto

        # Realizar análisis
        analyzer = SpectrumAnalyzer()
        analysis_params = config.get_analysis_params() # Obtener defaults del ConfigManager

        logging.info(f"📊 Analyzing: {file.filename} for company {company_id}")
        results = analyzer.analyze_file(
            file_path,
            fluor_range=parameters.get("fluor_range", analysis_params.get('fluor_range')),
            pifas_range=parameters.get("pifas_range", analysis_params.get('pifas_range')),
            concentration=parameters.get("concentration", analysis_params.get('default_concentration'))
        )
        # Validar que results sea un dict
        if not results or not isinstance(results, dict):
            logging.error("❌ Analyzer returned no results or invalid format.")
            return jsonify({"error": "Analyzer returned no results"}), 500
        
        # Corregido el error 'unhashable type: dict'
        logging.debug(f"Analysis raw results: {results}")

        # --- INICIO DEL ENRIQUECIMIENTO 3D/2D ---
        logging.info("  🧬  Enriqueciendo lista de compuestos con datos 2D/3D...")

        if 'pfas_detection' in results and 'compounds' in results['pfas_detection']:
            for compound in results['pfas_detection']['compounds']:
                cas_number = compound.get('cas')
                molecule_viz = get_molecule_visualization(cas_number)  # ✅ Cambio de nombre
                
                # ✅ Siempre asignar (puede ser None si no existe)
                compound['file_3d'] = molecule_viz.get('file_3d')
                compound['image_2d'] = molecule_viz.get('image_2d')
                
                # ✅ Verificar si encontró ALGÚN archivo
                if molecule_viz.get('file_3d') or molecule_viz.get('image_2d'):
                    logging.debug(f"     -> Añadidos datos 2D/3D para {cas_number}: {molecule_viz['name']}")
                else:
                    logging.warning(f"     -> No se encontraron datos 2D/3D para CAS: {cas_number}")

        # --- FIN DEL ENRIQUECIMIENTO 3D/2D ---
        
        # GUARDAR EN JSON (Opcional, pero útil para debug)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(file.filename).stem}_{company_id}_analysis_{timestamp}.json"
        result_path = ANALYSIS_DIR / result_filename
        try:
            with open(result_path, "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2, cls=NumpyJSONEncoder, ensure_ascii=False)
            logging.info(f"  💾 Analysis JSON saved: {result_filename}")
        except Exception as json_err:
            logging.error(f"Failed to save analysis JSON {result_filename}: {json_err}")

        
        # --- ¡¡¡INICIO DE LA CORRECCIÓN DE GUARDADO EN BD!!! ---
        
        # 1. Obtenemos el diccionario 'analysis' base
        # (Usamos .copy() para no modificar el objeto 'results' original)
        analysis_data_to_save = results.get('analysis', {}).copy()
        
        # 2. Le añadimos la lista de compuestos detectados
        if 'pfas_detection' in results:
            analysis_data_to_save['pfas_detection'] = results['pfas_detection']
            
        # 3. Le añadimos el S/N (que está en el nivel raíz de 'results')
        if 'signal_to_noise' in results:
            analysis_data_to_save['signal_to_noise'] = results['signal_to_noise']
        
        # 4. Le añadimos el desglose de calidad (si existe)
        if 'quality_breakdown' in results:
            analysis_data_to_save['quality_breakdown'] = results['quality_breakdown']

        # GUARDAR EN SQLITE
        measurement_data = {
            'device_id': config.get_device_id(),
            'company_id': company_id,
            'filename': file.filename,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis_data_to_save, # <-- ¡USAMOS EL OBJETO CORREGIDO!
            'quality_score': results.get('quality_score'),
            'spectrum': results.get('spectrum', {}), 
            'peaks': results.get('peaks', []),
            'quality_metrics': results.get('quality_metrics', {}),
        }
        measurement_id = db.save_measurement(measurement_data)
        logging.info(f"  📊 Measurement saved to DB. ID: {measurement_id} for Company: {company_id}")
        
        # --- ¡¡¡FIN DE LA CORRECCIÓN!!! ---


        GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbynodLTTvLqqjCNhyN2y-O2U1sd7RrwaXaP-_yHGlyILXSwJoU1U6pbjlEf2DU433Js/exec"

        # Añadimos el ID a los datos que enviaremos
        measurement_data['measurement_id_local'] = measurement_id

        # Llamamos a nuestra nueva función en un hilo (segundo plano)
        try:
            sync_thread = threading.Thread(
                target=push_to_google_cloud,
                args=(GOOGLE_SCRIPT_URL, measurement_data, NumpyJSONEncoder)
            )
            sync_thread.start() # Inicia el envío
            logging.debug("  🚀  Cloud sync thread started.")
        except Exception as thread_err:
            logging.error(f"  ❌  Failed to start cloud sync thread: {thread_err}")


        results['measurement_id'] = measurement_id
        results['result_file'] = result_filename
        results['saved_company_id'] = company_id

        if not isinstance(results, dict):
            logging.error("❌ Final results object is not a dictionary.")
            return jsonify({"error": "Invalid results format"}), 500

        return jsonify(results)


    except Exception as e:
        logging.error(f"❌ Error during analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
        }), 500
    finally:
        if 'file_path' in locals() and file_path.exists():
            try:
                # os.remove(file_path)
                # logging.debug(f"Temporary file removed: {file_path}")
                pass
            except Exception as rm_err:
                logging.error(f"Failed to remove temporary file {file_path}: {rm_err}")
                                 
# ============================================================================
# API - Activación y Configuración del Dispositivo
# ============================================================================
@app.route("/api/activate", methods=["POST"])
def activate_device():
    """
    Activa el dispositivo (modo Admin) usando la licencia de ADMIN.
    """
    try:
        data = request.json
        if not data or 'license_key' not in data:
             return jsonify({"error": "Request body must be JSON with 'license_key'"}), 400

        license_key = data.get("license_key", "").strip()
        if not license_key:
            return jsonify({"error": "No license key provided"}), 400

        logging.debug(f"Received activation request with key: {license_key[:15]}...") # No loguear clave completa

        validator = LicenseValidator()
        device_id = config.get_device_id()

        # Validar la licencia (debe ser la de ADMIN)
        if validator.validate_license(license_key, device_id):
            logging.info("Admin license validated successfully.")
            # Llamar a la función de activación en ConfigManager
            success = config.activate_device(license_key) # activate_device ahora solo marca como activado

            if success:
                logging.info(f"Device {device_id} activated successfully (Admin Mode).")
                return jsonify({
                    "message": "Device activated successfully (Admin Mode)",
                    "device_id": device_id
                })
            else:
                logging.error("Failed to save activation state in database.")
                return jsonify({"error": "Failed to save activation state"}), 500
        else:
            # La licencia no es válida o no es la de ADMIN
            logging.warning(f"Invalid or incorrect admin license key provided for device {device_id}.")
            return jsonify({"error": "Invalid or incorrect admin license key"}), 403

    except Exception as e:
        logging.error(f"❌ Error during activation: {str(e)}", exc_info=True)
        return jsonify({"error": f"Activation failed: {str(e)}"}), 500

@app.route("/api/config", methods=["GET"])
def get_config_endpoint(): # Renombrado para evitar conflicto con variable 'config'
    """
    Obtener configuración del dispositivo para el frontend.
    Devuelve estado de activación, device_id y LISTA de empresas disponibles (sin admin).
    """
    try:
        # Crear la lista de empresas VISIBLES (excluyendo 'admin')
        visible_companies = [ # <--- !!! CORRECCIÓN: Usar [] para crear LISTA !!!
            profile for key, profile in COMPANY_PROFILES.items() if key != 'admin'
        ]

        # Comprobar si realmente es una lista (para depuración extra)
        if not isinstance(visible_companies, list):
             logging.error(f"CRITICAL: visible_companies is NOT a list! Type: {type(visible_companies)}")
             # Forzar una lista vacía o devolver error
             visible_companies = []
             # Considerar devolver un error 500 aquí si esto no debería pasar nunca

        logging.debug(f"Sending config: activated={config.is_activated()}, companies={len(visible_companies)}")

        return jsonify({
            "device_id": config.get_device_id(),
            "activated": config.is_activated(),
            "analysis_params": config.get_analysis_params(),
            "available_companies": visible_companies # <-- Devolver la LISTA
        })
    except Exception as e:
        logging.error(f"❌ Error getting config: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to get configuration: {str(e)}"}), 500

# ============================================================================
# API - Historial de Análisis (usado por el frontend)
# ============================================================================
@app.route("/api/history", methods=["GET"])
def get_history():
    """
    Obtener historial de mediciones para una empresa específica.
    Compatible con el frontend que usa 'company_id' en los parámetros.
    
    Query Parameters:
        - company_id (required): ID de la empresa
        - page (optional): Número de página (default: 1)
        - page_size (optional): Elementos por página (default: 50)
        - search (optional): Término de búsqueda
    """
    try:
        # Obtener parámetros de la URL
        company_id = request.args.get('company_id')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        search_term = request.args.get('search', '').strip()

        # Validar company_id (requerido)
        if not company_id:
            logging.warning("get_history called without 'company_id' parameter.")
            return jsonify({
                "error": "Missing 'company_id' parameter",
                "measurements": [],
                "page": 1,
                "total_pages": 0,
                "total_items": 0
            }), 400

        # Validar que la empresa existe
        if company_id not in COMPANY_PROFILES:
            logging.warning(f"get_history called with invalid company_id: {company_id}")
            return jsonify({
                "error": f"Invalid company_id: '{company_id}'",
                "measurements": [],
                "page": 1,
                "total_pages": 0,
                "total_items": 0
            }), 404

        # Validar paginación
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        logging.debug(
            f"Fetching history for company '{company_id}', "
            f"page {page}, page_size {page_size}, search: '{search_term}'"
        )

        # Consultar la base de datos
        try:
            # Calcular offset
            offset = (page - 1) * page_size

            # Obtener mediciones (con o sin búsqueda)
            if search_term:
                # Si hay búsqueda, filtrar por filename o sample_name
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
                # Sin búsqueda, obtener todos
                measurement_data = db.get_measurements(
                    company_id=company_id,
                    limit=page_size,
                    offset=offset
                )
                total_count = db.count_measurements(company_id=company_id)

            # Calcular total de páginas
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

            # Obtener las mediciones del resultado
            measurements = measurement_data.get('measurements', [])

            logging.info(
                f"Returning {len(measurements)} measurements for company '{company_id}' "
                f"(page {page}/{total_pages}, total: {total_count})"
            )

            # Devolver respuesta exitosa
            return jsonify({
                "measurements": measurements,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_items": total_count,
                "company_id": company_id
            }), 200

        except Exception as db_err:
            # Error de base de datos
            logging.error(
                f"Database error in get_history for {company_id}: {db_err}",
                exc_info=True
            )
            # Devolver respuesta con arrays vacíos en lugar de error 500
            return jsonify({
                "error": "Database error occurred",
                "measurements": [],
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "total_items": 0,
                "company_id": company_id
            }), 200  # ✅ Usar 200 para no bloquear la app

    except Exception as e:
        # Error inesperado del endpoint
        logging.error(f"❌ Unexpected error in get_history: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An unexpected server error occurred",
            "measurements": [],
            "page": 1,
            "total_pages": 0,
            "total_items": 0
        }), 200  # ✅ Usar 200 para no bloquear la app


# ENDPOINT NUEVO: Obtener perfil de empresa específico
@app.route("/api/company_profile", methods=["GET"])
def get_company_profile():
    """
    Obtiene el perfil (branding) de una empresa específica por su ID.
    Usado por el frontend después de la selección para aplicar branding.
    """
    company_id = request.args.get('id')
    if not company_id:
        logging.warning("get_company_profile called without 'id' parameter.")
        return jsonify({"error": "Missing 'id' parameter in query string"}), 400

    profile = COMPANY_PROFILES.get(company_id)

    if not profile:
        logging.warning(f"Company profile not found for id: {company_id}")
        return jsonify({"error": "Company profile not found"}), 404

    logging.debug(f"Returning profile for company: {company_id}")
    # Devolver el perfil completo
    return jsonify(profile)

# ============================================================================
# API - VALIDACIÓN DE PIN DE EMPRESA (NUEVO ENDPOINT)
# ============================================================================
@app.route("/api/validate_pin", methods=["POST"])
def validate_company_pin():
    """
    Valida si el PIN proporcionado para una empresa es correcto.
    """
    try:
        data = request.json
        if not data or 'company_id' not in data or 'pin' not in data:
            return jsonify({"error": "Faltan company_id o pin"}), 400

        company_id = data.get("company_id")
        provided_pin = data.get("pin")

        profile = COMPANY_PROFILES.get(company_id)

        # 1. Comprobar si la empresa existe
        if not profile:
            logging.warning(f"Intento de validación para empresa no existente: {company_id}")
            return jsonify({"error": "Empresa no válida"}), 404

        # 2. Comprobar si el PIN es correcto
        correct_pin = profile.get("pin")
        if not correct_pin or provided_pin != correct_pin:
            logging.warning(f"PIN incorrecto para la empresa: {company_id}")
            # Damos un error genérico para no dar pistas
            return jsonify({"error": "PIN o empresa incorrectos"}), 403 # 403 = Prohibido

        # 3. ¡Éxito! El PIN es correcto.
        # Devolvemos el perfil completo para que el frontend lo guarde.
        logging.info(f"PIN validado con éxito para: {company_id}")
        return jsonify({
            "success": True,
            "profile": profile # Devolvemos el perfil
        })

    except Exception as e:
        logging.error(f"❌ Error en validate_pin: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500
    

@app.route("/api/config", methods=["POST"])
def update_config():
    """
    Actualizar parámetros de configuración del dispositivo (ej. análisis).
    Debería requerir autenticación de admin en un futuro.
    """
    # TODO: Implementar seguridad/autenticación para este endpoint.
    # Por ahora, cualquiera puede cambiar la configuración.

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        updated_any = False
        response_config = {}

        # Actualizar solo los parámetros permitidos
        if 'analysis_params' in data and isinstance(data['analysis_params'], dict):
            # Podrías añadir validación aquí (ej. rangos numéricos)
            config.update_analysis_params(data['analysis_params'])
            logging.info(f"Analysis parameters updated: {data['analysis_params']}")
            response_config['analysis_params'] = config.get_analysis_params() # Devolver valor actualizado
            updated_any = True

        # Podrías añadir otros parámetros configurables aquí (ej. sync)
        # if 'sync_enabled' in data: ...
        # if 'sync_interval' in data: ...

        if not updated_any:
            return jsonify({"message": "No valid parameters provided to update"}), 400

        return jsonify({
            "message": "Configuration updated successfully",
            "updated_config": response_config
        })

    except Exception as e:
        logging.error(f"❌ Error updating config: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to update configuration: {str(e)}"}), 500

# ============================================================================
# API - Gestión de Mediciones (Historial)
# ============================================================================

@app.route("/api/measurements", methods=["GET"])
def get_measurements():
    """
    Obtener lista de mediciones de SQLite, filtrada por empresa.
    REQUIERE: parámetro 'company' en la URL (puede ser 'admin').
    """
    try:
        # Obtener parámetros de paginación y filtro
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int) # Aumentado por defecto
        company_id = request.args.get('company')

        # Validar company_id
        if not company_id:
             logging.warning("get_measurements called without 'company' parameter.")
             return jsonify({"error": "Missing 'company' parameter in query string"}), 400
        if company_id not in COMPANY_PROFILES:
             logging.warning(f"get_measurements called with invalid company_id: {company_id}")
             return jsonify({"error": f"Invalid company ID: '{company_id}'"}), 404 # 404 Not Found es más apropiado

        logging.debug(f"Fetching measurements for company '{company_id}', page {page}, per_page {per_page}")

        # Llamar a la base de datos (get_measurements maneja el caso 'admin')
        # Añadir manejo de errores por si la BD falla
        try:
             measurement_data = db.get_measurements(
                company_id=company_id,
                limit=per_page,
                offset=(page - 1) * per_page
            )
             total_count = db.count_measurements(company_id=company_id) # Necesitas añadir count_measurements a Database
             total_pages = (total_count + per_page - 1) // per_page

        except Exception as db_err:
             logging.error(f"Database error in get_measurements for {company_id}: {db_err}", exc_info=True)
             return jsonify({"error": "Database query failed"}), 500


        logging.info(f"Returning {len(measurement_data.get('measurements',[]))} measurements for company '{company_id}'")

        # Devolver resultados con metadatos de paginación
        return jsonify({
            "measurements": measurement_data.get('measurements', []), # Asegurar lista
            "page": page,
            "per_page": per_page,
            "total_items": measurement_data.get('total', 0), # Incluir total de la BD
            "total_pages": measurement_data.get('total_pages', 0),# Incluir total páginas
            "company_id_requested": company_id
        })

    except Exception as e:
        # Captura errores inesperados en el endpoint mismo
        logging.error(f"❌ Unexpected error in get_measurements endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred"}), 500


@app.route("/api/measurements/<int:measurement_id>", methods=["GET"])
def get_measurement(measurement_id):
    """
    Obtener una medición específica por ID.
    Incluye chequeo de seguridad por 'company' en la URL.
    """
    try:
        # Obtener company_id de la URL para chequeo de seguridad
        requesting_company_id = request.args.get('company')
        if not requesting_company_id:
            logging.warning(f"get_measurement {measurement_id} called without 'company' parameter.")
            return jsonify({"error": "Missing 'company' parameter for security check"}), 400
        if requesting_company_id not in COMPANY_PROFILES:
             logging.warning(f"get_measurement {measurement_id} called with invalid company_id: {requesting_company_id}")
             return jsonify({"error": f"Invalid company ID: '{requesting_company_id}'"}), 404

        logging.debug(f"Fetching measurement ID {measurement_id} requested by company '{requesting_company_id}'")

        # Obtener la medición de la BD
        try:
             measurement = db.get_measurement(measurement_id)
        except Exception as db_err:
             logging.error(f"Database error fetching measurement {measurement_id}: {db_err}", exc_info=True)
             return jsonify({"error": "Database query failed"}), 500


        if not measurement:
            logging.warning(f"Measurement ID {measurement_id} not found.")
            return jsonify({"error": "Measurement not found"}), 404

        # Chequeo de seguridad: ¿Puede esta empresa ver esta medición?
        actual_company_id = measurement.get('company_id')
        if requesting_company_id != 'admin' and actual_company_id != requesting_company_id:
             logging.warning(f"Access denied: Company '{requesting_company_id}' tried to access measurement {measurement_id} belonging to '{actual_company_id}'.")
             return jsonify({"error": "Access denied. This measurement belongs to another company."}), 403

        logging.info(f"Returning measurement ID {measurement_id} to company '{requesting_company_id}'")
        return jsonify(measurement)

    except Exception as e:
        logging.error(f"❌ Unexpected error in get_measurement endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred"}), 500

# ============================================================================
# API - Exportar Reportes
# ============================================================================

@app.route("/api/export", methods=["POST"])
def export_report():
    """
    Exportar reporte (single, comparison, dashboard).
    El frontend envía los datos a incluir + company_data para branding.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # --- Validar parámetros básicos ---
        format_type = data.get("format", "pdf").lower()
        export_type = data.get("type", "single")
        lang = data.get("lang", 'es')

        logging.info(f"📤 Export request: Type={export_type}, Format={format_type}, Lang={lang}")

        # --- ¡NUEVO! Extraer y procesar company_data ---
        company_data = data.get("company_data", {}) # Obtener datos de la empresa
        logo_url = company_data.get('logo')
        company_logo_server_path = None # Inicializar como None

        if logo_url:
            try:
                # --- Lógica para convertir URL a RUTA DE SERVIDOR ---
                # Asume que la URL es relativa a la carpeta 'static_folder' de Flask
                # Ejemplo: logo_url = '/assets/logos/faes_logo.png'
                # app.static_folder = '/path/to/project/frontend'
                
                # Quita la '/' inicial si existe para unir correctamente
                relative_path = logo_url.lstrip('/') 
                
                # Construye la ruta absoluta en el servidor
                # app.static_folder es la ruta a tu carpeta 'frontend'
                potential_path = Path(app.static_folder) / relative_path 
                
                # Resuelve a ruta absoluta y normalizada
                absolute_path = potential_path.resolve()

                # *** ¡Chequeo de seguridad MUY IMPORTANTE! ***
                # Asegurarse que la ruta resultante está DENTRO de la carpeta static
                if str(absolute_path).startswith(str(Path(app.static_folder).resolve())):
                    if absolute_path.exists() and absolute_path.is_file():
                        company_logo_server_path = str(absolute_path) # ¡Guardar como string!
                        logging.debug(f"Logo path resolved: {company_logo_server_path}")
                    else:
                        logging.warning(f"Logo file not found at resolved path: {absolute_path}")
                else:
                    # Si la ruta sale de la carpeta static, es un intento de Path Traversal
                    logging.error(f"Security Alert: Logo URL resolved outside static folder: {absolute_path}")
                    # No asignar la ruta, se usará el fallback o no habrá logo

            except Exception as path_err:
                logging.error(f"Error resolving logo path for URL '{logo_url}': {path_err}")
        else:
             logging.debug("No logo URL provided in company_data.")

        # Añadir la ruta resuelta (o None) de vuelta al diccionario company_data
        company_data['logo_path_on_server'] = company_logo_server_path
        # --------------------------------------------------------

        mime_types = { # (sin cambios)
             "json": "application/json", "csv": "text/csv",
             "pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        extensions = { # (sin cambios)
             "json": "json", "csv": "csv", "pdf": "pdf", "docx": "docx"
        }

        if format_type not in mime_types:
             logging.warning(f"Unsupported export format requested: {format_type}")
             return jsonify({"error": f"Unsupported format: '{format_type}'. Supported: {', '.join(extensions.keys())}"}), 400

        output = None
        filename_prefix = f"CraftRMN_{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # --- Lógica de exportación ---
        if export_type == "dashboard":
            stats = data.get("stats", {})
            chart_images_base64 = data.get("chart_images", {})
            chart_images = {}
            for key, base64_str in chart_images_base64.items():
                 if base64_str:
                     img_bytes = ReportExporter.base64_to_bytes(base64_str)
                     if img_bytes: chart_images[key] = img_bytes

            # --- ¡PASAR company_data! ---
            if format_type == "pdf":
                output = ReportExporter.export_dashboard_pdf(stats, company_data, chart_images, lang) # Modificado
            elif format_type == "docx":
                output = ReportExporter.export_dashboard_docx(stats, company_data, chart_images, lang) # Modificado
            # ... (json/csv si aplican) ...
            else:
                 return jsonify({"error": "Dashboard export to JSON/CSV not implemented with branding"}), 400


        elif export_type == "comparison":
            samples = data.get("samples", [])
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None

            # --- ¡PASAR company_data! ---
            if format_type == "pdf":
                output = ReportExporter.export_comparison_pdf(samples, company_data, chart_image_bytes, lang) # Modificado
            elif format_type == "docx":
                output = ReportExporter.export_comparison_docx(samples, company_data, chart_image_bytes, lang) # Modificado
            elif format_type == "csv":
                # CSV no necesita company_data (a menos que quieras añadirlo)
                output = ReportExporter.export_comparison_csv(samples, lang) 
            # ... (json si aplica) ...
            else:
                 output = ReportExporter.export_json(data) # JSON puede incluir company_data si quieres


        elif export_type == "single":
            results = data.get("results", {})
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None

            # --- ¡PASAR company_data! ---
            if format_type == "pdf":
                output = ReportExporter.export_pdf(results, company_data, chart_image_bytes, lang) # Modificado
            elif format_type == "docx":
                output = ReportExporter.export_docx(results, company_data, chart_image_bytes, lang) # Modificado
            elif format_type == "csv":
                 # CSV no necesita company_data (a menos que quieras añadirlo)
                output = ReportExporter.export_csv(results, lang) 
            else: # json
                # Podrías añadir company_data al JSON si quieres
                results_with_company = {**results, "company_info": company_data} # Ejemplo
                output = ReportExporter.export_json(results_with_company)


        else: # Tipo no soportado (sin cambios)
             logging.warning(f"Unsupported export type requested: {export_type}")
             return jsonify({"error": f"Unsupported export type: '{export_type}'..."}), 400


        # --- Enviar archivo generado (sin cambios) ---
        if output is None:
             logging.error(f"Export generation failed...")
             return jsonify({"error": f"Failed to generate export file..."}), 500

        filename = f"{filename_prefix}.{extensions[format_type]}"
        logging.info(f"✅ Sending export file: {filename} (MIME: {mime_types[format_type]})")

        return send_file(
            output,
            mimetype=mime_types[format_type],
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logging.error(f"❌ Error during export: {str(e)}", exc_info=True)
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

# ============================================================================
# API - Gestión de Archivos de Análisis (JSONs)
# ============================================================================
# NOTA: Estos endpoints operan sobre los archivos JSON en /storage/analysis.
# Son menos relevantes ahora que usamos la BD, pero pueden ser útiles para debug o migración.

@app.route("/api/analysis", methods=["GET"])
def list_analysis_files():
    """Listar archivos JSON de análisis disponibles."""
    # TODO: Considerar si este endpoint sigue siendo necesario o si /api/measurements lo reemplaza.
    # Podría requerir filtro por compañía si los nombres de archivo no son únicos globalmente.
    try:
        analyses = []
        for f in ANALYSIS_DIR.glob("*.json"):
            try:
                # Leer solo metadatos básicos para eficiencia
                stat = f.stat()
                # Intentar leer datos clave si es necesario (puede ralentizar)
                # with open(f, 'r', encoding='utf-8') as file: data = json.load(file) ...
                analyses.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    # Añadir company_id si está en el nombre del archivo
                })
            except Exception as e:
                logging.warning(f"⚠️ Error reading metadata for {f.name}: {str(e)}")
                # Incluir archivo con error para saber que existe
                analyses.append({"name": f.name, "error": str(e)})

        analyses.sort(key=lambda x: x.get("created", ""), reverse=True)
        return jsonify({"analyses": analyses, "total": len(analyses)})
    except Exception as e:
         logging.error(f"❌ Error listing analysis files: {str(e)}", exc_info=True)
         return jsonify({"error": "Failed to list analysis files"}), 500

@app.route("/api/result/<path:filename>", methods=["GET"])
def get_analysis_file(filename):
    """Obtener el contenido de un archivo JSON de análisis específico."""
    # TODO: Añadir chequeo de seguridad por compañía si es necesario.
    try:
        # Validar y limpiar filename para evitar Path Traversal
        if ".." in filename or filename.startswith("/"):
             return jsonify({"error": "Invalid filename"}), 400

        file_path = (ANALYSIS_DIR / filename).resolve()

        # Doble chequeo de seguridad
        if not str(file_path).startswith(str(ANALYSIS_DIR.resolve())):
             return jsonify({"error": "Access denied"}), 403

        if not file_path.is_file():
            return jsonify({"error": "Analysis file not found"}), 404

        # Devolver el contenido JSON
        with open(file_path, "r", encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)

    except FileNotFoundError:
         return jsonify({"error": "Analysis file not found"}), 404
    except json.JSONDecodeError:
         logging.error(f"Error decoding JSON file: {filename}")
         return jsonify({"error": "Invalid JSON format in analysis file"}), 500
    except Exception as e:
        logging.error(f"❌ Error getting analysis file {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve analysis file"}), 500

@app.route("/api/analysis/<path:filename>", methods=["DELETE"])
def delete_analysis_file(filename):
    """Eliminar un archivo JSON de análisis específico."""
    # TODO: Añadir chequeo de seguridad por compañía.
    try:
         # Validar y limpiar filename
        if ".." in filename or filename.startswith("/"):
             return jsonify({"error": "Invalid filename"}), 400

        file_path = (ANALYSIS_DIR / filename).resolve()

        # Seguridad
        if not str(file_path).startswith(str(ANALYSIS_DIR.resolve())):
             return jsonify({"error": "Access denied"}), 403

        if not file_path.is_file():
            return jsonify({"error": "Analysis file not found"}), 404

        # Eliminar el archivo
        file_path.unlink()
        logging.info(f"🗑️ Analysis file deleted: {filename}")
        return jsonify({"message": f"Analysis file '{filename}' deleted successfully"}), 200

    except FileNotFoundError:
         return jsonify({"error": "Analysis file not found"}), 404
    except Exception as e:
        logging.error(f"❌ Error deleting analysis file {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to delete analysis file: {str(e)}"}), 500

@app.route("/api/analysis/clear-all", methods=["DELETE"])
def clear_all_analysis_files():
    """Eliminar TODOS los archivos JSON de análisis."""
    # TODO: Añadir chequeo de seguridad por compañía (admin?).
    # La versión actual borra TODO, lo cual puede no ser deseado en multi-empresa.
    # Necesitaría un parámetro ?company=... y lógica para borrar solo esos.
    company_id = request.args.get('company') # Leer company si se envía

    # !!! --- AÑADIR LÓGICA DE FILTRADO AQUÍ --- !!!
    # Si company_id es None o 'admin', borrar todo (comportamiento actual)
    # Si company_id es específico, buscar archivos que coincidan (ej. por nombre) y borrarlos.
    # Esto requiere una convención en los nombres de archivo JSON o leer cada JSON.
    if company_id and company_id != 'admin':
         logging.warning(f"Clear-all called for specific company '{company_id}', but filtering is NOT YET IMPLEMENTED. Aborting.")
         return jsonify({"error": f"Clearing history for a specific company ('{company_id}') is not yet implemented. Only 'admin' can clear all."}), 400
         # Si lo implementas, ajusta la lógica de abajo.

    # Comportamiento actual (borrar todo si es admin o no se especifica)
    logging.warning("Executing CLEAR ALL analysis files request.")
    try:
        deleted_count = 0
        errors = []
        analysis_files = list(ANALYSIS_DIR.glob("*.json"))

        if not analysis_files:
            return jsonify({"message": "No analysis files to delete", "deleted_count": 0}), 200

        for file_path in analysis_files:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                logging.error(f"Error deleting {file_path.name}: {str(e)}")

        response = {
            "message": f"Deleted {deleted_count} analysis files",
            "deleted_count": deleted_count,
            "total_files": len(analysis_files)
        }
        if errors:
            response["errors"] = errors
        logging.info(f"✅ Bulk deletion completed: {deleted_count}/{len(analysis_files)} files removed.")
        return jsonify(response), 200

    except Exception as e:
        logging.error(f"❌ Error during bulk deletion of analysis files: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to clear all analysis files: {str(e)}"}), 500


# ============================================================================
# API - Gestión de Archivos de Entrada (Opcional, para carga manual)
# ============================================================================
# Estos endpoints manejan archivos en /storage/output, que son los archivos
# originales subidos ANTES del análisis. Pueden no ser necesarios si
# el flujo principal es subir y analizar directamente.

@app.route("/api/files", methods=["GET"])
def list_input_files():
    """Listar archivos en el directorio de entrada (output)."""
    try:
        files = []
        for f in OUTPUT_DIR.glob("*"): # Considerar filtrar por extensión .csv, .txt etc.
            if f.is_file():
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        return jsonify({"files": files})
    except Exception as e:
         logging.error(f"❌ Error listing input files: {str(e)}", exc_info=True)
         return jsonify({"error": "Failed to list input files"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_input_file():
    """Subir un archivo al directorio de entrada (output) sin analizarlo."""
    if "file" not in request.files:
        return jsonify({"error": "No 'file' part in the request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected for upload"}), 400

    try:
        # Guardar en OUTPUT_DIR
        file_path = OUTPUT_DIR / file.filename
        file.save(file_path)
        logging.info(f"📄 Input file uploaded manually: {file.filename}")
        return jsonify({
            "message": "File uploaded successfully to input directory",
            "filename": file.filename,
            "size": file_path.stat().st_size
        })
    except Exception as e:
         logging.error(f"❌ Error uploading input file {file.filename}: {str(e)}", exc_info=True)
         return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

@app.route("/api/download/<path:filename>", methods=["GET"])
def download_input_file(filename):
    """Descargar un archivo original del directorio de entrada (output)."""
    try:
        # Validar y limpiar filename
        if ".." in filename or filename.startswith("/"):
             return jsonify({"error": "Invalid filename"}), 400

        file_path = (OUTPUT_DIR / filename).resolve()

        # Seguridad
        if not str(file_path).startswith(str(OUTPUT_DIR.resolve())):
             return jsonify({"error": "Access denied"}), 403

        if not file_path.is_file():
            return jsonify({"error": "Input file not found"}), 404

        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

    except FileNotFoundError:
         return jsonify({"error": "Input file not found"}), 404
    except Exception as e:
        logging.error(f"❌ Error downloading input file {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to download file"}), 500

# ============================================================================
# API - Eliminar mediciones individuales
# ============================================================================
@app.route("/api/measurements/<int:measurement_id>", methods=["DELETE"])
def delete_measurement(measurement_id):
    """
    Elimina una medición específica por ID.
    Requiere 'company' en la URL para verificación de seguridad.
    """
    try:
        requesting_company_id = request.args.get('company')
        
        if not requesting_company_id:
            logging.warning(f"delete_measurement {measurement_id} called without 'company' parameter.")
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if requesting_company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company ID: '{requesting_company_id}'"}), 404
        
        logging.debug(f"Delete request for measurement {measurement_id} by company '{requesting_company_id}'")
        
        # Intentar eliminar (la BD hace el chequeo de pertenencia)
        success = db.delete_measurement(measurement_id, requesting_company_id)
        
        if success:
            logging.info(f"Measurement {measurement_id} deleted by {requesting_company_id}")
            return jsonify({
                "message": f"Measurement {measurement_id} deleted successfully"
            }), 200
        else:
            logging.warning(f"Measurement {measurement_id} not found or access denied for {requesting_company_id}")
            return jsonify({"error": "Measurement not found or access denied"}), 404
            
    except Exception as e:
        logging.error(f"Error deleting measurement {measurement_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to delete measurement: {str(e)}"}), 500


@app.route("/api/measurements/clear-all", methods=["DELETE"])
def clear_all_measurements():
    """
    Elimina todas las mediciones de una empresa específica.
    Requiere 'company' en la URL.
    """
    try:
        company_id = request.args.get('company')
        
        if not company_id:
            return jsonify({"error": "Missing 'company' parameter"}), 400
        
        if company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company ID: '{company_id}'"}), 404
        
        logging.warning(f"Clear all measurements request for company '{company_id}'")
        
        # Eliminar todas las mediciones de la empresa
        deleted_count = db.delete_all_measurements(company_id)
        
        logging.info(f"Deleted {deleted_count} measurements for company '{company_id}'")
        
        return jsonify({
            "message": f"Deleted {deleted_count} measurements",
            "deleted_count": deleted_count,
            "company_id": company_id
        }), 200
        
    except Exception as e:
        logging.error(f"Error clearing measurements: {e}", exc_info=True)
        return jsonify({"error": f"Failed to clear measurements: {str(e)}"}), 500



# ============================================================================
# Ejecutar servidor Flask
# ============================================================================
if __name__ == "__main__":
    # app.run() por defecto usa el servidor de desarrollo de Werkzeug.
    # debug=True activa el recargador automático y el depurador.
    # host='0.0.0.0' permite conexiones desde otras máquinas en la red local.
    app.run(host="0.0.0.0", port=5000, debug=True)
    # Para producción, deberías usar un servidor WSGI como Gunicorn o Waitress.
    # Ejemplo con Waitress (instalar con: pip install waitress):
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=5000)