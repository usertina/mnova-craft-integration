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


class ReportExporter:
    """Clase mejorada para exportar análisis RMN con gráficos"""
    
    # ========================================================================
    # EXPORTACIÓN JSON (sin cambios)
    # ========================================================================
    
    @staticmethod
    def export_json(results: Dict) -> BinaryIO:
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
    def export_pdf(results: Dict, chart_image: bytes = None) -> BinaryIO:
        """Exporta análisis individual como PDF con gráfico"""
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
        story.append(Paragraph("Reporte de Análisis RMN", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph("Detección y Cuantificación de PFAS", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>Muestra:</b> {results.get('filename', 'N/A')}", info_style))
        story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # ===== GRÁFICO DEL ESPECTRO =====
        if chart_image:
            story.append(Paragraph("1. Espectro RMN", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            img = Image(io.BytesIO(chart_image), width=6*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
        
        # ===== RESUMEN EJECUTIVO =====
        story.append(Paragraph("2. Resumen Ejecutivo", styles['Heading1']))
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
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        quality_text = f"<b>Score de Calidad:</b> {results.get('quality_score', 0):.1f}/10"
        story.append(Paragraph(quality_text, styles['Normal']))
        story.append(PageBreak())

        # ===== sección simple ===== 
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Información Rápida", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))

        quick_info_data = [
            ['Métrica', 'Valor'],
            ['Picos Detectados', str(len(results.get('peaks', [])))],
            ['Integral Total', f"{analysis.get('total_area', 0):,.2f}"],
            ['Relación S/N', f"{results.get('quality_metrics', {}).get('snr', 0):.2f}"]
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
        story.append(Paragraph("3. Análisis Detallado", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("3.1 Composición Química", styles['Heading2']))
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
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(comp_table)
        story.append(Spacer(1, 0.3*inch))

        # 🆕 3.2 Estadísticas Detalladas
        story.append(Paragraph("3.2 Estadísticas Detalladas", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))

        detailed_stats = results.get("detailed_analysis", {})

        if detailed_stats and not detailed_stats.get("error"):
            # Crear tabla de estadísticas detalladas
            stats_data = [['Parámetro', 'Valor', 'Unidades', 'Límites']]
            
            # Orden de parámetros a mostrar
            param_order = [
                'ppm_range',
                'intensity_range_corrected',
                'intensity_range_original',
                'max_signal_corr',
                'mean_intensity_corr',
                'std_intensity_corr',
                'signal_to_noise'
            ]
            
            for param_key in param_order:
                if param_key in detailed_stats:
                    stat = detailed_stats[param_key]
                    param_name = stat.get('parameter', param_key)
                    value = stat.get('value', '--')
                    unit = stat.get('unit', '')
                    limits = stat.get('limits', '—')
                    
                    # Convertir valor a string si no lo es
                    if not isinstance(value, str):
                        if isinstance(value, float):
                            value = f"{value:.2f}"
                        else:
                            value = str(value)
                    
                    stats_data.append([param_name, value, unit, limits])
            
            stats_table = Table(stats_data, colWidths=[2.2*inch, 1.5*inch, 1*inch, 1.1*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Alinear valores a la derecha
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(stats_table)
        else:
            story.append(Paragraph("No hay estadísticas detalladas disponibles.", styles['Normal']))

        story.append(PageBreak())


        
        # ===== PICOS DETECTADOS =====
        story.append(Paragraph("4. Picos Detectados", styles['Heading1']))
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
        
        doc.build(story)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_docx(results: Dict, chart_image: bytes = None) -> BinaryIO:
        """Exporta análisis individual como DOCX con gráfico"""
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
        
        # ===== GRÁFICO DEL ESPECTRO =====
        if chart_image:
            doc.add_heading('1. Espectro RMN', level=1)
            doc.add_picture(io.BytesIO(chart_image), width=Inches(6))
            doc.add_paragraph()
        
        # ===== RESUMEN EJECUTIVO =====
        doc.add_heading('2. Resumen Ejecutivo', level=1)
        
        analysis = results.get("analysis", {})
        
        summary_table = doc.add_table(rows=4, cols=3)
        summary_table.style = 'Light Grid Accent 1'
        
        hdr_cells = summary_table.rows[0].cells
        hdr_cells[0].text = 'Parámetro'
        hdr_cells[1].text = 'Valor'
        hdr_cells[2].text = 'Unidad'
        
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

        doc.add_paragraph()

        # 🆕 Información Rápida
        info_p = doc.add_paragraph()
        info_p.add_run('Información Rápida').bold = True
        info_p.style = 'Heading 2'

        quick_table = doc.add_table(rows=4, cols=2)
        quick_table.style = 'Light List Accent 1'

        quick_data = [
            ('Picos Detectados', str(len(results.get('peaks', [])))),
            ('Integral Total', f"{analysis.get('total_area', 0):,.2f}"),
            ('Relación S/N', f"{results.get('quality_metrics', {}).get('snr', 0):.2f}")
        ]

        hdr_cells = quick_table.rows[0].cells
        hdr_cells[0].text = 'Métrica'
        hdr_cells[1].text = 'Valor'

        for idx, (metric, value) in enumerate(quick_data, start=1):
            row_cells = quick_table.rows[idx].cells
            row_cells[0].text = metric
            row_cells[1].text = value

        doc.add_page_break()
        
        # ===== RESULTADOS DETALLADOS =====
        doc.add_heading('3. Análisis Detallado', level=1)
        doc.add_heading('3.1 Composición Química', level=2)
        
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

        # 🆕 3.2 Estadísticas Detalladas
        doc.add_heading('3.2 Estadísticas Detalladas', level=2)

        detailed_stats = results.get("detailed_analysis", {})

        if detailed_stats and not detailed_stats.get("error"):
            # Orden de parámetros
            param_order = [
                'ppm_range',
                'intensity_range_corrected',
                'intensity_range_original',
                'max_signal_corr',
                'mean_intensity_corr',
                'std_intensity_corr',
                'signal_to_noise'
            ]
            
            # Contar parámetros válidos
            valid_params = [p for p in param_order if p in detailed_stats]
            
            if valid_params:
                stats_table = doc.add_table(rows=len(valid_params)+1, cols=4)
                stats_table.style = 'Light Grid Accent 1'
                
                # Encabezados
                hdr = stats_table.rows[0].cells
                hdr[0].text = 'Parámetro'
                hdr[1].text = 'Valor'
                hdr[2].text = 'Unidades'
                hdr[3].text = 'Límites'
                
                # Datos
                for idx, param_key in enumerate(valid_params, start=1):
                    stat = detailed_stats[param_key]
                    row = stats_table.rows[idx].cells
                    
                    row[0].text = stat.get('parameter', param_key)
                    
                    # Formatear valor
                    value = stat.get('value', '--')
                    if not isinstance(value, str):
                        if isinstance(value, float):
                            value = f"{value:.2f}"
                        else:
                            value = str(value)
                    row[1].text = value
                    
                    row[2].text = stat.get('unit', '')
                    row[3].text = stat.get('limits', '—')
            else:
                doc.add_paragraph("No hay estadísticas detalladas disponibles.")
        else:
            doc.add_paragraph("No hay estadísticas detalladas disponibles.")

        doc.add_paragraph()

                
        # ===== PICOS DETECTADOS =====
        doc.add_heading('4. Picos Detectados', level=1)
        
        peaks = results.get("peaks", [])[:20]
        
        if peaks:
            peak_table = doc.add_table(rows=len(peaks)+1, cols=5)
            peak_table.style = 'Light Grid Accent 1'
            
            hdr = peak_table.rows[0].cells
            hdr[0].text = 'PPM'
            hdr[1].text = 'Intensidad'
            hdr[2].text = 'Int. Rel. (%)'
            hdr[3].text = 'Ancho (ppm)'
            hdr[4].text = 'Región'
            
            for idx, peak in enumerate(peaks, start=1):
                row = peak_table.rows[idx].cells
                row[0].text = f"{peak.get('ppm', 0):.3f}"
                row[1].text = f"{peak.get('intensity', 0):.1f}"
                row[2].text = f"{peak.get('relative_intensity', 0):.1f}"
                row[3].text = f"{peak.get('width_ppm', 0):.3f}"
                row[4].text = peak.get('region', '')[:30]
        else:
            doc.add_paragraph("No se detectaron picos significativos.")
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_csv(results: Dict) -> BinaryIO:
        """Exporta análisis individual como CSV"""
        import csv
        from io import StringIO
        
        text_buffer = StringIO()
        writer = csv.writer(text_buffer)
        
        writer.writerow(["REPORTE DE ANÁLISIS RMN - PFAS"])
        writer.writerow(["Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Archivo:", results.get("filename", "N/A")])
        writer.writerow([])
        
        writer.writerow(["COMPOSICIÓN QUÍMICA"])
        writer.writerow(["Parámetro", "Valor", "Unidad"])
        
        analysis = results.get("analysis", {})
        writer.writerow(["Flúor Total (% Área)", f"{analysis.get('fluor_percentage', 0):.2f}", "%"])
        writer.writerow(["PFAS (% Flúor)", f"{analysis.get('pifas_percentage', 0):.2f}", "%"])
        writer.writerow(["Concentración PFAS", f"{analysis.get('pifas_concentration', 0):.4f}", "mM"])
        writer.writerow(["Área Total Integrada", f"{analysis.get('total_area', 0):.2f}", "a.u."])
        writer.writerow([])
        
        writer.writerow(["CALIDAD"])
        writer.writerow(["Métrica", "Valor"])
        writer.writerow(["Score de Calidad", f"{results.get('quality_score', 0):.1f}/10"])
        
        quality = results.get("quality_metrics", {})
        writer.writerow(["SNR", f"{quality.get('snr', 0):.2f}"])
        writer.writerow(["Rango Dinámico", f"{quality.get('dynamic_range', 0):.2f}"])
        writer.writerow([])
        
        writer.writerow(["PICOS DETECTADOS"])
        writer.writerow(["PPM", "Intensidad", "Int. Relativa (%)", "Ancho (ppm)", "Región"])
        
        peaks = results.get("peaks", [])
        for peak in peaks[:20]:
            writer.writerow([
                f"{peak.get('ppm', 0):.3f}",
                f"{peak.get('intensity', 0):.1f}",
                f"{peak.get('relative_intensity', 0):.1f}",
                f"{peak.get('width_ppm', 0):.3f}",
                peak.get('region', '')
            ])
        
        byte_buffer = io.BytesIO()
        byte_buffer.write(text_buffer.getvalue().encode('utf-8'))
        byte_buffer.seek(0)
        text_buffer.close()
        
        return byte_buffer
    
    # ========================================================================
    # EXPORTACIÓN DE COMPARACIÓN
    # ========================================================================
    
    @staticmethod
    def export_comparison_pdf(samples: List[Dict], chart_image: bytes = None) -> BinaryIO:
        """Exporta comparación de muestras como PDF con gráfico"""
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
        story.append(Paragraph("Comparación de Muestras RMN", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph(f"Análisis Comparativo de {len(samples)} Muestras", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        
        # 🆕 LISTA DE MUESTRAS COMPARADAS
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("<b>Muestras incluidas:</b>", info_style))
        story.append(Spacer(1, 0.1*inch))
        
        for i, sample in enumerate(samples, 1):
            sample_text = f"{i}. {sample.get('filename', sample.get('name', 'N/A'))} - {sample.get('date', 'N/A')}"
            sample_para = Paragraph(sample_text, styles['Normal'])
            sample_para.alignment = TA_CENTER
            story.append(sample_para)
        
        story.append(PageBreak())
        
        # GRÁFICO DE COMPARACIÓN
        if chart_image:
            story.append(Paragraph("1. Gráfico Comparativo", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            img = Image(io.BytesIO(chart_image), width=6.5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())
        
        # TABLA COMPARATIVA
        story.append(Paragraph("2. Tabla Comparativa", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Crear tabla con nombres de archivo completos en header
        table_data = [['Parámetro'] + [s.get('filename', s.get('name', 'N/A'))[:20] + '...' if len(s.get('filename', s.get('name', 'N/A'))) > 20 else s.get('filename', s.get('name', 'N/A')) for s in samples]]
        
        # Añadir fila de fechas
        table_data.append(['Fecha'] + [s.get('date', '--') for s in samples])
        
        # Parámetros
        params = [
            ('Flúor (%)', 'fluor', lambda x: f"{x:.2f}"),
            ('PFAS (%)', 'pfas', lambda x: f"{x:.2f}"),
            ('Concentración (mM)', 'concentration', lambda x: f"{x:.4f}"),
            ('Calidad (/10)', 'quality', lambda x: f"{x:.1f}")
        ]
        
        for param_name, param_key, formatter in params:
            row = [param_name]
            for sample in samples:
                value = sample.get(param_key, 0)
                row.append(formatter(value) if value else '--')
            table_data.append(row)
        
        # Calcular anchos de columna dinámicamente
        num_samples = len(samples)
        param_col_width = 1.5*inch
        remaining_width = 6.5*inch - param_col_width
        sample_col_width = remaining_width / max(num_samples, 1)
        
        col_widths = [param_col_width] + [sample_col_width] * num_samples
        
        comp_table = Table(table_data, colWidths=col_widths)
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ecf0f1')),  # Fila de fechas
            ('BACKGROUND', (0, 2), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(comp_table)
        
        doc.build(story)
        output.seek(0)
        
        return output

    @staticmethod
    def export_comparison_docx(samples: List[Dict], chart_image: bytes = None) -> BinaryIO:
        """Exporta comparación de muestras como DOCX con gráfico"""
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # PORTADA
        title = doc.add_heading('Comparación de Muestras RMN', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading(f'Análisis Comparativo de {len(samples)} Muestras', level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        date_p = doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 🆕 LISTA DE MUESTRAS
        doc.add_paragraph()
        samples_title = doc.add_paragraph()
        samples_title.add_run('Muestras incluidas:').bold = True
        samples_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        for i, sample in enumerate(samples, 1):
            sample_p = doc.add_paragraph(
                f"{i}. {sample.get('filename', sample.get('name', 'N/A'))} - {sample.get('date', 'N/A')}"
            )
            sample_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # GRÁFICO
        if chart_image:
            doc.add_heading('1. Gráfico Comparativo', level=1)
            doc.add_picture(io.BytesIO(chart_image), width=Inches(6.5))
            doc.add_paragraph()
            doc.add_page_break()
        
        # TABLA COMPARATIVA
        doc.add_heading('2. Tabla Comparativa', level=1)
        
        num_samples = len(samples)
        table = doc.add_table(rows=6, cols=num_samples+1)
        table.style = 'Light Grid Accent 1'
        
        # Encabezados con nombres completos
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Parámetro'
        for idx, sample in enumerate(samples, 1):
            hdr_cells[idx].text = sample.get('filename', sample.get('name', 'N/A'))[:25]  # Truncar si es muy largo
            # Ajustar tamaño de fuente si hay muchas muestras
            if num_samples > 3:
                for paragraph in hdr_cells[idx].paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        
        # Fila de fechas
        date_row = table.rows[1].cells
        date_row[0].text = 'Fecha'
        for idx, sample in enumerate(samples, 1):
            date_row[idx].text = sample.get('date', '--')
        
        # Datos
        params = [
            ('Flúor (%)', 'fluor'),
            ('PFAS (%)', 'pfas'),
            ('Concentración (mM)', 'concentration'),
            ('Calidad (/10)', 'quality')
        ]
        
        for row_idx, (param_name, param_key) in enumerate(params, 2):
            row_cells = table.rows[row_idx].cells
            row_cells[0].text = param_name
            for col_idx, sample in enumerate(samples, 1):
                value = sample.get(param_key, 0)
                if param_key == 'concentration':
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
    def export_comparison_csv(samples: List[Dict]) -> BinaryIO:
        """Exporta comparación de muestras como CSV"""
        import csv
        from io import StringIO
        
        text_buffer = StringIO()
        writer = csv.writer(text_buffer)
        
        writer.writerow(["COMPARACIÓN DE MUESTRAS RMN - PFAS"])
        writer.writerow(["Generado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Total de muestras:", len(samples)])
        writer.writerow([])
        
        # Encabezados
        headers = ['Parámetro'] + [s.get('filename', s.get('name', 'N/A')) for s in samples]
        writer.writerow(headers)
        
        # Datos
        params = [
            ('Flúor (%)', 'fluor'),
            ('PFAS (%)', 'pfas'),
            ('Concentración (mM)', 'concentration'),
            ('Calidad (/10)', 'quality')
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
    def export_dashboard_pdf(stats: Dict, chart_images: Dict[str, bytes] = None) -> BinaryIO:
        """Exporta estadísticas del dashboard como PDF con gráficos"""
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
        story.append(Paragraph("Dashboard de Estadísticas", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)
        story.append(Paragraph("Análisis Agregado de Muestras RMN", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        info_style = ParagraphStyle('Info', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", info_style))
        story.append(PageBreak())
        
        # ESTADÍSTICAS GENERALES
        story.append(Paragraph("1. Estadísticas Generales", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        stats_data = [
            ['Métrica', 'Valor'],
            ['Total de Análisis', str(stats.get('totalAnalyses', 0))],
            ['Flúor Promedio', f"{stats.get('avgFluor', 0)}%"],
            ['PFAS Promedio', f"{stats.get('avgPfas', 0)}%"],
            ['Concentración Promedio', f"{stats.get('avgConcentration', 0)} mM"],
            ['Calidad Promedio', f"{stats.get('avgQuality', 0)}/10"],
            ['Muestras Alta Calidad (≥8)', str(stats.get('highQualitySamples', 0))],
            ['Análisis (Última Semana)', str(stats.get('lastWeek', 0))],
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
            story.append(Paragraph("2. Gráficos Estadísticos", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            
            if 'trend' in chart_images and chart_images['trend']:
                story.append(Paragraph("2.1 Tendencia de Concentración", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                img = Image(io.BytesIO(chart_images['trend']), width=6*inch, height=3.5*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            
            if 'distribution' in chart_images and chart_images['distribution']:
                story.append(Paragraph("2.2 Distribución de Calidad", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                img = Image(io.BytesIO(chart_images['distribution']), width=6*inch, height=3.5*inch)
                story.append(img)
        
        doc.build(story)
        output.seek(0)
        
        return output

    @staticmethod
    def export_dashboard_docx(stats: Dict, chart_images: Dict[str, bytes] = None) -> BinaryIO:
        """Exporta estadísticas del dashboard como DOCX con gráficos"""
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11)
        
        # PORTADA
        title = doc.add_heading('Dashboard de Estadísticas', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_heading('Análisis Agregado de Muestras RMN', level=2)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        date_p = doc.add_paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_page_break()
        
        # ESTADÍSTICAS GENERALES
        doc.add_heading('1. Estadísticas Generales', level=1)
        
        table = doc.add_table(rows=9, cols=2)
        table.style = 'Light Grid Accent 1'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Métrica'
        hdr_cells[1].text = 'Valor'
        
        stats_data = [
            ('Total de Análisis', str(stats.get('totalAnalyses', 0))),
            ('Flúor Promedio', f"{stats.get('avgFluor', 0)}%"),
            ('PFAS Promedio', f"{stats.get('avgPfas', 0)}%"),
            ('Concentración Promedio', f"{stats.get('avgConcentration', 0)} mM"),
            ('Calidad Promedio', f"{stats.get('avgQuality', 0)}/10"),
            ('Muestras Alta Calidad (≥8)', str(stats.get('highQualitySamples', 0))),
            ('Análisis (Última Semana)', str(stats.get('lastWeek', 0))),
            ('SNR Promedio', str(stats.get('avgSNR', 'N/A')))
        ]
        
        for idx, (metric, value) in enumerate(stats_data, 1):
            row_cells = table.rows[idx].cells
            row_cells[0].text = metric
            row_cells[1].text = value
        
        doc.add_page_break()
        
        # GRÁFICOS
        if chart_images:
            doc.add_heading('2. Gráficos Estadísticos', level=1)
            
            if 'trend' in chart_images and chart_images['trend']:
                doc.add_heading('2.1 Tendencia de Concentración', level=2)
                doc.add_picture(io.BytesIO(chart_images['trend']), width=Inches(6))
                doc.add_paragraph()
            
            if 'distribution' in chart_images and chart_images['distribution']:
                doc.add_heading('2.2 Distribución de Calidad', level=2)
                doc.add_picture(io.BytesIO(chart_images['distribution']), width=Inches(6))
        
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        
        return output   