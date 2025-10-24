import csv
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
import numpy as np # <-- 1. Importar numpy

# Importar el analizador
sys.path.append(str(Path(__file__).parent.parent / "worker"))
from analyzer import SpectrumAnalyzer

# ============================================================================
# 2. AÑADIR CLASE DE CODIFICADOR JSON
# ============================================================================
class NumpyJSONEncoder(json.JSONEncoder):
    """
    Codificador JSON personalizado para manejar tipos de datos de NumPy
    que aparecen durante el análisis científico.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return super(NumpyJSONEncoder, self).default(obj)

# ============================================================================

app = Flask(__name__, static_folder="../frontend")
CORS(app)  # Permitir CORS para desarrollo

# 3. Asignar el codificador personalizado a Flask
app.json_encoder = NumpyJSONEncoder 

# Directorios
OUTPUT_DIR = Path("storage/output").resolve()
ANALYSIS_DIR = Path("storage/analysis").resolve()
CRAFT_EXPORTS_DIR = Path("storage/craft_exports").resolve()

# Crear directorios si no existen
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
    return send_from_directory(app.static_folder, "index.html")

@app.route('/<path:path>')
def static_proxy(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, "index.html")

# ============================================================================
# API - Health Check
# ============================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "ok",
        "message": "CraftRMN Analysis Server Running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# API - Análisis de Espectros
# ============================================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_spectrum():
    """Analizar un único espectro"""
    try:
        # Verificar que se recibió un archivo
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # Obtener parámetros de análisis
        parameters = {}
        if "parameters" in request.form:
            parameters = json.loads(request.form["parameters"])

        # Guardar archivo temporalmente
        file_path = OUTPUT_DIR / file.filename
        file.save(file_path)

        print(f"📊 Analizando: {file.filename}")

        # Realizar análisis
        analyzer = SpectrumAnalyzer()
        results = analyzer.analyze_file(
            file_path,
            fluor_range=parameters.get("fluor_range", {"min": -150, "max": -50}),
            pifas_range=parameters.get("pifas_range", {"min": -60, "max": -130}),
            concentration=parameters.get("concentration", 1.0)
        )

        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(file.filename).stem}_analysis_{timestamp}.json"
        result_path = ANALYSIS_DIR / result_filename

        # 4. Usar el codificador al guardar en el archivo
        with open(result_path, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, cls=NumpyJSONEncoder)

        print(f"✅ Análisis completado: {result_filename}")

        # 5. Flask usará automáticamente el app.json_encoder
        #    para convertir 'results' al enviarlo
        return jsonify(results)

    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "details": traceback.format_exc()
        }), 500

# ============================================================================
# API - Procesamiento por Lotes
# ============================================================================

@app.route("/api/batch", methods=["POST"])
def batch_analyze():
    """Analizar múltiples espectros"""
    try:
        files = request.files.getlist("files")

        if not files:
            return jsonify({"error": "No files provided"}), 400

        # Obtener parámetros
        parameters = {}
        if "parameters" in request.form:
            parameters = json.loads(request.form["parameters"])

        print(f"📦 Procesamiento por lotes: {len(files)} archivos")

        results = []
        analyzer = SpectrumAnalyzer()

        for file in files:
            try:
                # Guardar archivo
                file_path = OUTPUT_DIR / file.filename
                file.save(file_path)

                # Analizar
                result = analyzer.analyze_file(
                    file_path,
                    fluor_range=parameters.get("fluor_range", {"min": -150, "max": -50}),
                    pifas_range=parameters.get("pifas_range", {"min": -60, "max": -130}),
                    concentration=parameters.get("concentration", 1.0)
                )

                result["filename"] = file.filename
                result["status"] = "success"
                results.append(result)

                print(f"  ✅ {file.filename}")

            except Exception as e:
                print(f"  ❌ {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })

        # Guardar resultados del lote
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_result_path = ANALYSIS_DIR / f"batch_analysis_{timestamp}.json"

        batch_summary = {
            "total_files": len(files),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

        # 4b. Usar el codificador también al guardar el lote
        with open(batch_result_path, "w", encoding='utf-8') as f:
            json.dump(batch_summary, f, indent=2, ensure_ascii=False, cls=NumpyJSONEncoder)

        print(f"✅ Lote completado: {batch_summary['successful']}/{len(files)} exitosos")

        # 5b. Flask usará automáticamente el app.json_encoder
        return jsonify(batch_summary)

    except Exception as e:
        print(f"❌ Error en procesamiento por lotes: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Batch analysis failed: {str(e)}"
        }), 500

# ============================================================================
# API - Exportar Reportes (ENDPOINT MODIFICADO)
# ============================================================================

@app.route("/api/export", methods=["POST"])
def export_report():
    """
    Exportar reporte en PDF, DOCX, CSV o JSON.
    Maneja análisis únicos, comparaciones y dashboard.
    """
    try:
        data = request.get_json()
        format_type = data.get("format", "pdf").lower()
        export_type = data.get("type", "single")  # 'single', 'comparison', 'dashboard'
        lang = data.get("lang", "es")

        print(f"📤 Solicitud de exportación: Tipo={export_type}, Formato={format_type}")

        mime_types = {
            "json": "application/json",
            "csv": "text/csv",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        extensions = {
            "json": "json",
            "csv": "csv",
            "pdf": "pdf",
            "docx": "docx"
        }

        if format_type not in mime_types:
            return jsonify({"error": f"Formato '{format_type}' no soportado"}), 400

        output = None
        filename_prefix = ""

        # 🆕 EXPORTACIÓN DE DASHBOARD
        if export_type == "dashboard":
            stats = data.get("stats", {})
            chart_images_base64 = data.get("chart_images", {})
            recent_analyses = data.get("recent_analyses", [])
            
            # Convertir imágenes base64 a bytes
            chart_images = {}
            for chart_name, base64_str in chart_images_base64.items():
                try:
                    chart_images[chart_name] = ReportExporter.base64_to_bytes(base64_str)
                    print(f"📊 Gráfico '{chart_name}' decodificado")
                except Exception as e:
                    print(f"⚠️ Error decodificando gráfico '{chart_name}': {e}")
            
            filename_prefix = f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format_type == "pdf":
                output = ReportExporter.export_dashboard_pdf(stats, chart_images, lang)
            elif format_type == "docx":
                output = ReportExporter.export_dashboard_docx(stats, chart_images, lang)
            elif format_type == "csv":
                # Para CSV, usar el método existente o crear uno nuevo
                return jsonify({"error": "CSV export for dashboard should be handled in frontend"}), 400
            else:
                output = ReportExporter.export_json(data)
        
        # EXPORTACIÓN DE COMPARACIÓN
        elif export_type == "comparison":
            samples = data.get("samples", [])
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = None
            
            if chart_image_base64:
                try:
                    chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64)
                except Exception as e:
                    print(f"⚠️ Error decodificando imagen: {e}")
            
            filename_prefix = f"rmn_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format_type == "pdf":
                output = ReportExporter.export_comparison_pdf(samples, chart_image_bytes, lang)
            elif format_type == "docx":
                output = ReportExporter.export_comparison_docx(samples, chart_image_bytes, lang)
            elif format_type == "csv":
                output = ReportExporter.export_comparison_csv(samples, lang)
            else:
                output = ReportExporter.export_json(data)
        
        # EXPORTACIÓN DE ANÁLISIS ÚNICO
        else:
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = None
            
            if chart_image_base64:
                try:
                    chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64)
                except Exception as e:
                    print(f"⚠️ Error decodificando imagen: {e}")
            
            results = data.get("results", {})
            filename_prefix = f"rmn_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if format_type == "json":
                output = ReportExporter.export_json(results, lang)
            elif format_type == "csv":
                output = ReportExporter.export_csv(results, lang)
            elif format_type == "pdf":
                output = ReportExporter.export_pdf(results, chart_image_bytes, lang)
            elif format_type == "docx":
                output = ReportExporter.export_docx(results, chart_image_bytes, lang)
        
        if output is None:
             return jsonify({"error": f"No se pudo generar la exportación"}), 500

        filename = f"{filename_prefix}.{extensions[format_type]}"

        return send_file(
            output,
            mimetype=mime_types[format_type],
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ Error exportando: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

# ============================================================================
# API - Gestión de Archivos (endpoints originales)
# ============================================================================

@app.route("/api/files", methods=["GET"])
def list_files():
    """Listar archivos en OUTPUT_DIR"""
    files = []
    for f in OUTPUT_DIR.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    return jsonify({"files": files})

# ============================================================================
# API - Gestión de Archivos - ENDPOINT ACTUALIZADO
# ============================================================================

@app.route("/api/analysis", methods=["GET"])
def list_analysis():
    """Listar análisis disponibles con resumen de datos"""
    analyses = []

    for f in ANALYSIS_DIR.glob("*.json"):
        try:
            # Leer el contenido del archivo JSON
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Extraer datos clave para el historial
            # Asegurarse de que los datos clave existen
            analysis_data = data.get("analysis", {})
            analysis_summary = {
                "name": f.name,
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                # Datos del análisis
                "fluor": analysis_data.get("fluor_percentage"),
                "pfas": analysis_data.get("pifas_percentage"),
                "concentration": analysis_data.get("pifas_concentration"),
                "quality": data.get("quality_score"),
                "filename": data.get("filename", f.name)
            }

            analyses.append(analysis_summary)

        except Exception as e:
            # Si hay error leyendo el archivo, incluirlo con datos limitados
            print(f"⚠️  Error leyendo {f.name}: {str(e)}")
            analyses.append({
                "name": f.name,
                "size": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "error": str(e)
            })

    # Ordenar por fecha de creación (más reciente primero)
    analyses.sort(key=lambda x: x.get("created", ""), reverse=True)

    return jsonify({"analyses": analyses, "total": len(analyses)})

# ============================================================================
# API - Eliminar Análisis Individual
# ============================================================================

@app.route("/api/analysis/<path:filename>", methods=["DELETE"])
def delete_analysis(filename):
    """Eliminar un análisis específico"""
    try:
        file_path = ANALYSIS_DIR / filename

        # Verificar que el archivo existe
        if not file_path.exists():
            return jsonify({
                "error": "Analysis not found",
                "filename": filename
            }), 404

        # Verificar que está dentro del directorio permitido (seguridad)
        if not str(file_path.resolve()).startswith(str(ANALYSIS_DIR.resolve())):
            return jsonify({
                "error": "Invalid file path"
            }), 403

        # Eliminar el archivo
        file_path.unlink()

        print(f"🗑️  Análisis eliminado: {filename}")

        return jsonify({
            "message": "Analysis deleted successfully",
            "filename": filename
        }), 200

    except Exception as e:
        print(f"❌ Error eliminando análisis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to delete analysis: {str(e)}"
        }), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Subir archivo manualmente"""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file_path = OUTPUT_DIR / file.filename
    file.save(file_path)

    return jsonify({
        "message": "File uploaded successfully",
        "filename": file.filename,
        "size": file_path.stat().st_size
    })

@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Descargar archivo original"""
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/api/result/<path:filename>", methods=["GET"])
def get_analysis(filename):
    """Obtener resultado de análisis específico"""
    file_path = ANALYSIS_DIR / filename

    if not file_path.exists():
        return jsonify({"error": "Analysis not found"}), 404

    with open(file_path, "r", encoding='utf-8') as f:
        data = json.load(f)

    return jsonify(data)

@app.route("/api/analysis/clear-all", methods=["DELETE"])
def clear_all_analysis():
    """Eliminar TODOS los análisis del sistema"""
    try:
        deleted_count = 0
        errors = []

        # Obtener todos los archivos JSON en ANALYSIS_DIR
        analysis_files = list(ANALYSIS_DIR.glob("*.json"))

        if not analysis_files:
            return jsonify({
                "message": "No hay análisis para eliminar",
                "deleted_count": 0
            }), 200

        # Eliminar cada archivo
        for file_path in analysis_files:
            try:
                file_path.unlink()
                deleted_count += 1
                print(f"🗑️  Eliminado: {file_path.name}")
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                print(f"❌ Error eliminando {file_path.name}: {str(e)}")

        # Preparar respuesta
        response = {
            "message": f"Eliminados {deleted_count} análisis",
            "deleted_count": deleted_count,
            "total_files": len(analysis_files)
        }

        if errors:
            response["errors"] = errors
            response["warning"] = f"Se encontraron {len(errors)} errores durante la eliminación"

        print(f"✅ Limpieza completada: {deleted_count}/{len(analysis_files)} archivos eliminados")

        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Error en limpieza masiva: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to clear all analyses: {str(e)}"
        }), 500

# ============================================================================
# Ejecutar servidor
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CraftRMN Analysis Server")
    print("=" * 60)
    print(f"📊 Version: 1.0.0")
    print(f"🌐 Running on: http://localhost:5000")
    print(f"📁 Storage: {OUTPUT_DIR}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)