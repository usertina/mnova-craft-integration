from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import os
import json

app = Flask(__name__, static_folder="../frontend")

OUTPUT_DIR = Path("storage/output").resolve()
ANALYSIS_DIR = Path("storage/analysis").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# FRONTEND
@app.route('/')
def home():
    return send_from_directory(app.static_folder, "index.html")

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# API
@app.route("/api/files", methods=["GET"])
def list_files():
    files = [f.name for f in OUTPUT_DIR.glob("*") if f.is_file()]
    return jsonify({"files": files})

@app.route("/api/analysis", methods=["GET"])
def list_analysis():
    analyses = [f.name for f in ANALYSIS_DIR.glob("*.json")]
    return jsonify({"analyses": analyses})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    path = OUTPUT_DIR / file.filename
    file.save(path)
    return jsonify({"message": "File uploaded", "filename": file.filename})

@app.route("/api/download/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/api/result/<path:filename>", methods=["GET"])
def get_analysis(filename):
    file_path = ANALYSIS_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Not found"}), 404
    with open(file_path, "r") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
