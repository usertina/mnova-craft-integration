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

from database import get_db
from config_manager import get_config_manager, LicenseValidator
from company_data import COMPANY_PROFILES

logging.getLogger().setLevel(logging.DEBUG)

# Inicializar
db = get_db()
config = get_config_manager()

# Importar el analizador
# Asumimos que la carpeta 'worker' está al mismo nivel que 'backend'
sys.path.append(str(Path(__file__).parent.parent / "worker"))
from analyzer import SpectrumAnalyzer

class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, np.bool_): return bool(obj)
        else: return super(NumpyJSONEncoder, self).default(obj)

app = Flask(__name__, static_folder="../frontend")
CORS(app)
app.json_encoder = NumpyJSONEncoder 

# Anclar las rutas al directorio de este script
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "storage" / "output"
ANALYSIS_DIR = SCRIPT_DIR / "storage" / "analysis"
CRAFT_EXPORTS_DIR = SCRIPT_DIR / "storage" / "craft_exports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
CRAFT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 Directorios configurados:")
print(f"   Output: {OUTPUT_DIR}")
print(f"   Analysis: {ANALYSIS_DIR}")
print(f"   Craft Exports: {CRAFT_EXPORTS_DIR}")

# ============================================================================
# FRONTEND - Servir archivos estáticos
# ============================================================================

@app.route('/')
def home():
    # Asumimos que el frontend está en la carpeta ../frontend/
    return send_from_directory(app.static_folder, "index.html")

@app.route('/<path:path>')
def static_proxy(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, "index.html")

# ============================================================================
# API - Análisis de Espectros
# ============================================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_spectrum():
    """
    Analizar un único espectro.
    REQUIERE: un 'company_id' en el formulario.
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        company_id = request.form.get("company_id")
        if not company_id:
            return jsonify({"error": "No company_id provided with the analysis request"}), 400
        if company_id not in COMPANY_PROFILES:
             return jsonify({"error": f"Invalid company_id: {company_id}"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        parameters = {}
        if "parameters" in request.form:
            parameters = json.loads(request.form["parameters"])

        file_path = OUTPUT_DIR / file.filename
        file.save(file_path)

        print(f"📊 Analizando: {file.filename} para la empresa {company_id}")

        analyzer = SpectrumAnalyzer()
        analysis_params = config.get_analysis_params()
        
        results = analyzer.analyze_file(
            file_path,
            fluor_range=parameters.get("fluor_range", analysis_params['fluor_range']),
            pifas_range=parameters.get("pifas_range", analysis_params['pifas_range']),
            concentration=parameters.get("concentration", analysis_params['default_concentration'])
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(file.filename).stem}_analysis_{timestamp}.json"
        result_path = ANALYSIS_DIR / result_filename
        
        with open(result_path, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, cls=NumpyJSONEncoder)
        
        print(f"  💾 Guardado: {result_filename}")

        measurement_data = {
            'device_id': config.get_device_id(),
            'company_id': company_id, # Usar el company_id de la petición
            'filename': file.filename,
            'timestamp': datetime.now().isoformat(),
            'analysis': results.get('analysis', {}),
            'quality_score': results.get('quality_score'),
            'spectrum': results.get('spectrum', {}),
            'peaks': results.get('peaks', [])
        }
        
        measurement_id = db.save_measurement(measurement_data)
        print(f"  📊 SQLite ID: {measurement_id}")
        
        results['measurement_id'] = measurement_id
        results['result_file'] = result_filename

        return jsonify(results)

    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "details": traceback.format_exc()
        }), 500

# ============================================================================
# API - Activación y Configuración del Dispositivo
# ============================================================================

@app.route("/api/activate", methods=["POST"])
def activate_device():
    """
    Activa el dispositivo para el ADMIN, no para una empresa.
    """
    try:
        data = request.json
        license_key = data.get("license_key", "").strip()

        if not license_key:
            return jsonify({"error": "No license key provided"}), 400

        validator = LicenseValidator()
        device_id = config.get_device_id()

        if validator.validate_license(license_key, device_id):
            
            success = config.activate_device(license_key)

            if success:
                return jsonify({
                    "message": "Device activated successfully (Admin Mode)",
                    "device_id": device_id
                })
            else:
                return jsonify({"error": "Failed to save activation"}), 500
        
        else:
            return jsonify({"error": "Invalid or incorrect admin license key"}), 403

    except Exception as e:
        print(f"❌ Error en activación: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Activation failed: {str(e)}"}), 500
    
@app.route("/api/config", methods=["GET"])
def get_config():
    """
    Obtener configuración del dispositivo.
    Devuelve el estado de activación y la LISTA de empresas.
    """
    try:
        # Extraer solo los perfiles públicos (sin admin) para la lista de login
        login_companies = {
            cid: prof for cid, prof in COMPANY_PROFILES.items() 
            if cid != 'admin'
        }

        return jsonify({
            "device_id": config.get_device_id(),
            "activated": config.is_activated(),
            "analysis_params": config.get_analysis_params(),
            "available_companies": login_companies # Lista para la pantalla de login
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT NUEVO: Obtener perfil de empresa
@app.route("/api/company_profile", methods=["GET"])
def get_company_profile():
    """
    Obtiene el perfil (branding) de una empresa específica
    para que el frontend pueda "loguearse" y cambiar su apariencia.
    """
    company_id = request.args.get('id')
    if not company_id:
        return jsonify({"error": "No company 'id' provided"}), 400
        
    profile = COMPANY_PROFILES.get(company_id)
    
    if not profile:
        return jsonify({"error": "Company profile not found"}), 404
        
    return jsonify(profile)


@app.route("/api/config", methods=["POST"])
def update_config():
    """
    Actualizar configuración del dispositivo (solo admin).
    """
    # TODO: Añadir aquí una comprobación de seguridad (ej. un token de admin)
    
    try:
        data = request.json
        
        if 'sync_enabled' in data:
            config.set_sync_enabled(data['sync_enabled'])
        if 'sync_interval' in data:
            config.set_sync_interval(data['sync_interval'])
        if 'analysis_params' in data:
            config.update_analysis_params(data['analysis_params'])
        
        return jsonify({
            "message": "Configuration updated",
            "config": {
                "sync_enabled": config.get_sync_enabled(),
                "sync_interval": config.get_sync_interval(),
                "analysis_params": config.get_analysis_params()
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# LISTAR MEDICIONES DESDE SQLITE
# ============================================================================

@app.route("/api/measurements", methods=["GET"])
def get_measurements():
    """
    Obtener mediciones de SQLite.
    REQUIERE: un parámetro 'company' en la URL.
    ej: /api/measurements?company=BIDATEK
    ej: /api/measurements?company=admin (para ver todo)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        company_id = request.args.get('company')
        
        if not company_id:
             return jsonify({"error": "No 'company' parameter provided in URL"}), 400
        
        if company_id not in COMPANY_PROFILES:
            return jsonify({"error": f"Invalid company ID: {company_id}"}), 404

        # La lógica de 'admin' se maneja dentro de db.get_measurements
        measurements = db.get_measurements(
            company_id=company_id,
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        return jsonify({
            "measurements": measurements,
            "page": page,
            "per_page": per_page,
            "company_id_requested": company_id
        })
    
    except Exception as e:
        print(f"❌ Error obteniendo mediciones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/measurements/<int:measurement_id>", methods=["GET"])
def get_measurement(measurement_id):
    """
    Obtener una medición específica de SQLite.
    REQUIERE: 'company' en la URL para seguridad.
    """
    try:
        measurement = db.get_measurement(measurement_id)
        if not measurement:
            return jsonify({"error": "Measurement not found"}), 404
        
        company_id = request.args.get('company')
        if not company_id:
            return jsonify({"error": "No 'company' parameter provided for security check"}), 400

        # Si no eres admin Y la medición no es tuya, denegar acceso.
        if company_id != 'admin' and measurement.get('company_id') != company_id:
             return jsonify({"error": "Access denied. This measurement belongs to another company."}), 403
            
        return jsonify(measurement)
    
    except Exception as e:
        print(f"❌ Error obteniendo medición: {str(e)}")
        return jsonify({"error": str(e)}), 500
   
# ============================================================================
# API - Exportar Reportes
# ============================================================================

@app.route("/api/export", methods=["POST"])
def export_report():
    """
    Exportar reporte.
    El frontend DEBE enviar el branding (logo, nombre) en la petición.
    """
    try:
        data = request.get_json()
        format_type = data.get("format", "pdf").lower()
        export_type = data.get("type", "single")
        lang = data.get("lang", 'es')
        
        # El frontend obtiene esto de /api/company_profile
        company_name = data.get("company_name", "CraftRMN Pro")
        branding_info = data.get("branding_info", {})

        print(f"📤 Solicitud de exportación: Tipo={export_type}, Formato={format_type} para {company_name}")
        
        mime_types = {
            "json": "application/json", "csv": "text/csv",
            "pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        extensions = {
            "json": "json", "csv": "csv", "pdf": "pdf", "docx": "docx"
        }
        if format_type not in mime_types:
            return jsonify({"error": f"Formato '{format_type}' no soportado"}), 400
        output = None
        filename_prefix = ""
        
        if export_type == "dashboard":
            stats = data.get("stats", {})
            chart_images_base64 = data.get("chart_images", {})
            chart_images = {k: ReportExporter.base64_to_bytes(v) for k, v in chart_images_base64.items()}
            filename_prefix = f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if format_type == "pdf":
                output = ReportExporter.export_dashboard_pdf(stats, chart_images, lang, company_name, branding_info)
            elif format_type == "docx":
                output = ReportExporter.export_dashboard_docx(stats, chart_images, lang, company_name, branding_info)
            else:
                output = ReportExporter.export_json(data)
        elif export_type == "comparison":
            samples = data.get("samples", [])
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None
            filename_prefix = f"rmn_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if format_type == "pdf":
                output = ReportExporter.export_comparison_pdf(samples, chart_image_bytes, lang, company_name, branding_info)
            elif format_type == "docx":
                output = ReportExporter.export_comparison_docx(samples, chart_image_bytes, lang, company_name, branding_info)
            elif format_type == "csv":
                output = ReportExporter.export_comparison_csv(samples, lang)
            else:
                output = ReportExporter.export_json(data)
        else: # single
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None
            results = data.get("results", {})
            filename_prefix = f"rmn_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if format_type == "json":
                output = ReportExporter.export_json(results, lang)
            elif format_type == "csv":
                output = ReportExporter.export_csv(results, lang)
            elif format_type == "pdf":
                output = ReportExporter.export_pdf(results, chart_image_bytes, lang, company_name, branding_info)
            elif format_type == "docx":
                output = ReportExporter.export_docx(results, chart_image_bytes, lang, company_name, branding_info)
        
        if output is None:
             return jsonify({"error": f"No se pudo generar la exportación"}), 500

        filename = f"{filename_prefix}.{extensions[format_type]}"
        return send_file(output, mimetype=mime_types[format_type], as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"❌ Error exportando: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

# ============================================================================
# API - Gestión de Archivos (sin cambios)
# ============================================================================

@app.route("/api/files", methods=["GET"])
def list_files():
    files = []
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    return jsonify({"files": files})

@app.route("/api/analysis", methods=["GET"])
def list_analysis():
    analyses = []
    for f in ANALYSIS_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            analysis_data = data.get("analysis", {})
            analysis_summary = {
                "name": f.name, "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "fluor": analysis_data.get("fluor_percentage"),
                "pfas": analysis_data.get("pifas_percentage"),
                "concentration": analysis_data.get("pifas_concentration"),
                "quality": data.get("quality_score"),
                "filename": data.get("filename", f.name)
            }
            analyses.append(analysis_summary)
        except Exception as e:
            print(f"⚠️  Error leyendo {f.name}: {str(e)}")
    analyses.sort(key=lambda x: x.get("created", ""), reverse=True)
    return jsonify({"analyses": analyses, "total": len(analyses)})

@app.route("/api/analysis/<path:filename>", methods=["DELETE"])
def delete_analysis(filename):
    try:
        file_path = ANALYSIS_DIR / filename
        if not file_path.exists():
            return jsonify({"error": "Analysis not found"}), 404
        if not str(file_path.resolve()).startswith(str(ANALYSIS_DIR.resolve())):
            return jsonify({"error": "Invalid file path"}), 403
        file_path.unlink()
        print(f"🗑️  Análisis eliminado: {filename}")
        return jsonify({"message": "Analysis deleted successfully"}), 200
    except Exception as e:
        print(f"❌ Error eliminando análisis: {str(e)}")
        return jsonify({"error": f"Failed to delete analysis: {str(e)}"}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    file_path = OUTPUT_DIR / file.filename
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully", "filename": file.filename})

@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/api/result/<path:filename>", methods=["GET"])
def get_analysis(filename):
    file_path = ANALYSIS_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Analysis not found"}), 404
    with open(file_path, "r", encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/api/analysis/clear-all", methods=["DELETE"])
def clear_all_analysis():
    try:
        deleted_count = 0
        errors = []
        analysis_files = list(ANALYSIS_DIR.glob("*.json"))
        if not analysis_files:
            return jsonify({"message": "No hay análisis para eliminar", "deleted_count": 0}), 200
        for file_path in analysis_files:
            try:
                file_path.unlink()
                deleted_count += 1
                print(f"🗑️  Eliminado: {file_path.name}")
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        response = {"message": f"Eliminados {deleted_count} análisis", "deleted_count": deleted_count}
        if errors:
            response["errors"] = errors
        print(f"✅ Limpieza completada: {deleted_count}/{len(analysis_files)} archivos eliminados")
        return jsonify(response), 200
    except Exception as e:
        print(f"❌ Error en limpieza masiva: {str(e)}")
        return jsonify({"error": f"Failed to clear all analyses: {str(e)}"}), 500

# ============================================================================
# Ejecutar servidor
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CraftRMN Analysis Server (Multi-Empresa)")
    print("=" * 60)
    print(f"📊 Version: 2.0.0")
    print(f"🌐 Running on: http://localhost:5000")
    print(f"📁 Storage: {OUTPUT_DIR}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
