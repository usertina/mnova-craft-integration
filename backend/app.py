from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from pathlib import Path
import os
import json
import sys
from datetime import datetime
from io import BytesIO
import traceback

# Importar el analizador
sys.path.append(str(Path(__file__).parent.parent / "worker"))
from analyzer import SpectrumAnalyzer

app = Flask(__name__, static_folder="../frontend")
CORS(app)  # Permitir CORS para desarrollo

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
        result_filename = f"{file.stem}_analysis_{timestamp}.json"
        result_path = ANALYSIS_DIR / result_filename
        
        with open(result_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Análisis completado: {result_filename}")
        
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
        
        with open(batch_result_path, "w") as f:
            json.dump(batch_summary, f, indent=2)
        
        print(f"✅ Lote completado: {batch_summary['successful']}/{len(files)} exitosos")
        
        return jsonify(batch_summary)
        
    except Exception as e:
        print(f"❌ Error en procesamiento por lotes: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": f"Batch analysis failed: {str(e)}"
        }), 500

# ============================================================================
# API - Exportar Reportes
# ============================================================================

@app.route("/api/export", methods=["POST"])
def export_report():
    """Exportar reporte en PDF o CSV"""
    try:
        data = request.get_json()
        results = data.get("results", {})
        format_type = data.get("format", "pdf")
        
        if format_type == "json":
            # Exportar como JSON
            output = BytesIO()
            output.write(json.dumps(results, indent=2).encode())
            output.seek(0)
            
            return send_file(
                output,
                mimetype="application/json",
                as_attachment=True,
                download_name=f"rmn_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        
        elif format_type == "csv":
            # Exportar como CSV
            import csv
            output = BytesIO()
            
            # Escribir CSV
            writer = csv.writer(output)
            writer.writerow(["Parameter", "Value", "Units"])
            
            if "analysis" in results:
                analysis = results["analysis"]
                writer.writerow(["Fluorine %", analysis.get("fluor_percentage", "N/A"), "%"])
                writer.writerow(["PIFAS %", analysis.get("pifas_percentage", "N/A"), "%"])
                writer.writerow(["Concentration", analysis.get("concentration", "N/A"), "mM"])
            
            output.seek(0)
            
            return send_file(
                output,
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"rmn_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
        
        else:
            return jsonify({"error": f"Format '{format_type}' not supported. Use 'json' or 'csv'"}), 400
            
    except Exception as e:
        print(f"❌ Error exportando: {str(e)}")
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

@app.route("/api/analysis", methods=["GET"])
def list_analysis():
    """Listar análisis disponibles"""
    analyses = []
    for f in ANALYSIS_DIR.glob("*.json"):
        analyses.append({
            "name": f.name,
            "size": f.stat().st_size,
            "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
        })
    return jsonify({"analyses": analyses})

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
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    return jsonify(data)

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