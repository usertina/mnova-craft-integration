"""
Utilidades de Exportación - CraftRMN Pro
Genera reportes en múltiples formatos: PDF, DOCX, CSV, JSON
"""

import io
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, BinaryIO

import plotly.graph_objects as go
from plotly.io import write_image

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportExporter:
    """Clase para exportar análisis RMN en múltiples formatos"""
    
    @staticmethod
    def export_json(results: Dict) -> BinaryIO:
        """Exporta resultados como JSON"""
        output = io.BytesIO()
        json_str = json.dumps(results, indent=2, ensure_ascii=False)
        output.write(json_str.encode('utf-8'))
        output.seek(0)
        return output
    
    @staticmethod
    def export_csv(results: Dict) -> BinaryIO:
        """Exporta resultados como CSV completo"""
        import csv
        from io import StringIO
        
        text_buffer = StringIO()
        writer = csv.writer(text_buffer)
        
        # Encabezados
        writer.writerow(["REPORTE DE ANÁLISIS RMN - PFAS"])
        writer.writerow(["Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Archivo:", results.get("filename", "N/A")])
        writer.writerow([])
        
        # Composición Química
        writer.writerow(["COMPOSICIÓN QUÍMICA"])
        writer.writerow(["Parámetro", "Valor", "Unidad"])
        
        analysis = results.get("analysis", {})
        writer.writerow(["Flúor Total (% Área)", f"{analysis.get('fluor_percentage', 0):.2f}", "%"])
        writer.writerow(["PFAS (% Flúor)", f"{analysis.get('pifas_percentage', 0):.2f}", "%"])
        writer.writerow(["Concentración PFAS", f"{analysis.get('pifas_concentration', 0):.4f}", "mM"])
        writer.writerow(["Área Total Integrada", f"{analysis.get('total_area', 0):.2f}", "a.u."])
        writer.writerow([])
        
        # Calidad
        writer.writerow(["MÉTRICAS DE CALIDAD"])
        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Score de Calidad", f"{results.get('quality_score', 0):.1f}/10"])
        
        quality = results.get("quality_metrics", {})
        writer.writerow(["SNR", f"{quality.get('snr', 0):.2f}"])
        writer.writerow(["Rango Dinámico", f"{quality.get('dynamic_range', 0):.2f}"])
        writer.writerow(["Estabilidad Baseline", f"{quality.get('baseline_stability_std', 0):.3f}"])
        writer.writerow([])
        
        # Picos Detectados
        peaks = results.get("peaks", [])
        writer.writerow(["PICOS DETECTADOS"])
        writer.writerow(["PPM", "Intensidad", "Int. Relativa (%)", "Ancho (ppm)", "Región"])
        
        for peak in peaks[:20]:  # Top 20
            writer.writerow([
                f"{peak.get('ppm', 0):.3f}",
                f"{peak.get('intensity', 0):.1f}",
                f"{peak.get('relative_intensity', 0):.1f}",
                f"{peak.get('width_ppm', 0):.3f}",
                peak.get('region', '')
            ])
        
        # Convertir a bytes
        byte_buffer = io.BytesIO()
        byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        text_buffer.close()
        
        return byte_buffer
    
    @staticmethod
    def export_docx(results: Dict) -> BinaryIO:
        """Exporta reporte completo en formato DOCX"""
        doc = Document()
        
        # Configurar estilos
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # ===== PORTADA =====
        title = doc.add_heading('Reporte de Análisis RMN', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading('Detección y Cuantificación de PFAS', level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        info_p = doc.add_paragraph()
        info_p.add_run(f"Muestra: {results.get('filename', 'N/A')}").bold = True
        info_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        date_p = doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # ===== RESUMEN EJECUTIVO =====
        doc.add_heading('1. Resumen Ejecutivo', level=1)
        
        analysis = results.get("analysis", {})
        
        summary_table = doc.add_table(rows=4, cols=3)
        summary_table.style = 'Light Grid Accent 1'
        
        # Encabezados
        hdr_cells = summary_table.rows[0].cells
        hdr_cells[0].text = 'Parámetro'
        hdr_cells[1].text = 'Valor'
        hdr_cells[2].text = 'Unidad'
        
        # Datos clave
        row1 = summary_table.rows[1].cells
        row1[0].text = 'Flúor Total'
        row1[1].text = f"{analysis.get('fluor_percentage', 0):.2f}"
        row1[2].text = '%'
        
        row2 = summary_table.rows[2].cells
        row2[0].text = 'PFAS'
        row2[1].text = f"{analysis.get('pifas_percentage', 0):.2f}"
        row2[2].text = '% del Flúor'
        
        row3 = summary_table.rows[3].cells
        row3[0].text = 'Concentración PFAS'
        row3[1].text = f"{analysis.get('pifas_concentration', 0):.4f}"
        row3[2].text = 'mM'
        
        doc.add_paragraph()
        
        quality_p = doc.add_paragraph()
        quality_p.add_run('Score de Calidad: ').bold = True
        quality_p.add_run(f"{results.get('quality_score', 0):.1f}/10")
        
        doc.add_page_break()
        
        # ===== RESULTADOS DETALLADOS =====
        doc.add_heading('2. Análisis Detallado', level=1)
        
        doc.add_heading('2.1 Composición Química', level=2)
        
        comp_table = doc.add_table(rows=5, cols=2)
        comp_table.style = 'Light Shading Accent 1'
        
        comp_data = [
            ('Área Total Integrada', f"{analysis.get('total_area', 0):,.2f} a.u."),
            ('Área Flúor', f"{analysis.get('fluor_area', 0):,.2f} a.u."),
            ('Área PFAS', f"{analysis.get('pifas_area', 0):,.2f} a.u."),
            ('Concentración Muestra', f"{analysis.get('concentration', 0):.2f} mM")
        ]
        
        for idx, (param, val) in enumerate(comp_data):
            comp_table.rows[idx].cells[0].text = param
            comp_table.rows[idx].cells[1].text = val
        
        doc.add_paragraph()
        
        # ===== MÉTRICAS DE CALIDAD =====
        doc.add_heading('2.2 Métricas de Calidad', level=2)
        
        quality = results.get("quality_metrics", {})
        
        qual_table = doc.add_table(rows=6, cols=2)
        qual_table.style = 'Light Shading Accent 1'
        
        qual_data = [
            ('Score de Calidad', f"{results.get('quality_score', 0):.1f}/10"),
            ('SNR', f"{quality.get('snr', 0):.2f}"),
            ('Rango Dinámico', f"{quality.get('dynamic_range', 0):.2f}"),
            ('Estabilidad Baseline', f"{quality.get('baseline_stability_std', 0):.3f}"),
            ('Puntos de Datos', f"{quality.get('total_points', 0):,}")
        ]
        
        for idx, (param, val) in enumerate(qual_data):
            qual_table.rows[idx].cells[0].text = param
            qual_table.rows[idx].cells[1].text = val
        
        doc.add_page_break()
        
        # ===== PICOS DETECTADOS =====
        doc.add_heading('3. Picos Detectados', level=1)
        
        peaks = results.get("peaks", [])[:20]  # Top 20
        
        if peaks:
            peak_table = doc.add_table(rows=len(peaks)+1, cols=5)
            peak_table.style = 'Light Grid Accent 1'
            
            # Encabezados
            hdr = peak_table.rows[0].cells
            hdr[0].text = 'PPM'
            hdr[1].text = 'Intensidad'
            hdr[2].text = 'Int. Rel. (%)'
            hdr[3].text = 'Ancho (ppm)'
            hdr[4].text = 'Región'
            
            # Datos
            for idx, peak in enumerate(peaks, start=1):
                row = peak_table.rows[idx].cells
                row[0].text = f"{peak.get('ppm', 0):.3f}"
                row[1].text = f"{peak.get('intensity', 0):.1f}"
                row[2].text = f"{peak.get('relative_intensity', 0):.1f}"
                row[3].text = f"{peak.get('width_ppm', 0):.3f}"
                row[4].text = peak.get('region', '')[:30]  # Truncar si es muy largo
        else:
            doc.add_paragraph("No se detectaron picos significativos.")
        
        # Guardar en BytesIO
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_pdf(results: Dict) -> BinaryIO:
        """Exporta reporte completo en formato PDF"""
        output = io.BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(output, pagesize=A4,
                               topMargin=0.75*inch, bottomMargin=0.75*inch,
                               leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # ===== PORTADA =====
        story.append(Paragraph("Reporte de Análisis RMN", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph("Detección y Cuantificación de PFAS", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>Muestra:</b> {results.get('filename', 'N/A')}", info_style))
        story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # ===== RESUMEN EJECUTIVO =====
        story.append(Paragraph("1. Resumen Ejecutivo", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        analysis = results.get("analysis", {})
        
        summary_data = [
            ['Parámetro', 'Valor', 'Unidad'],
            ['Flúor Total', f"{analysis.get('fluor_percentage', 0):.2f}", '%'],
            ['PFAS', f"{analysis.get('pifas_percentage', 0):.2f}", '% del Flúor'],
            ['Concentración PFAS', f"{analysis.get('pifas_concentration', 0):.4f}", 'mM'],
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
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        quality_text = f"<b>Score de Calidad:</b> {results.get('quality_score', 0):.1f}/10"
        story.append(Paragraph(quality_text, styles['Normal']))
        story.append(PageBreak())
        
        # ===== ANÁLISIS DETALLADO =====
        story.append(Paragraph("2. Análisis Detallado", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("2.1 Composición Química", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        comp_data = [
            ['Parámetro', 'Valor'],
            ['Área Total Integrada', f"{analysis.get('total_area', 0):,.2f} a.u."],
            ['Área Flúor', f"{analysis.get('fluor_area', 0):,.2f} a.u."],
            ['Área PFAS', f"{analysis.get('pifas_area', 0):,.2f} a.u."],
            ['Concentración Muestra', f"{analysis.get('concentration', 0):.2f} mM"],
        ]
        
        comp_table = Table(comp_data, colWidths=[3.5*inch, 2*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(comp_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ===== MÉTRICAS DE CALIDAD =====
        story.append(Paragraph("2.2 Métricas de Calidad", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        quality = results.get("quality_metrics", {})
        
        qual_data = [
            ['Métrica', 'Valor'],
            ['Score de Calidad', f"{results.get('quality_score', 0):.1f}/10"],
            ['SNR', f"{quality.get('snr', 0):.2f}"],
            ['Rango Dinámico', f"{quality.get('dynamic_range', 0):.2f}"],
            ['Estabilidad Baseline', f"{quality.get('baseline_stability_std', 0):.3f}"],
            ['Puntos de Datos', f"{quality.get('total_points', 0):,}"],
        ]
        
        qual_table = Table(qual_data, colWidths=[3.5*inch, 2*inch])
        qual_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(qual_table)
        story.append(PageBreak())
        
        # ===== PICOS DETECTADOS =====
        story.append(Paragraph("3. Picos Detectados", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        peaks = results.get("peaks", [])[:20]
        
        if peaks:
            peak_data = [['PPM', 'Intensidad', 'Int. Rel.(%)', 'Ancho(ppm)']]
            
            for peak in peaks:
                peak_data.append([
                    f"{peak.get('ppm', 0):.3f}",
                    f"{peak.get('intensity', 0):.1f}",
                    f"{peak.get('relative_intensity', 0):.1f}",
                    f"{peak.get('width_ppm', 0):.3f}"
                ])
            
            peak_table = Table(peak_data, colWidths=[1.3*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            peak_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(peak_table)
        else:
            story.append(Paragraph("No se detectaron picos significativos.", styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        output.seek(0)
        
        return output