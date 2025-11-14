"""
Rutas de exportación de reportes (PDF, DOCX, CSV, JSON)
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from pathlib import Path
from datetime import datetime
import logging
import base64

from auth import token_required
from export_utils import ReportExporter

export_bp = Blueprint('export', __name__)
logger = logging.getLogger(__name__)


@export_bp.route("/export", methods=["POST"])
@token_required
def export_report():
    """
    Exportar reporte (single, comparison, dashboard)
    Body: format, type, lang, company_data, results/samples/stats
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        format_type = data.get("format", "pdf").lower()
        export_type = data.get("type", "single")
        lang = data.get("lang", 'es')

        logger.info(f"📤 Export: Type={export_type}, Format={format_type}, Lang={lang}")

        # Procesar company_data (Logo)
        company_data = data.get("company_data", {})
        logo_url = company_data.get('logo')
        company_logo_server_path = None

        if logo_url:
            try:
                relative_path = logo_url.lstrip('/')
                potential_path = Path(current_app.static_folder) / relative_path
                absolute_path = potential_path.resolve()

                # Seguridad: verificar que está en static_folder
                if str(absolute_path).startswith(str(Path(current_app.static_folder).resolve())):
                    if absolute_path.exists() and absolute_path.is_file():
                        company_logo_server_path = str(absolute_path)
                        logger.debug(f"Logo path: {company_logo_server_path}")
                    else:
                        logger.warning(f"Logo not found: {absolute_path}")
                else:
                    logger.error(f"Security: Logo outside static folder: {absolute_path}")
            except Exception as path_err:
                logger.error(f"Error resolving logo: {path_err}")
        
        company_data['logo_path_on_server'] = company_logo_server_path

        # MIME types
        mime_types = {
            "json": "application/json",
            "csv": "text/csv",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        extensions = {
            "json": "json", "csv": "csv", "pdf": "pdf", "docx": "docx"
        }

        if format_type not in mime_types:
            logger.warning(f"Unsupported format: {format_type}")
            return jsonify({"error": f"Unsupported format: '{format_type}'"}), 400

        output = None
        filename_prefix = f"CraftRMN_{export_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Función helper para convertir imágenes 2D a Base64
        def convert_image_paths_to_base64(results_obj):
            """Convierte paths de imágenes 2D a Base64"""
            logger.debug("Convirtiendo imágenes 2D a Base64...")
            try:
                pfas_detection = results_obj.get('pfas_detection', {})
                compounds_list = pfas_detection.get('detected_pfas', pfas_detection.get('compounds', []))

                if not compounds_list:
                    logger.warning("No se encontró lista de compuestos")
                    return

                for compound in compounds_list:
                    image_path_url = compound.get('image_2d')
                    
                    if image_path_url and not image_path_url.startswith('data:image'):
                        relative_path = image_path_url.lstrip('/')
                        absolute_path = (Path(current_app.static_folder) / relative_path).resolve()
                        
                        assets_dir = (Path(current_app.static_folder) / "assets").resolve()
                        if str(absolute_path).startswith(str(assets_dir)):
                            if absolute_path.exists() and absolute_path.is_file():
                                with open(absolute_path, "rb") as f:
                                    img_bytes = f.read()
                                img_b64_str = base64.b64encode(img_bytes).decode('utf-8')
                                compound['image_2d'] = f"data:image/png;base64,{img_b64_str}"
                                logger.debug(f"Convertido {image_path_url}")
                            else:
                                logger.warning(f"Imagen no encontrada: {absolute_path}")
                                compound['image_2d'] = None
                        else:
                            logger.warning(f"Imagen fuera de assets: {absolute_path}")
                            compound['image_2d'] = None
            except Exception as img_err:
                logger.error(f"Error convirtiendo imágenes: {img_err}", exc_info=True)

        # Lógica de exportación según tipo
        if export_type == "dashboard":
            stats = data.get("stats", {})
            chart_images_base64 = data.get("chart_images", {})
            chart_images = {}
            for key, base64_str in chart_images_base64.items():
                if base64_str:
                    img_bytes = ReportExporter.base64_to_bytes(base64_str)
                    if img_bytes:
                        chart_images[key] = img_bytes
            
            if format_type == "pdf":
                output = ReportExporter.export_dashboard_pdf(stats, company_data, chart_images, lang)
            elif format_type == "docx":
                output = ReportExporter.export_dashboard_docx(stats, company_data, chart_images, lang)
            else:
                return jsonify({"error": "Dashboard export to JSON/CSV not implemented"}), 400

        elif export_type == "comparison":
            samples = data.get("samples", [])
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None

            if format_type == "pdf":
                output = ReportExporter.export_comparison_pdf(samples, company_data, chart_image_bytes, lang)
            elif format_type == "docx":
                output = ReportExporter.export_comparison_docx(samples, company_data, chart_image_bytes, lang)
            elif format_type == "csv":
                output = ReportExporter.export_comparison_csv(samples, lang)
            else:
                output = ReportExporter.export_json(data)

        elif export_type == "single":
            results = data.get("results", {})
            
            # Convertir imágenes
            convert_image_paths_to_base64(results)
            
            chart_image_base64 = data.get("chart_image")
            chart_image_bytes = ReportExporter.base64_to_bytes(chart_image_base64) if chart_image_base64 else None

            if format_type == "pdf":
                output = ReportExporter.export_pdf(results, company_data, chart_image_bytes, lang)
            elif format_type == "docx":
                output = ReportExporter.export_docx(results, company_data, chart_image_bytes, lang)
            elif format_type == "csv":
                output = ReportExporter.export_csv(results, lang)
            else:
                results_with_company = {**results, "company_info": company_data}
                output = ReportExporter.export_json(results_with_company)

        else:
            logger.warning(f"Unsupported export type: {export_type}")
            return jsonify({"error": f"Unsupported export type: '{export_type}'"}), 400

        # Enviar archivo
        if output is None:
            logger.error(f"Export generation failed")
            return jsonify({"error": f"Failed to generate export file"}), 500

        filename = f"{filename_prefix}.{extensions[format_type]}"
        logger.info(f"✅ Sending: {filename}")

        return send_file(
            output,
            mimetype=mime_types[format_type],
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"❌ Error during export: {str(e)}", exc_info=True)
        return jsonify({"error": f"Export failed: {str(e)}"}), 500