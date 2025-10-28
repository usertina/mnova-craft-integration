# backend/export_utils.py

"""
Utilidades de Exportación Mejoradas - CraftRMN Pro
Genera reportes completos con gráficos en PDF, DOCX y CSV
"""

import io
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, BinaryIO

import plotly.graph_objects as go
from plotly.io import to_image
from translation_manager import TranslationManager

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT



# ============================================================================
# FUNCIÓN AUXILIAR PARA NORMALIZAR UNICODE
# ============================================================================

def normalize_region_text(text: str) -> str:
    """
    Convierte caracteres Unicode de subíndices/superíndices a texto normal
    para compatibilidad con fuentes PDF estándar.
    
    CF₂ -> CF2
    CF₃ -> CF3
    COO⁻ -> COO-
    """
    replacements = {
        '\u2082': '2',  # ₂ -> 2
        '\u2083': '3',  # ₃ -> 3
        '\u207b': '-',  # ⁻ -> -
        '₂': '2',
        '₃': '3',
        '⁻': '-',
        'ó': 'o',
    }
    
    result = text
    for unicode_char, replacement in replacements.items():
        result = result.replace(unicode_char, replacement)
    
    return result


class ReportExporter:
    """Clase mejorada para exportar análisis RMN con gráficos"""
    
    # ========================================================================
    # EXPORTACIÓN JSON
    # ========================================================================
    
    @staticmethod
    def export_json(results: Dict, lang: str = 'es') -> BinaryIO:
        """Exporta resultados como JSON"""
        output = io.BytesIO()
        json_str = json.dumps(results, indent=2, ensure_ascii=False)
        output.write(json_str.encode('utf-8'))
        output.seek(0)
        return output
    
    # ========================================================================
    # UTILIDADES PARA GRÁFICOS
    # ========================================================================
    
    @staticmethod
    def plotly_to_image(plotly_json: Dict, format='png', width=800, height=500) -> bytes:
        """Convierte un gráfico Plotly (JSON) a imagen"""
        try:
            fig = go.Figure(plotly_json)
            img_bytes = to_image(fig, format=format, width=width, height=height, scale=2)
            return img_bytes
        except Exception as e:
            print(f"Error convirtiendo gráfico Plotly: {e}")
            return None
    
    @staticmethod
    def base64_to_bytes(base64_str: str) -> bytes:
        """Convierte string base64 a bytes"""
        try:
            # Remover prefijo "data:image/png;base64," si existe
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            return base64.b64decode(base64_str)
        except Exception as e:
            print(f"Error decodificando base64: {e}")
            return None
    
    # ========================================================================
    # EXPORTACIÓN DE ANÁLISIS INDIVIDUAL
    # ========================================================================
    
    @staticmethod
    def export_pdf(results: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como PDF con gráfico"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        output = io.BytesIO()
        
        doc = SimpleDocTemplate(
            output, pagesize=A4,
            topMargin=0.75*inch, bottomMargin=0.75*inch,
            leftMargin=0.75*inch, rightMargin=0.75*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # ===== PORTADA =====
        story.append(Paragraph(t('report.title'), title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph(t('report.subtitle'), subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>{t('report.sample')}:</b> {results.get('filename', 'N/A')}", info_style))
        story.append(Paragraph(f"<b>{t('report.date')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # ===== GRÁFICO DEL ESPECTRO =====
        if chart_image:
            story.append(Paragraph(f"1. {t('report.spectrum')}", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            img = Image(io.BytesIO(chart_image), width=6*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
        
        # ===== RESUMEN EJECUTIVO =====
        story.append(Paragraph(f"2. {t('report.executive_summary')}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        analysis = results.get("analysis", {})
        
        summary_data = [
            [t('report.parameter'), t('report.value'), t('report.unit')],
            [t('results.fluor'), f"{analysis.get('fluor_percentage', 0):.2f}", t('units.percentage')],
            [t('results.pfas'), f"{analysis.get('pifas_percentage', 0):.2f}", t('units.percent_fluor')],
            [t('results.concentration'), f"{analysis.get('pifas_concentration', 0):.4f}", t('units.millimolar')],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        quality_text = f"<b>{t('report.quality_score')}:</b> {results.get('quality_score', 0):.1f}{t('units.over_ten')}"
        story.append(Paragraph(quality_text, styles['Normal']))
        story.append(PageBreak())

        # ===== INFORMACIÓN RÁPIDA ===== 
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"3. {t('report.quick_info')}", styles['Heading1']))
        story.append(Spacer(1, 0.1*inch))

        quick_info_data = [
            [t('report.metric'), t('report.value')],
            [t('peaks.title'), str(len(results.get('peaks', [])))],
            [t('results.total_area'), f"{analysis.get('total_area', 0):,.2f}"],
            ['SNR', f"{results.get('quality_metrics', {}).get('snr', 0):.2f}"]
        ]

        quick_table = Table(quick_info_data, colWidths=[2.5*inch, 2*inch])
        quick_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(quick_table)
        story.append(PageBreak())
        
        # ===== ANÁLISIS DETALLADO =====
        story.append(Paragraph(f"4. {t('report.detailed_analysis')}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"4.1 {t('report.chemical_composition')}", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        detailed_data = [
            [t('report.parameter'), t('report.value'), t('report.unit')],
            [t('results.total_area'), f"{analysis.get('total_area', 0):,.2f}", t('units.arbitrary')],
            [t('results.fluor_area'), f"{analysis.get('fluor_area', 0):,.2f}", t('units.arbitrary')],
            [t('results.pfas_area'), f"{analysis.get('pifas_area', 0):,.2f}", t('units.arbitrary')],
            [t('results.sample_concentration'), f"{results.get('sample_concentration', 0):.2f}", t('units.millimolar')],
        ]
        
        detailed_table = Table(detailed_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(detailed_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ===== ESTADÍSTICAS DETALLADAS =====
        story.append(Paragraph(f"4.2 {t('report.detailed_statistics')}", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        qm = results.get("quality_metrics", {})
        
        stats_data = [
            [t('report.parameter'), t('report.value')],
            ['SNR', f"{qm.get('snr', 0):.2f}"],
            [t('report.limits'), f"{qm.get('resolution', 0):.2f} ppm"],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(stats_table)
        story.append(PageBreak())
        
        # ===== PICOS DETECTADOS =====
        peaks = results.get("peaks", [])
        if peaks:
            story.append(Paragraph(f"5. {t('report.detected_peaks')}", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            peaks_data = [
                [t('peaks.ppm'), t('peaks.intensity'), t('peaks.relative_intensity'), t('peaks.width'), t('peaks.region')]
            ]
            
            for peak in peaks:
                peaks_data.append([
                    f"{peak.get('ppm', 0):.2f}",
                    f"{peak.get('intensity', 0):,.0f}",
                    f"{peak.get('relative_intensity', 0):.1f}{t('units.percentage')}",
                    f"{peak.get('width_ppm', 0):.3f}",
                    normalize_region_text(peak.get('region', 'N/A'))
                ])
            
            peaks_table = Table(peaks_data, colWidths=[0.9*inch, 1.0*inch, 1.1*inch, 0.9*inch, 2.9*inch])
            peaks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            
            story.append(peaks_table)
        else:
            story.append(Paragraph(f"5. {t('report.detected_peaks')}", styles['Heading1']))
            story.append(Paragraph(t('peaks.none'), styles['Normal']))
        
        doc.build(story)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_docx(results: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como DOCX con gráfico"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # PORTADA
        title = doc.add_heading(t('report.title'), 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(t('report.subtitle'), level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        
        info = doc.add_paragraph()
        info.add_run(f"{t('report.sample')}: ").bold = True
        info.add_run(results.get('filename', 'N/A'))
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        date_p = doc.add_paragraph()
        date_p.add_run(f"{t('report.date')}: ").bold = True
        date_p.add_run(datetime.now().strftime('%d/%m/%Y %H:%M'))
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # GRÁFICO DEL ESPECTRO
        if chart_image:
            doc.add_heading(f"1. {t('report.spectrum')}", level=1)
            doc.add_picture(io.BytesIO(chart_image), width=Inches(6))
            doc.add_paragraph()
        
        # RESUMEN EJECUTIVO
        doc.add_heading(f"2. {t('report.executive_summary')}", level=1)
        
        analysis = results.get("analysis", {})
        
        table = doc.add_table(rows=4, cols=3)
        table.style = 'Light Grid Accent 1'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = t('report.parameter')
        hdr_cells[1].text = t('report.value')
        hdr_cells[2].text = t('report.unit')
        
        data_rows = [
            (t('results.fluor'), f"{analysis.get('fluor_percentage', 0):.2f}", t('units.percentage')),
            (t('results.pfas'), f"{analysis.get('pifas_percentage', 0):.2f}", t('units.percent_fluor')),
            (t('results.concentration'), f"{analysis.get('pifas_concentration', 0):.4f}", t('units.millimolar')),
        ]
        
        for idx, (param, value, unit) in enumerate(data_rows, 1):
            row_cells = table.rows[idx].cells
            row_cells[0].text = param
            row_cells[1].text = value
            row_cells[2].text = unit
        
        doc.add_paragraph()
        quality_p = doc.add_paragraph()
        quality_p.add_run(f"{t('report.quality_score')}: ").bold = True
        quality_p.add_run(f"{results.get('quality_score', 0):.1f}{t('units.over_ten')}")
        
        doc.add_page_break()
        
        # INFORMACIÓN RÁPIDA
        doc.add_heading(t('report.quick_info'), level=2)
        
        quick_table = doc.add_table(rows=4, cols=2)
        quick_table.style = 'Light Grid Accent 1'
        
        quick_hdr = quick_table.rows[0].cells
        quick_hdr[0].text = t('report.metric')
        quick_hdr[1].text = t('report.value')
        
        quick_rows = [
            (t('peaks.title'), str(len(results.get('peaks', [])))),
            (t('results.total_area'), f"{analysis.get('total_area', 0):,.2f}"),
            ('SNR', f"{results.get('quality_metrics', {}).get('snr', 0):.2f}")
        ]
        
        for idx, (metric, value) in enumerate(quick_rows, 1):
            row_cells = quick_table.rows[idx].cells
            row_cells[0].text = metric
            row_cells[1].text = value
        
        doc.add_page_break()
        
        # ANÁLISIS DETALLADO
        doc.add_heading(f"4. {t('report.detailed_analysis')}", level=1)
        doc.add_heading(f"4.1 {t('report.chemical_composition')}", level=2)
        
        detailed_table = doc.add_table(rows=5, cols=3)
        detailed_table.style = 'Light Grid Accent 1'
        
        hdr_cells = detailed_table.rows[0].cells
        hdr_cells[0].text = t('report.parameter')
        hdr_cells[1].text = t('report.value')
        hdr_cells[2].text = t('report.unit')
        
        detailed_rows = [
            (t('results.total_area'), f"{analysis.get('total_area', 0):,.2f}", t('units.arbitrary')),
            (t('results.fluor_area'), f"{analysis.get('fluor_area', 0):,.2f}", t('units.arbitrary')),
            (t('results.pfas_area'), f"{analysis.get('pifas_area', 0):,.2f}", t('units.arbitrary')),
            (t('results.sample_concentration'), f"{results.get('sample_concentration', 0):.2f}", t('units.millimolar')),
        ]
        
        for idx, (param, value, unit) in enumerate(detailed_rows, 1):
            row_cells = detailed_table.rows[idx].cells
            row_cells[0].text = param
            row_cells[1].text = value
            row_cells[2].text = unit
        
        doc.add_paragraph()
        
        # ESTADÍSTICAS DETALLADAS
        doc.add_heading(f"4.2 {t('report.detailed_statistics')}", level=2)
        
        qm = results.get("quality_metrics", {})
        stats_table = doc.add_table(rows=3, cols=2)
        stats_table.style = 'Light Grid Accent 1'
        
        stats_hdr = stats_table.rows[0].cells
        stats_hdr[0].text = t('report.parameter')
        stats_hdr[1].text = t('report.value')
        
        stats_rows = [
            ('SNR', f"{qm.get('snr', 0):.2f}"),
            (t('report.limits'), f"{qm.get('resolution', 0):.2f} ppm"),
        ]
        
        for idx, (param, value) in enumerate(stats_rows, 1):
            row_cells = stats_table.rows[idx].cells
            row_cells[0].text = param
            row_cells[1].text = value
        
        doc.add_page_break()
        
        # PICOS DETECTADOS
        peaks = results.get("peaks", [])
        doc.add_heading(f"5. {t('report.detected_peaks')}", level=1)
        
        if peaks:
            peaks_table = doc.add_table(rows=len(peaks)+1, cols=5)
            peaks_table.style = 'Light Grid Accent 1'
            
            # Ajustar anchos de columna para mejor visualización
            for row in peaks_table.rows:
                row.cells[0].width = Inches(0.9)  # PPM
                row.cells[1].width = Inches(1.0)  # Intensity
                row.cells[2].width = Inches(1.1)  # Relative Int
                row.cells[3].width = Inches(0.9)  # Width
                row.cells[4].width = Inches(3.0)  # Region (más ancha)
            
            hdr_cells = peaks_table.rows[0].cells
            hdr_cells[0].text = t('peaks.ppm')
            hdr_cells[1].text = t('peaks.intensity')
            hdr_cells[2].text = t('peaks.relative_intensity')
            hdr_cells[3].text = t('peaks.width')
            hdr_cells[4].text = t('peaks.region')
            
            for idx, peak in enumerate(peaks, 1):
                row_cells = peaks_table.rows[idx].cells
                row_cells[0].text = f"{peak.get('ppm', 0):.2f}"
                row_cells[1].text = f"{peak.get('intensity', 0):,.0f}"
                row_cells[2].text = f"{peak.get('relative_intensity', 0):.1f}{t('units.percentage')}"
                row_cells[3].text = f"{peak.get('width_ppm', 0):.3f}"
                row_cells[4].text = normalize_region_text(peak.get('region', 'N/A'))
        else:
            doc.add_paragraph(t('peaks.none'))
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_csv(results: Dict, lang: str = 'es') -> BinaryIO:
        """Exporta análisis individual como CSV"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        import csv
        
        text_buffer = io.StringIO()
        writer = csv.writer(text_buffer)
        
        writer.writerow([t('report.title').upper()])
        writer.writerow([t('report.sample'), results.get('filename', 'N/A')])
        writer.writerow([t('report.date'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        
        # RESUMEN
        writer.writerow([t('report.executive_summary').upper()])
        analysis = results.get("analysis", {})
        
        writer.writerow([t('report.parameter'), t('report.value'), t('report.unit')])
        writer.writerow([t('results.fluor'), f"{analysis.get('fluor_percentage', 0):.2f}", t('units.percentage')])
        writer.writerow([t('results.pfas'), f"{analysis.get('pifas_percentage', 0):.2f}", t('units.percent_fluor')])
        writer.writerow([t('results.concentration'), f"{analysis.get('pifas_concentration', 0):.4f}", t('units.millimolar')])
        writer.writerow([t('report.quality_score'), f"{results.get('quality_score', 0):.1f}", t('units.over_ten')])
        writer.writerow([])
        
        # PICOS
        peaks = results.get("peaks", [])
        if peaks:
            writer.writerow([t('report.detected_peaks').upper()])
            writer.writerow([t('peaks.ppm'), t('peaks.intensity'), t('peaks.relative_intensity'), t('peaks.width'), t('peaks.region')])
            
            for peak in peaks:
                writer.writerow([
                    f"{peak.get('ppm', 0):.2f}",
                    f"{peak.get('intensity', 0):,.0f}",
                    f"{peak.get('relative_intensity', 0):.1f}",
                    f"{peak.get('width_ppm', 0):.3f}",
                    normalize_region_text(peak.get('region', 'N/A'))
                ])
        
        byte_buffer = io.BytesIO()
        byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        text_buffer.close()
        
        return byte_buffer
    
    # ========================================================================
    # EXPORTACIÓN DE COMPARACIÓN DE MUESTRAS
    # ========================================================================
    
    @staticmethod
    def export_comparison_pdf(samples: List[Dict], chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta comparación de múltiples muestras como PDF con gráfico"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        output = io.BytesIO()
        
        doc = SimpleDocTemplate(
            output, pagesize=A4,
            topMargin=0.75*inch, bottomMargin=0.75*inch,
            leftMargin=0.75*inch, rightMargin=0.75*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # PORTADA
        story.append(Paragraph(t('comparison.title'), title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph(t('comparison.subtitle', {'count': len(samples)}), subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>{t('report.date')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # MUESTRAS INCLUIDAS
        story.append(Paragraph(f"1. {t('comparison.samples_included')}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, sample in enumerate(samples, 1):
            story.append(Paragraph(f"{idx}. {sample.get('filename', sample.get('name', 'N/A'))}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(PageBreak())
        
        # GRÁFICO COMPARATIVO
        if chart_image:
            story.append(Paragraph(f"2. {t('comparison.chart')}", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            img = Image(io.BytesIO(chart_image), width=6.5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())
        
        # TABLA COMPARATIVA
        story.append(Paragraph(f"3. {t('comparison.table')}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Preparar datos
        table_data = [[t('report.parameter')] + [s.get('filename', s.get('name', 'N/A'))[:15] for s in samples]]
        
        params = [
            (t('results.fluor') + f" ({t('units.percentage')})", 'fluor'),
            (t('results.pfas') + f" ({t('units.percent_fluor')})", 'pfas'),
            (t('results.concentration') + f" ({t('units.millimolar')})", 'concentration'),
            (t('results.quality') + f" ({t('units.over_ten')})", 'quality')
        ]
        
        for param_name, param_key in params:
            row = [param_name]
            for sample in samples:
                value = sample.get(param_key, 0)
                if param_key == 'concentration':
                    row.append(f"{value:.4f}" if value else '--')
                elif param_key == 'quality':
                    row.append(f"{value:.1f}" if value else '--')
                else:
                    row.append(f"{value:.2f}" if value else '--')
            table_data.append(row)
        
        col_width = 6.5*inch / (len(samples) + 1)
        comparison_table = Table(table_data, colWidths=[col_width] * (len(samples) + 1))
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        
        story.append(comparison_table)
        
        doc.build(story)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_comparison_docx(samples: List[Dict], chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
        """Exporta comparación de múltiples muestras como DOCX con gráfico"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # PORTADA
        title = doc.add_heading(t('comparison.title'), 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(t('comparison.subtitle', {'count': len(samples)}), level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        date_p = doc.add_paragraph(f"{t('report.date')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # MUESTRAS INCLUIDAS
        doc.add_heading(f"1. {t('comparison.samples_included')}", level=1)
        
        for idx, sample in enumerate(samples, 1):
            doc.add_paragraph(f"{idx}. {sample.get('filename', sample.get('name', 'N/A'))}", style='List Number')
        
        doc.add_page_break()
        
        # GRÁFICO COMPARATIVO
        if chart_image:
            doc.add_heading(f"2. {t('comparison.chart')}", level=1)
            doc.add_picture(io.BytesIO(chart_image), width=Inches(6))
            doc.add_page_break()
        
        # TABLA COMPARATIVA
        doc.add_heading(f"3. {t('comparison.table')}", level=1)
        
        table = doc.add_table(rows=5, cols=len(samples)+1)
        table.style = 'Light Grid Accent 1'
        
        # Encabezados
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = t('report.parameter')
        for idx, sample in enumerate(samples, 1):
            hdr_cells[idx].text = sample.get('filename', sample.get('name', 'N/A'))[:20]
        
        # Datos
        params = [
            (t('results.fluor') + f" ({t('units.percentage')})", 'fluor', False),
            (t('results.pfas') + f" ({t('units.percent_fluor')})", 'pfas', False),
            (t('results.concentration') + f" ({t('units.millimolar')})", 'concentration', True),
            (t('results.quality') + f" ({t('units.over_ten')})", 'quality', False)
        ]
        
        for row_idx, (param_name, param_key, is_concentration) in enumerate(params, 1):
            row_cells = table.rows[row_idx].cells
            row_cells[0].text = param_name
            
            for col_idx, sample in enumerate(samples, 1):
                value = sample.get(param_key, 0)
                if is_concentration:
                    row_cells[col_idx].text = f"{value:.4f}" if value else '--'
                elif param_key == 'quality':
                    row_cells[col_idx].text = f"{value:.1f}" if value else '--'
                else:
                    row_cells[col_idx].text = f"{value:.2f}" if value else '--'
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_comparison_csv(samples: List[Dict], lang: str = 'es') -> BinaryIO:
        """Exporta comparación de múltiples muestras como CSV"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        import csv
        
        text_buffer = io.StringIO()
        writer = csv.writer(text_buffer)
        
        writer.writerow([t('comparison.title').upper()])
        writer.writerow([t('report.date'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([t('comparison.samples_included'), len(samples)])
        writer.writerow([])
        
        # Encabezados
        headers = [t('report.parameter')] + [s.get('filename', s.get('name', 'N/A')) for s in samples]
        writer.writerow(headers)
        
        # Datos
        params = [
            (t('results.fluor') + f" ({t('units.percentage')})", 'fluor'),
            (t('results.pfas') + f" ({t('units.percent_fluor')})", 'pfas'),
            (t('results.concentration') + f" ({t('units.millimolar')})", 'concentration'),
            (t('results.quality') + f" ({t('units.over_ten')})", 'quality')
        ]
        
        for param_name, param_key in params:
            row = [param_name]
            for sample in samples:
                value = sample.get(param_key, 0)
                if param_key == 'concentration':
                    row.append(f"{value:.4f}" if value else '--')
                elif param_key == 'quality':
                    row.append(f"{value:.1f}" if value else '--')
                else:
                    row.append(f"{value:.2f}" if value else '--')
            writer.writerow(row)
        
        byte_buffer = io.BytesIO()
        byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        text_buffer.close()
        
        return byte_buffer
    
    # ========================================================================
    # EXPORTACIÓN DE DASHBOARD
    # ========================================================================
    
    @staticmethod
    def export_dashboard_pdf(stats: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:
        """Exporta estadísticas del dashboard como PDF con gráficos"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        output = io.BytesIO()
        
        doc = SimpleDocTemplate(
            output, pagesize=A4,
            topMargin=0.75*inch, bottomMargin=0.75*inch,
            leftMargin=0.75*inch, rightMargin=0.75*inch
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # PORTADA
        story.append(Paragraph(t('dashboard.title'), title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph(t('dashboard.subtitle'), subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>{t('report.date')}:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # ESTADÍSTICAS GENERALES
        story.append(Paragraph(f"1. {t('dashboard.general_stats')}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        stats_data = [
            [t('report.metric'), t('report.value')],
            [t('dashboard.total_analyses'), str(stats.get('totalAnalyses', 0))],
            [t('dashboard.avg_fluor'), f"{stats.get('avgFluor', 0)}{t('units.percentage')}"],
            [t('dashboard.avg_pfas'), f"{stats.get('avgPfas', 0)}{t('units.percentage')}"],
            [t('dashboard.avg_concentration'), f"{stats.get('avgConcentration', 0)} {t('units.millimolar')}"],
            [t('dashboard.avg_quality'), f"{stats.get('avgQuality', 0)}{t('units.over_ten')}"],
            [t('dashboard.high_quality'), str(stats.get('highQualitySamples', 0))],
            [t('dashboard.last_week'), str(stats.get('lastWeek', 0))],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 0.3*inch))
        story.append(PageBreak())
        
        # GRÁFICOS
        if chart_images:
            story.append(Paragraph(f"2. {t('dashboard.charts')}", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            if 'trend' in chart_images and chart_images['trend']:
                story.append(Paragraph(f"2.1 {t('dashboard.trend')}", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                img = Image(io.BytesIO(chart_images['trend']), width=6*inch, height=3.5*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            
            if 'distribution' in chart_images and chart_images['distribution']:
                story.append(Paragraph(f"2.2 {t('dashboard.distribution')}", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                img = Image(io.BytesIO(chart_images['distribution']), width=6*inch, height=3.5*inch)
                story.append(img)
        
        doc.build(story)
        output.seek(0)
        
        return output

    @staticmethod
    def export_dashboard_docx(stats: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:
        """Exporta estadísticas del dashboard como DOCX con gráficos"""
        # 🆕 Crear traductor
        t = TranslationManager(lang)
        
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # PORTADA
        title = doc.add_heading(t('dashboard.title'), 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(t('dashboard.subtitle'), level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        date_p = doc.add_paragraph(f"{t('report.date')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # ESTADÍSTICAS GENERALES
        doc.add_heading(f"1. {t('dashboard.general_stats')}", level=1)
        
        table = doc.add_table(rows=9, cols=2)
        table.style = 'Light Grid Accent 1'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = t('report.metric')
        hdr_cells[1].text = t('report.value')
        
        stats_data = [
            (t('dashboard.total_analyses'), str(stats.get('totalAnalyses', 0))),
            (t('dashboard.avg_fluor'), f"{stats.get('avgFluor', 0)}{t('units.percentage')}"),
            (t('dashboard.avg_pfas'), f"{stats.get('avgPfas', 0)}{t('units.percentage')}"),
            (t('dashboard.avg_concentration'), f"{stats.get('avgConcentration', 0)} {t('units.millimolar')}"),
            (t('dashboard.avg_quality'), f"{stats.get('avgQuality', 0)}{t('units.over_ten')}"),
            (t('dashboard.high_quality'), str(stats.get('highQualitySamples', 0))),
            (t('dashboard.last_week'), str(stats.get('lastWeek', 0))),
            (t('dashboard.avg_snr'), str(stats.get('avgSNR', 'N/A')))
        ]
        
        for idx, (metric, value) in enumerate(stats_data, 1):
            row_cells = table.rows[idx].cells
            row_cells[0].text = metric
            row_cells[1].text = value
        
        doc.add_page_break()
        
        # GRÁFICOS
        if chart_images:
            doc.add_heading(f"2. {t('dashboard.charts')}", level=1)
            
            if 'trend' in chart_images and chart_images['trend']:
                doc.add_heading(f"2.1 {t('dashboard.trend')}", level=2)
                doc.add_picture(io.BytesIO(chart_images['trend']), width=Inches(6))
                doc.add_paragraph()
            
            if 'distribution' in chart_images and chart_images['distribution']:
                doc.add_heading(f"2.2 {t('dashboard.distribution')}", level=2)
                doc.add_picture(io.BytesIO(chart_images['distribution']), width=Inches(6))
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output