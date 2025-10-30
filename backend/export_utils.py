# backend/export_utils.py

"""
Utilidades de Exportación Mejoradas - CraftRMN Pro v2.1
Genera reportes completos con gráficos en PDF, DOCX y CSV,
incluyendo personalización completa por empresa.
"""

import io
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, BinaryIO
import os
from typing import Dict, List, BinaryIO, Optional 

# --- Plotly ---
try:
    import plotly.graph_objects as go
    from plotly.io import to_image
except ImportError:
    print("Error: Plotly no está instalado. `pip install plotly kaleido`")
    go = None # Para evitar errores posteriores

# --- Traducciones ---
try:
    from translation_manager import TranslationManager
except ImportError:
    # Fallback si translation_manager no existe
    class TranslationManager:
        def __init__(self, lang='es'):
            self.lang = lang
        
        def get(self, key, default=None):
            """Obtener traducción con valor por defecto."""
            return default or f"[{key}]"
        
        def t(self, key, default=None):
            """Alias para get()."""
            return self.get(key, default)
    print("Advertencia: translation_manager no encontrado. Usando traducciones placeholder.")

# --- DOCX ---
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    print("Advertencia: python-docx no está instalado (`pip install python-docx`). Exportación DOCX deshabilitada.")
    DOCX_AVAILABLE = False
    Document = None # Define dummy para evitar errores si se llama

# --- PDF (ReportLab) ---
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, BaseDocTemplate, Frame, PageTemplate,
        Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    print("Advertencia: reportlab no está instalado (`pip install reportlab`). Exportación PDF deshabilitada.")
    PDF_AVAILABLE = False
    BaseDocTemplate = None # Define dummy

# ============================================================================
# FUNCIÓN AUXILIAR PARA NORMALIZAR UNICODE (Sin cambios)
# ============================================================================
def normalize_region_text(text: str) -> str:
    """Convierte caracteres Unicode específicos a texto normal."""
    replacements = {
        '\u2082': '2', '\u2083': '3', '\u207b': '-',
        '₂': '2', '₃': '3', '⁻': '-', 'ó': 'o',
        # Puedes añadir más reemplazos si encuentras otros caracteres problemáticos
    }
    result = str(text) # Asegurar que sea string
    for unicode_char, replacement in replacements.items():
        result = result.replace(unicode_char, replacement)
    return result

# ============================================================================
# CLASE PRINCIPAL ReportExporter
# ============================================================================
class ReportExporter:
    """Clase mejorada para exportar análisis RMN con gráficos y branding."""

    # ========================================================================
    # EXPORTACIÓN JSON (Sin cambios)
    # ========================================================================
    @staticmethod
    def export_json(results: Dict, lang: str = 'es') -> BinaryIO:
        """Exporta resultados como JSON."""
        output = io.BytesIO()
        json_str = json.dumps(results, indent=2, ensure_ascii=False)
        output.write(json_str.encode('utf-8'))
        output.seek(0)
        return output

    # ========================================================================
    # UTILIDADES PARA GRÁFICOS (Sin cambios)
    # ========================================================================
    @staticmethod
    def plotly_to_image(plotly_json: Dict, format='png', width=800, height=500) -> bytes:
        """Convierte un gráfico Plotly (JSON) a imagen."""
        if go is None: return None
        try:
            fig = go.Figure(plotly_json)
            img_bytes = to_image(fig, format=format, width=width, height=height, scale=2)
            return img_bytes
        except Exception as e:
            print(f"Error convirtiendo gráfico Plotly: {e}")
            return None

    @staticmethod
    def base64_to_bytes(base64_str: str) -> bytes:
        """Convierte string base64 a bytes, manejando padding."""
        if not base64_str: return None
        try:
            if isinstance(base64_str, bytes): base64_str = base64_str.decode('utf-8')
            if ',' in base64_str: base64_str = base64_str.split(',')[1]
            missing_padding = len(base64_str) % 4
            if missing_padding: base64_str += '=' * (4 - missing_padding)
            return base64.b64decode(base64_str)
        except Exception as e:
            print(f"Error decodificando base64: {e}")
            return None

    # ========================================================================
    # FUNCIÓN AUXILIAR PARA PIE DE PÁGINA PDF (REUTILIZABLE)
    # ========================================================================
    @staticmethod
    def _add_pdf_footer(canvas, doc, company_data):
        """Añade pie de página con info de empresa y número de página (ReportLab)."""
        if not company_data: company_data = {}
        canvas.saveState()
        styles = getSampleStyleSheet()
        footer_style = ParagraphStyle(
            'FooterStyle', parent=styles['Normal'], fontSize=8,
            alignment=TA_CENTER, textColor=colors.grey
        )
        company_name=company_data.get('name','CraftRMN Pro'); company_address=company_data.get('address','');
        company_phone=company_data.get('phone',''); company_email=company_data.get('email','')
        parts = [part for part in [company_name, company_address, f"Tel: {company_phone}", company_email] if part]
        footer_text = " | ".join(parts)
        p = Paragraph(footer_text, footer_style)
        p.wrapOn(canvas, doc.width, doc.bottomMargin)
        p.drawOn(canvas, doc.leftMargin, 0.5 * inch)
        page_num_text = f"Página {canvas.getPageNumber()}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.width + doc.leftMargin - 0.1*inch, 0.5 * inch, page_num_text)
        canvas.restoreState()

    # ========================================================================
    # FUNCIÓN AUXILIAR PARA PIE DE PÁGINA DOCX (REUTILIZABLE)
    # ========================================================================
    @staticmethod
    def _add_docx_footer(doc: Document, company_data: Dict): # pyright: ignore[reportInvalidTypeForm]
        """Añade pie de página con info de empresa a un documento DOCX."""
        if not DOCX_AVAILABLE or not doc: return
        if not company_data: company_data = {}
        try:
            section = doc.sections[0]; footer = section.footer
            if footer.paragraphs: footer_para = footer.paragraphs[0]; footer_para.clear()
            else: footer_para = footer.add_paragraph()
            company_name=company_data.get('name','CraftRMN Pro'); company_address=company_data.get('address','');
            company_phone=company_data.get('phone',''); company_email=company_data.get('email','')
            parts = [part for part in [company_name, company_address, f"Tel: {company_phone}", company_email] if part]
            run = footer_para.add_run(" | ".join(parts)); run.font.name='Calibri'; run.font.size=Pt(8); run.font.color.rgb=RGBColor(0x80,0x80,0x80)
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e: print(f"Error al configurar pie de página DOCX: {e}")

    # ========================================================================
    # FUNCIÓN AUXILIAR PARA LOGO (REUTILIZABLE)
    # ========================================================================
    @staticmethod
    def _add_logo(story_or_doc, company_data: Dict, format: str):
        """Añade el logo de la empresa al story (PDF) o doc (DOCX)."""
        if not company_data: return
        company_logo_path = company_data.get('logo_path_on_server')
        if company_logo_path and Path(company_logo_path).exists():
            try:
                if format == 'pdf' and PDF_AVAILABLE:
                    logo_img = Image(company_logo_path, width=1.5*inch, height=0.75*inch)
                    logo_img.hAlign = 'LEFT'
                    story_or_doc.append(logo_img)
                    story_or_doc.append(Spacer(1, 0.2*inch))
                elif format == 'docx' and DOCX_AVAILABLE:
                    story_or_doc.add_picture(company_logo_path, width=Inches(1.5))
                    last_paragraph = story_or_doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    story_or_doc.add_paragraph() # Espacio
            except Exception as e: print(f"Error al añadir logo {format.upper()} {company_logo_path}: {e}")
        else: print(f"Advertencia {format.upper()}: Logo no encontrado en: {company_logo_path}")

    # ========================================================================
    # EXPORTACIÓN PDF INDIVIDUAL (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_pdf(results: Dict, company_data: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como PDF con gráfico y datos de empresa."""
        if not PDF_AVAILABLE: raise ImportError("ReportLab no está instalado.")
        t = TranslationManager(lang)
        output = io.BytesIO()

        doc = BaseDocTemplate(output, pagesize=A4, topMargin=0.75*inch, bottomMargin=1.0*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='main', frames=[frame], onPage=lambda canvas, doc: ReportExporter._add_pdf_footer(canvas, doc, company_data))
        doc.addPageTemplates([template])
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2c3e50'), spaceAfter=30, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)

        # PORTADA
        story.append(Paragraph(t.get('report.title', default="Reporte de Análisis RMN"), title_style))
        story.append(Spacer(1, 0.3*inch)); story.append(Paragraph(t.get('report.subtitle', default="Análisis de Espectroscopia RMN"), subtitle_style))
        story.append(Spacer(1, 0.5*inch)); story.append(Paragraph(f"<b>{t.get('report.sample', default='Muestra')}:</b> {results.get('filename', 'N/A')}", info_style))
        story.append(Paragraph(f"<b>{t.get('report.date', default='Fecha')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style)); story.append(PageBreak())

        # LOGO
        ReportExporter._add_logo(story, company_data, 'pdf')

        # GRÁFICO
        story.append(Paragraph(f"1. {t.get('report.spectrum', default='Espectro')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        if chart_image:
            try: img = Image(io.BytesIO(chart_image), width=6*inch, height=3.5*inch); img.hAlign = 'CENTER'; story.append(KeepTogether(img))
            except Exception as e: print(f"Error al añadir imagen del gráfico PDF: {e}"); story.append(Paragraph(f"[{t.get('errors.chartError', default='Error al mostrar gráfico')}]", styles['Italic']))
        else: story.append(Paragraph(f"[{t.get('errors.noChartData', default='Gráfico no disponible')}]", styles['Italic']))
        story.append(Spacer(1, 0.3*inch))

        # RESUMEN EJECUTIVO
        story.append(Paragraph(f"2. {t.get('report.executive_summary', default='Resumen Ejecutivo')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        analysis = results.get("analysis", {})
        summary_data = [
             [t.get('report.parameter', default='Parámetro'), t.get('report.value', default='Valor'), t.get('report.unit', default='Unidad')],
             [t.get('results.fluor', default='Flúor Total'), f"{analysis.get('fluor_percentage', 0):.2f}", t.get('units.percentage', default='%')],
             [t.get('results.pfas', default='PFAS'), f"{analysis.get('pifas_percentage', analysis.get('pfas_percentage', 0)):.2f}", t.get('units.percent_fluor', default='% Flúor')],
             [t.get('results.concentration', default='Concentración PFAS'), f"{analysis.get('pifas_concentration', analysis.get('pfas_concentration', 0)):.4f}", t.get('units.millimolar', default='mM')],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table); story.append(Spacer(1, 0.3*inch))
        quality_score = results.get('quality_score', 0)
        quality_text = f"<b>{t.get('report.quality_score', default='Puntuación de Calidad')}:</b> {quality_score:.1f}{t.get('units.over_ten', default='/10')}"
        story.append(Paragraph(quality_text, styles['Normal'])); story.append(PageBreak())

        # INFORMACIÓN RÁPIDA
        story.append(Paragraph(f"3. {t.get('report.quick_info', default='Información Rápida')}", styles['Heading1'])); story.append(Spacer(1, 0.1*inch))
        qm = results.get("quality_metrics", {})
        snr_value = qm.get('snr', results.get('signal_to_noise')) # Buscar en ambos sitios
        quick_info_data = [
             [t.get('report.metric', default='Métrica'), t.get('report.value', default='Valor')],
             [t.get('peaks.title', default='Picos Detectados'), str(len(results.get('peaks', [])))],
             [t.get('results.total_area', default='Área Total'), f"{analysis.get('total_area', 0):,.2f}"],
             ['SNR', f"{snr_value:.2f}" if snr_value is not None else 'N/A']
        ]
        quick_table = Table(quick_info_data, colWidths=[2.5*inch, 2*inch])
        quick_table.setStyle(TableStyle([
             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
             ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
             ('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(quick_table); story.append(PageBreak())

        # ANÁLISIS DETALLADO
        story.append(Paragraph(f"4. {t.get('report.detailed_analysis', default='Análisis Detallado')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"4.1 {t.get('report.chemical_composition', default='Composición Química')}", styles['Heading2'])); story.append(Spacer(1, 0.1*inch))
        detailed_data = [
             [t.get('report.parameter', default='Parámetro'), t.get('report.value', default='Valor'), t.get('report.unit', default='Unidad')],
             [t.get('results.total_area', default='Área Total'), f"{analysis.get('total_area', 0):,.2f}", t.get('units.arbitrary', default='u.a.')],
             [t.get('results.fluor_area', default='Área Flúor'), f"{analysis.get('fluor_area', 0):,.2f}", t.get('units.arbitrary', default='u.a.')],
             [t.get('results.pfas_area', default='Área PFAS'), f"{analysis.get('pifas_area', analysis.get('pfas_area', 0)):,.2f}", t.get('units.arbitrary', default='u.a.')],
             [t.get('results.sample_concentration', default='Concentración Muestra'), f"{results.get('sample_concentration', 0):.2f}", t.get('units.millimolar', default='mM')], # Usar results aquí
        ]
        detailed_table = Table(detailed_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        detailed_table.setStyle(TableStyle([
             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
             ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
             ('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(detailed_table); story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"4.2 {t.get('report.detailed_statistics', default='Estadísticas Detalladas')}", styles['Heading2'])); story.append(Spacer(1, 0.1*inch))
        stats_data = [
             [t.get('report.parameter', default='Parámetro'), t.get('report.value', default='Valor')],
             ['SNR', f"{snr_value:.2f}" if snr_value is not None else 'N/A'],
             [t.get('report.limits', default='Límites (Resolución)'), f"{qm.get('resolution', 0):.2f} ppm"],
             # ['FWHM', f"{qm.get('fwhm', 0):.2f} Hz"], # Descomentar si tienes FWHM
        ]
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
             ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
             ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
             ('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(stats_table); story.append(PageBreak())

        # PICOS DETECTADOS
        story.append(Paragraph(f"5. {t.get('report.detected_peaks', default='Picos Detectados')}", styles['Heading1']))
        peaks = results.get("peaks", [])
        if peaks:
            story.append(Spacer(1, 0.2*inch))
            peaks_data = [
                [t.get('peaks.ppm', default='PPM'), t.get('peaks.intensity', default='Intensidad'), t.get('peaks.relative_intensity', default='Int. Rel.'), t.get('peaks.width', default='Ancho (ppm)'), t.get('peaks.region', default='Región')]
            ]
            for peak in peaks:
                width_val = peak.get('width_ppm', peak.get('width', 0))
                peaks_data.append([
                     f"{peak.get('ppm', peak.get('position', 0)):.3f}",
                     f"{peak.get('intensity', peak.get('height', 0)):,.0f}",
                     f"{peak.get('relative_intensity', 0):.1f}{t.get('units.percentage', default='%')}",
                     f"{width_val:.3f}",
                     normalize_region_text(peak.get('region', 'N/A'))
                ])
            peaks_table = Table(peaks_data, colWidths=[0.9*inch, 1.0*inch, 1.1*inch, 0.9*inch, 2.9*inch])
            peaks_table.setStyle(TableStyle([
                 ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                 ('FONTSIZE', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 1, colors.black),
                 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('WORDWRAP', (4, 1), (4, -1), True), # Permitir wrap en la columna de región
            ]))
            story.append(peaks_table)
        else:
            story.append(Paragraph(t.get('peaks.none', default='No se detectaron picos significativos.'), styles['Normal']))

        doc.build(story); output.seek(0)
        return output

    # ========================================================================
    # EXPORTACIÓN DOCX INDIVIDUAL (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_docx(results: Dict, company_data: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como DOCX con gráfico y datos de empresa."""
        if not DOCX_AVAILABLE: raise ImportError("python-docx no está instalado.")
        t = TranslationManager(lang)
        doc = Document()
        style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)

        # PIE DE PÁGINA
        ReportExporter._add_docx_footer(doc, company_data)

        # PORTADA
        title = doc.add_heading(t.get('report.title', default="Reporte de Análisis RMN"), 0); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle = doc.add_heading(t.get('report.subtitle', default="Análisis de Espectroscopia RMN"), level=2); subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()
        info = doc.add_paragraph(); info.add_run(f"{t.get('report.sample', default='Muestra')}: ").bold = True; info.add_run(results.get('filename', 'N/A')); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_p = doc.add_paragraph(); date_p.add_run(f"{t.get('report.date', default='Fecha')}: ").bold = True; date_p.add_run(datetime.now().strftime('%d/%m/%Y %H:%M')); date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()

        # LOGO
        ReportExporter._add_logo(doc, company_data, 'docx')

        # GRÁFICO
        doc.add_heading(f"1. {t.get('report.spectrum', default='Espectro')}", level=1)
        if chart_image:
            try: doc.add_picture(io.BytesIO(chart_image), width=Inches(6)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e: print(f"Error al añadir imagen del gráfico DOCX: {e}"); doc.add_paragraph(f"[{t.get('errors.chartError', default='Error al mostrar gráfico')}]")
        else: doc.add_paragraph(f"[{t.get('errors.noChartData', default='Gráfico no disponible')}]")
        doc.add_paragraph()

        # RESUMEN EJECUTIVO
        doc.add_heading(f"2. {t.get('report.executive_summary', default='Resumen Ejecutivo')}", level=1)
        analysis = results.get("analysis", {})
        table = doc.add_table(rows=4, cols=3) # Ajusta rows
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = t.get('report.parameter', default='Parámetro')
        hdr_cells[1].text = t.get('report.value', default='Valor')
        hdr_cells[2].text = t.get('report.unit', default='Unidad')
        data_rows = [
             (t.get('results.fluor'), f"{analysis.get('fluor_percentage', 0):.2f}", t.get('units.percentage', default='%')),
             (t.get('results.pfas'), f"{analysis.get('pifas_percentage', analysis.get('pfas_percentage', 0)):.2f}", t.get('units.percent_fluor', default='% Flúor')),
             (t.get('results.concentration'), f"{analysis.get('pifas_concentration', analysis.get('pfas_concentration', 0)):.4f}", t.get('units.millimolar', default='mM')),
        ]
        for idx, (param, value, unit) in enumerate(data_rows, 1):
            if idx < len(table.rows):
                 row_cells = table.rows[idx].cells; row_cells[0].text = param; row_cells[1].text = value; row_cells[2].text = unit
        doc.add_paragraph()
        quality_score = results.get('quality_score', 0)
        quality_p = doc.add_paragraph(); quality_p.add_run(f"{t.get('report.quality_score', default='Puntuación de Calidad')}: ").bold = True
        quality_p.add_run(f"{quality_score:.1f}{t.get('units.over_ten', default='/10')}")
        doc.add_page_break()

        # INFORMACIÓN RÁPIDA
        doc.add_heading(f"3. {t.get('report.quick_info', default='Información Rápida')}", level=1)
        qm = results.get("quality_metrics", {})
        snr_value = qm.get('snr', results.get('signal_to_noise'))
        quick_table = doc.add_table(rows=4, cols=2) # Ajusta rows
        quick_table.style = 'Light Grid Accent 1'
        quick_hdr = quick_table.rows[0].cells
        quick_hdr[0].text = t.get('report.metric', default='Métrica')
        quick_hdr[1].text = t.get('report.value', default='Valor')
        quick_rows = [
            (t.get('peaks.title', default='Picos Detectados'), str(len(results.get('peaks', [])))),
            (t.get('results.total_area', default='Área Total'), f"{analysis.get('total_area', 0):,.2f}"),
            ('SNR', f"{snr_value:.2f}" if snr_value is not None else 'N/A')
        ]
        for idx, (metric, value) in enumerate(quick_rows, 1):
            if idx < len(quick_table.rows):
                 row_cells = quick_table.rows[idx].cells; row_cells[0].text = metric; row_cells[1].text = value
        doc.add_page_break()

        # ANÁLISIS DETALLADO
        doc.add_heading(f"4. {t.get('report.detailed_analysis', default='Análisis Detallado')}", level=1)
        doc.add_heading(f"4.1 {t.get('report.chemical_composition', default='Composición Química')}", level=2)
        detailed_table = doc.add_table(rows=5, cols=3) # Ajusta rows
        detailed_table.style = 'Light Grid Accent 1'
        hdr_cells_det = detailed_table.rows[0].cells
        hdr_cells_det[0].text = t.get('report.parameter'); hdr_cells_det[1].text = t.get('report.value'); hdr_cells_det[2].text = t.get('report.unit')
        detailed_rows = [
             (t.get('results.total_area'), f"{analysis.get('total_area', 0):,.2f}", t.get('units.arbitrary', default='u.a.')),
             (t.get('results.fluor_area'), f"{analysis.get('fluor_area', 0):,.2f}", t.get('units.arbitrary', default='u.a.')),
             (t.get('results.pfas_area'), f"{analysis.get('pifas_area', analysis.get('pfas_area', 0)):,.2f}", t.get('units.arbitrary', default='u.a.')),
             (t.get('results.sample_concentration'), f"{results.get('sample_concentration', 0):.2f}", t.get('units.millimolar', default='mM')),
        ]
        for idx, (param, value, unit) in enumerate(detailed_rows, 1):
            if idx < len(detailed_table.rows):
                 row_cells = detailed_table.rows[idx].cells; row_cells[0].text = param; row_cells[1].text = value; row_cells[2].text = unit
        doc.add_paragraph()
        doc.add_heading(f"4.2 {t.get('report.detailed_statistics', default='Estadísticas Detalladas')}", level=2)
        stats_table = doc.add_table(rows=3, cols=2) # Ajusta rows
        stats_table.style = 'Light Grid Accent 1'
        stats_hdr = stats_table.rows[0].cells
        stats_hdr[0].text = t.get('report.parameter'); stats_hdr[1].text = t.get('report.value')
        stats_rows = [
             ('SNR', f"{snr_value:.2f}" if snr_value is not None else 'N/A'),
             (t.get('report.limits', default='Límites (Resolución)'), f"{qm.get('resolution', 0):.2f} ppm"),
             # ('FWHM', f"{qm.get('fwhm', 0):.2f} Hz"), # Descomentar si tienes FWHM
        ]
        for idx, (param, value) in enumerate(stats_rows, 1):
             if idx < len(stats_table.rows):
                 row_cells = stats_table.rows[idx].cells; row_cells[0].text = param; row_cells[1].text = value
        doc.add_page_break()

        # PICOS DETECTADOS
        doc.add_heading(f"5. {t.get('report.detected_peaks', default='Picos Detectados')}", level=1)
        peaks = results.get("peaks", [])
        if peaks:
            peaks_table = doc.add_table(rows=len(peaks) + 1, cols=5)
            peaks_table.style = 'Light Grid Accent 1'
            widths = [0.9, 1.0, 1.1, 0.9, 2.5]
            for i, width in enumerate(widths):
                 for cell in peaks_table.columns[i].cells: cell.width = Inches(width)
            hdr_cells_peaks = peaks_table.rows[0].cells
            hdr_cells_peaks[0].text=t.get('peaks.ppm', default='PPM'); hdr_cells_peaks[1].text=t.get('peaks.intensity', default='Intensidad')
            hdr_cells_peaks[2].text=t.get('peaks.relative_intensity', default='Int. Rel.'); hdr_cells_peaks[3].text=t.get('peaks.width', default='Ancho (ppm)')
            hdr_cells_peaks[4].text=t.get('peaks.region', default='Región')
            for idx, peak in enumerate(peaks, 1):
                if idx < len(peaks_table.rows):
                    row_cells = peaks_table.rows[idx].cells
                    row_cells[0].text = f"{peak.get('ppm', peak.get('position', 0)):.3f}"
                    row_cells[1].text = f"{peak.get('intensity', peak.get('height', 0)):,.0f}"
                    row_cells[2].text = f"{peak.get('relative_intensity', 0):.1f}%"
                    width_val = peak.get('width_ppm', peak.get('width', 0))
                    row_cells[3].text = f"{width_val:.3f}"
                    row_cells[4].text = normalize_region_text(peak.get('region', 'N/A'))
        else:
            doc.add_paragraph(t.get('peaks.none', default='No se detectaron picos significativos.'))

        output = io.BytesIO(); doc.save(output); output.seek(0)
        return output

    # ========================================================================
    # EXPORTACIÓN CSV (¡FINAL!) - Reinsertado código original
    # ========================================================================
    @staticmethod
    def export_csv(results: Dict, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como CSV."""
        t = TranslationManager(lang)
        import csv

        text_buffer = io.StringIO()
        writer = csv.writer(text_buffer)

        writer.writerow([t.get('report.title', default='Reporte de Análisis RMN').upper()])
        writer.writerow([t.get('report.sample', default='Muestra'), results.get('filename', 'N/A')])
        writer.writerow([t.get('report.date', default='Fecha'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        # RESUMEN
        writer.writerow([t.get('report.executive_summary', default='Resumen Ejecutivo').upper()])
        analysis = results.get("analysis", {})
        writer.writerow([t.get('report.parameter'), t.get('report.value'), t.get('report.unit')])
        writer.writerow([t.get('results.fluor'), f"{analysis.get('fluor_percentage', 0):.2f}", t.get('units.percentage', default='%')])
        writer.writerow([t.get('results.pfas'), f"{analysis.get('pifas_percentage', analysis.get('pfas_percentage', 0)):.2f}", t.get('units.percent_fluor', default='% Flúor')])
        writer.writerow([t.get('results.concentration'), f"{analysis.get('pifas_concentration', analysis.get('pfas_concentration', 0)):.4f}", t.get('units.millimolar', default='mM')])
        writer.writerow([t.get('report.quality_score'), f"{results.get('quality_score', 0):.1f}", t.get('units.over_ten', default='/10')])
        writer.writerow([])

        # PICOS
        peaks = results.get("peaks", [])
        if peaks:
            writer.writerow([t.get('report.detected_peaks', default='Picos Detectados').upper()])
            writer.writerow([t.get('peaks.ppm'), t.get('peaks.intensity'), t.get('peaks.relative_intensity'), t.get('peaks.width', default='Ancho (ppm)'), t.get('peaks.region')])
            for peak in peaks:
                width_val = peak.get('width_ppm', peak.get('width', 0))
                writer.writerow([
                     f"{peak.get('ppm', peak.get('position', 0)):.3f}",
                     f"{peak.get('intensity', peak.get('height', 0)):,.0f}",
                     f"{peak.get('relative_intensity', 0):.1f}",
                     f"{width_val:.3f}",
                     normalize_region_text(peak.get('region', 'N/A'))
                ])

        byte_buffer = io.BytesIO()
        byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        text_buffer.close()
        return byte_buffer

    # ========================================================================
    # EXPORTACIÓN DE COMPARACIÓN PDF (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_comparison_pdf(samples: List[Dict], company_data: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta comparación como PDF con gráfico y branding."""
        if not PDF_AVAILABLE: raise ImportError("ReportLab no está instalado.")
        t = TranslationManager(lang)
        output = io.BytesIO()

        doc = BaseDocTemplate(output, pagesize=A4, topMargin=0.75*inch, bottomMargin=1.0*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='main', frames=[frame], onPage=lambda canvas, doc: ReportExporter._add_pdf_footer(canvas, doc, company_data))
        doc.addPageTemplates([template])
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2c3e50'), spaceAfter=30, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)

        # PORTADA
        story.append(Paragraph(t.get('comparison.title', default="Comparación de Muestras RMN"), title_style))
        subtitle_text = t.get('comparison.subtitle', default=f"Análisis Comparativo de {len(samples)} Muestras")
        # Si el texto contiene {count}, reemplazarlo
        if '{count}' in subtitle_text:
            subtitle_text = subtitle_text.replace('{count}', str(len(samples)))
        story.append(Spacer(1, 0.3*inch)); story.append(Paragraph(subtitle_text, subtitle_style))
        story.append(Spacer(1, 0.5*inch)); story.append(Paragraph(f"<b>{t.get('report.date', default='Fecha')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())

        # LOGO
        ReportExporter._add_logo(story, company_data, 'pdf')

        # MUESTRAS INCLUIDAS
        story.append(Paragraph(f"1. {t.get('comparison.samples_included', default='Muestras Incluidas')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        sample_list_style = ParagraphStyle('SampleList', parent=styles['Normal'], leftIndent=0.2*inch)
        for idx, sample in enumerate(samples, 1): story.append(Paragraph(f"{idx}. {sample.get('filename', sample.get('name', 'N/A'))}", sample_list_style))
        story.append(PageBreak())

        # GRÁFICO COMPARATIVO
        story.append(Paragraph(f"2. {t.get('comparison.chart', default='Gráfico Comparativo')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        if chart_image:
            try: img = Image(io.BytesIO(chart_image), width=6.5*inch, height=4*inch); img.hAlign = 'CENTER'; story.append(KeepTogether(img))
            except Exception as e: print(f"Error al añadir imagen del gráfico Comp PDF: {e}"); story.append(Paragraph(f"[{t.get('errors.chartError', default='Error al mostrar gráfico')}]", styles['Italic']))
        else: story.append(Paragraph(f"[{t.get('errors.noChartData', default='Gráfico no disponible')}]", styles['Italic']))
        story.append(PageBreak())

        # TABLA COMPARATIVA
        story.append(Paragraph(f"3. {t.get('comparison.table', default='Tabla Comparativa')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        table_data = [[t.get('report.parameter', default='Parámetro')] + [s.get('filename', s.get('name', 'N/A'))[:15] for s in samples]]
        params = [
            (f"{t.get('results.fluor', default='Flúor Total')} ({t.get('units.percentage', default='%')})", 'fluor'),
            (f"{t.get('results.pfas', default='PFAS')} ({t.get('units.percent_fluor', default='% Flúor')})", 'pfas'),
            (f"{t.get('results.concentration', default='Concentración PFAS')} ({t.get('units.millimolar', default='mM')})", 'concentration'),
            (f"{t.get('results.quality', default='Calidad')} ({t.get('units.over_ten', default='/10')})", 'quality')
        ]
        for param_name, param_key in params:
            row = [param_name]
            for sample in samples:
                value = sample.get(param_key)
                if value is None and param_key == 'pfas': value = sample.get('pifas_percentage')
                if value is None and param_key == 'concentration': value = sample.get('pifas_concentration')
                text_value = '--'
                if value is not None:
                     try:
                         if param_key == 'concentration': text_value = f"{float(value):.4f}"
                         elif param_key == 'quality': text_value = f"{float(value):.1f}"
                         else: text_value = f"{float(value):.2f}"
                     except (ValueError, TypeError): text_value = str(value)
                row.append(text_value)
            table_data.append(row)
        num_cols = len(samples) + 1; first_col_width = 2.0 * inch
        other_col_width = (doc.width - first_col_width) / len(samples) if samples else 0.5*inch
        col_widths = [first_col_width] + [other_col_width] * len(samples)
        comparison_table = Table(table_data, colWidths=col_widths)
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(comparison_table)

        doc.build(story); output.seek(0)
        return output

    # ========================================================================
    # EXPORTACIÓN DE COMPARACIÓN DOCX (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_comparison_docx(samples: List[Dict], company_data: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta comparación como DOCX con gráfico y branding."""
        if not DOCX_AVAILABLE: raise ImportError("python-docx no está instalado.")
        t = TranslationManager(lang)
        doc = Document()
        style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)

        # PIE DE PÁGINA
        ReportExporter._add_docx_footer(doc, company_data)

        # PORTADA
        title = doc.add_heading(t.get('comparison.title', default="Comparación de Muestras RMN"), 0); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_text = t.get('comparison.subtitle', default=f"Análisis Comparativo de {len(samples)} Muestras")
        # Si el texto contiene {count}, reemplazarlo
        if '{count}' in subtitle_text:
            subtitle_text = subtitle_text.replace('{count}', str(len(samples)))
        subtitle = doc.add_heading(subtitle_text, level=2); subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(); date_p = doc.add_paragraph(f"{t.get('report.date', default='Fecha')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}"); date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()

        # LOGO
        ReportExporter._add_logo(doc, company_data, 'docx')

        # MUESTRAS INCLUIDAS
        doc.add_heading(f"1. {t.get('comparison.samples_included', default='Muestras Incluidas')}", level=1)
        for idx, sample in enumerate(samples, 1):
            try: doc.add_paragraph(f"{idx}. {sample.get('filename', sample.get('name', 'N/A'))}", style='List Number')
            except KeyError: doc.add_paragraph(f"{idx}. {sample.get('filename', sample.get('name', 'N/A'))}")
        doc.add_page_break()

        # GRÁFICO COMPARATIVO
        doc.add_heading(f"2. {t.get('comparison.chart', default='Gráfico Comparativo')}", level=1)
        if chart_image:
            try: doc.add_picture(io.BytesIO(chart_image), width=Inches(6)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e: print(f"Error al añadir imagen del gráfico Comp DOCX: {e}"); doc.add_paragraph(f"[{t.get('errors.chartError', default='Error al mostrar gráfico')}]")
        else: doc.add_paragraph(f"[{t.get('errors.noChartData', default='Gráfico no disponible')}]")
        doc.add_page_break()

        # TABLA COMPARATIVA
        doc.add_heading(f"3. {t.get('comparison.table', default='Tabla Comparativa')}", level=1)
        num_params = 4; table = doc.add_table(rows=num_params + 1, cols=len(samples) + 1); table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells; hdr_cells[0].text = t.get('report.parameter', default='Parámetro')
        for idx, sample in enumerate(samples, 1): hdr_cells[idx].text = sample.get('filename', sample.get('name', 'N/A'))[:20]
        params = [
            (f"{t.get('results.fluor', default='Flúor Total')} ({t.get('units.percentage', default='%')})", 'fluor'),
            (f"{t.get('results.pfas', default='PFAS')} ({t.get('units.percent_fluor', default='% Flúor')})", 'pfas'),
            (f"{t.get('results.concentration', default='Concentración PFAS')} ({t.get('units.millimolar', default='mM')})", 'concentration'),
            (f"{t.get('results.quality', default='Calidad')} ({t.get('units.over_ten', default='/10')})", 'quality')
        ]
        for row_idx, (param_name, param_key) in enumerate(params, 1):
             if row_idx < len(table.rows):
                 row_cells = table.rows[row_idx].cells; row_cells[0].text = param_name
                 for col_idx, sample in enumerate(samples, 1):
                     value = sample.get(param_key)
                     if value is None and param_key == 'pfas': value = sample.get('pifas_percentage')
                     if value is None and param_key == 'concentration': value = sample.get('pifas_concentration')
                     text_value = '--'
                     if value is not None:
                         try:
                             if param_key == 'concentration': text_value = f"{float(value):.4f}"
                             elif param_key == 'quality': text_value = f"{float(value):.1f}"
                             else: text_value = f"{float(value):.2f}"
                         except (ValueError, TypeError): text_value = str(value)
                     row_cells[col_idx].text = text_value

        output = io.BytesIO(); doc.save(output); output.seek(0)
        return output

    # ========================================================================
    # EXPORTACIÓN DE COMPARACIÓN CSV (¡FINAL!) - Reinsertado código original
    # ========================================================================
    @staticmethod
    def export_comparison_csv(samples: List[Dict], lang: str = 'es') -> BinaryIO:
         """Exporta comparación como CSV."""
         t = TranslationManager(lang)
         import csv
         text_buffer = io.StringIO()
         writer = csv.writer(text_buffer)
         writer.writerow([t.get('comparison.title', default="Comparación de Muestras RMN").upper()])
         writer.writerow([t.get('report.date', default='Fecha'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
         writer.writerow([t.get('comparison.samples_included', default='Muestras Incluidas'), len(samples)])
         writer.writerow([])
         headers = [t.get('report.parameter', default='Parámetro')] + [s.get('filename', s.get('name', 'N/A')) for s in samples]
         writer.writerow(headers)
         params = [
            (f"{t.get('results.fluor', default='Flúor Total')} ({t.get('units.percentage', default='%')})", 'fluor'),
            (f"{t.get('results.pfas', default='PFAS')} ({t.get('units.percent_fluor', default='% Flúor')})", 'pfas'),
            (f"{t.get('results.concentration', default='Concentración PFAS')} ({t.get('units.millimolar', default='mM')})", 'concentration'),
            (f"{t.get('results.quality', default='Calidad')} ({t.get('units.over_ten', default='/10')})", 'quality')
         ]
         for param_name, param_key in params:
             row = [param_name]
             for sample in samples:
                 value = sample.get(param_key)
                 if value is None and param_key == 'pfas': value = sample.get('pifas_percentage')
                 if value is None and param_key == 'concentration': value = sample.get('pifas_concentration')
                 text_value = '--'
                 if value is not None:
                     try:
                         if param_key == 'concentration': text_value = f"{float(value):.4f}"
                         elif param_key == 'quality': text_value = f"{float(value):.1f}"
                         else: text_value = f"{float(value):.2f}"
                     except (ValueError, TypeError): text_value = str(value)
                 row.append(text_value)
             writer.writerow(row)
         byte_buffer = io.BytesIO()
         byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
         byte_buffer.seek(0)
         text_buffer.close()
         return byte_buffer

    # ========================================================================
    # EXPORTACIÓN DE DASHBOARD PDF (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_dashboard_pdf(stats: Dict, company_data: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:
        """Exporta dashboard como PDF con gráficos y branding."""
        if not PDF_AVAILABLE: raise ImportError("ReportLab no está instalado.")
        t = TranslationManager(lang)
        output = io.BytesIO()

        doc = BaseDocTemplate(output, pagesize=A4, topMargin=0.75*inch, bottomMargin=1.0*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='main', frames=[frame], onPage=lambda canvas, doc: ReportExporter._add_pdf_footer(canvas, doc, company_data))
        doc.addPageTemplates([template])
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2c3e50'), spaceAfter=30, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)

        # PORTADA
        story.append(Paragraph(t.get('dashboard.title', default="Panel de Control"), title_style))
        story.append(Spacer(1, 0.3*inch)); story.append(Paragraph(t.get('dashboard.subtitle', default="Resumen Estadístico"), subtitle_style))
        story.append(Spacer(1, 0.5*inch)); story.append(Paragraph(f"<b>{t.get('report.date', default='Fecha')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())

        # LOGO
        ReportExporter._add_logo(story, company_data, 'pdf')

        # ESTADÍSTICAS GENERALES
        story.append(Paragraph(f"1. {t.get('dashboard.general_stats', default='Estadísticas Generales')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        stats_report_data = [
            [t.get('report.metric', default='Métrica'), t.get('report.value', default='Valor')],
            [t.get('dashboard.totalAnalyses', default='Total Análisis'), str(stats.get('totalAnalyses', 0))],
            [t.get('dashboard.avgFluor', default='Flúor Promedio'), f"{stats.get('avgFluor', 0):.2f}{t.get('units.percentage', default='%')}"],
            [t.get('dashboard.avgPfas', default='PFAS Promedio'), f"{stats.get('avgPfas', 0):.2f}{t.get('units.percentage', default='%')}"],
            [t.get('dashboard.avgConcentration', default='Concentración Promedio'), f"{stats.get('avgConcentration', 0):.4f} {t.get('units.millimolar', default='mM')}"],
            [t.get('dashboard.avgQuality', default='Calidad Promedia'), f"{stats.get('avgQuality', 0):.1f}{t.get('units.over_ten', default='/10')}"],
            [t.get('dashboard.highQuality', default='Muestras Alta Calidad'), str(stats.get('highQualitySamples', 0))],
            [t.get('dashboard.avg_snr', default='SNR Promedio'), f"{stats.get('avgSNR', stats.get('avg_snr', 0)):.2f}" if stats.get('avgSNR', stats.get('avg_snr')) is not None else 'N/A']
        ]
        stats_table = Table(stats_report_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(stats_table); story.append(PageBreak())

        # GRÁFICOS
        story.append(Paragraph(f"2. {t.get('dashboard.charts', default='Gráficos')}", styles['Heading1'])); story.append(Spacer(1, 0.2*inch))
        if chart_images:
            if 'trend' in chart_images and chart_images['trend']:
                 story.append(Paragraph(f"2.1 {t.get('dashboard.trend', default='Tendencia')}", styles['Heading2'])); story.append(Spacer(1, 0.1*inch))
                 try: img = Image(io.BytesIO(chart_images['trend']), width=6*inch, height=3.5*inch); img.hAlign='CENTER'; story.append(KeepTogether(img))
                 except Exception as e: print(f"Error al añadir gráfico Trend PDF: {e}")
                 story.append(Spacer(1, 0.3*inch))

            if 'distribution' in chart_images and chart_images['distribution']:
                 story.append(Paragraph(f"2.2 {t.get('dashboard.distribution', default='Distribución')}", styles['Heading2'])); story.append(Spacer(1, 0.1*inch))
                 try: img = Image(io.BytesIO(chart_images['distribution']), width=6*inch, height=3.5*inch); img.hAlign='CENTER'; story.append(KeepTogether(img))
                 except Exception as e: print(f"Error al añadir gráfico Dist PDF: {e}")
        else: story.append(Paragraph(f"[{t.get('errors.noChartData', default='Gráficos no disponibles')}]", styles['Italic']))

        doc.build(story); output.seek(0)
        return output

    # ========================================================================
    # EXPORTACIÓN DE DASHBOARD DOCX (¡FINAL!)
    # ========================================================================
    @staticmethod
    def export_dashboard_docx(stats: Dict, company_data: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:
        """Exporta dashboard como DOCX con gráficos y branding."""
        if not DOCX_AVAILABLE: raise ImportError("python-docx no está instalado.")
        t = TranslationManager(lang)
        doc = Document()
        style = doc.styles['Normal']; style.font.name = 'Calibri'; style.font.size = Pt(11)

        # PIE DE PÁGINA
        ReportExporter._add_docx_footer(doc, company_data)

        # PORTADA
        title = doc.add_heading(t.get('dashboard.title', default="Panel de Control"), 0); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle = doc.add_heading(t.get('dashboard.subtitle', default="Resumen Estadístico"), level=2); subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(); date_p = doc.add_paragraph(f"{t.get('report.date', default='Fecha')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}"); date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()

        # LOGO
        ReportExporter._add_logo(doc, company_data, 'docx')

        # ESTADÍSTICAS GENERALES
        doc.add_heading(f"1. {t.get('dashboard.general_stats', default='Estadísticas Generales')}", level=1)
        stats_report_data = [
            (t.get('dashboard.totalAnalyses', default='Total Análisis'), str(stats.get('totalAnalyses', 0))),
            (t.get('dashboard.avgFluor', default='Flúor Promedio'), f"{stats.get('avgFluor', 0):.2f}{t.get('units.percentage', default='%')}" ),
            (t.get('dashboard.avgPfas', default='PFAS Promedio'), f"{stats.get('avgPfas', 0):.2f}{t.get('units.percentage', default='%')}"),
            (t.get('dashboard.avgConcentration', default='Concentración Promedio'), f"{stats.get('avgConcentration', 0):.4f} {t.get('units.millimolar', default='mM')}"),
            (t.get('dashboard.avgQuality', default='Calidad Promedia'), f"{stats.get('avgQuality', 0):.1f}{t.get('units.over_ten', default='/10')}"),
            (t.get('dashboard.highQuality', default='Muestras Alta Calidad'), str(stats.get('highQualitySamples', 0))),
            (t.get('dashboard.avg_snr', default='SNR Promedio'), f"{stats.get('avgSNR', stats.get('avg_snr', 0)):.2f}" if stats.get('avgSNR', stats.get('avg_snr')) is not None else 'N/A')
        ]
        table = doc.add_table(rows=len(stats_report_data) + 1, cols=2)
        table.style = 'Light Grid Accent 1'
        hdr_cells_dash = table.rows[0].cells
        hdr_cells_dash[0].text = t.get('report.metric', default='Métrica')
        hdr_cells_dash[1].text = t.get('report.value', default='Valor')
        for idx, (metric, value) in enumerate(stats_report_data, 1):
             if idx < len(table.rows):
                 row_cells = table.rows[idx].cells; row_cells[0].text = metric; row_cells[1].text = value
        doc.add_page_break()

        # GRÁFICOS
        doc.add_heading(f"2. {t.get('dashboard.charts', default='Gráficos')}", level=1)
        if chart_images:
             if 'trend' in chart_images and chart_images['trend']:
                 doc.add_heading(f"2.1 {t.get('dashboard.trend', default='Tendencia')}", level=2)
                 try: doc.add_picture(io.BytesIO(chart_images['trend']), width=Inches(6)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER; doc.add_paragraph()
                 except Exception as e: print(f"Error al añadir gráfico Trend DOCX: {e}")

             if 'distribution' in chart_images and chart_images['distribution']:
                 doc.add_heading(f"2.2 {t.get('dashboard.distribution', default='Distribución')}", level=2)
                 try: doc.add_picture(io.BytesIO(chart_images['distribution']), width=Inches(6)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                 except Exception as e: print(f"Error al añadir gráfico Dist DOCX: {e}")
        else: doc.add_paragraph(f"[{t.get('errors.noChartData', default='Gráficos no disponibles')}]")

        output = io.BytesIO(); doc.save(output); output.seek(0)
        return output