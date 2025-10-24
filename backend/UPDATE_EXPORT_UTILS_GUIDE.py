#!/usr/bin/env python3
"""
Script para actualizar export_utils.py con soporte de múltiples idiomas
Ejecuta este script para aplicar los cambios automáticamente
"""

CHANGES = """
===========================================
CAMBIOS NECESARIOS EN export_utils.py
===========================================

1. IMPORTAR TranslationManager (línea ~27):
   
   from translation_manager import TranslationManager


2. MODIFICAR FIRMAS DE MÉTODOS (agregar parámetro lang='es'):

   @staticmethod
   def export_json(results: Dict, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_pdf(results: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_docx(results: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_csv(results: Dict, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_comparison_pdf(samples: List[Dict], chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_comparison_docx(samples: List[Dict], chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_comparison_csv(samples: List[Dict], lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_dashboard_pdf(stats: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:
   
   @staticmethod
   def export_dashboard_docx(stats: Dict, chart_images: Dict[str, bytes] = None, lang: str = 'es') -> BinaryIO:


3. AL INICIO DE CADA MÉTODO, CREAR INSTANCIA DE TRADUCTOR:

   def export_pdf(results: Dict, chart_image: bytes = None, lang: str = 'es') -> BinaryIO:
       # 🆕 Crear traductor
       t = TranslationManager(lang)
       
       output = io.BytesIO()
       # ... resto del código


4. REEMPLAZAR TEXTOS HARDCODEADOS POR TRADUCCIONES:

   ANTES:
       story.append(Paragraph("Reporte de Análisis RMN", title_style))
       story.append(Paragraph("Detección y Cuantificación de PFAS", subtitle_style))
   
   DESPUÉS:
       story.append(Paragraph(t('report.title'), title_style))
       story.append(Paragraph(t('report.subtitle'), subtitle_style))


5. EJEMPLOS DE REEMPLAZOS COMUNES:

   "Muestra:" → t('report.sample')
   "Fecha:" → t('report.date')
   "Espectro RMN" → t('report.spectrum')
   "Resumen Ejecutivo" → t('report.executive_summary')
   "Parámetro" → t('report.parameter')
   "Valor" → t('report.value')
   "Unidad" → t('report.unit')
   "Score de Calidad" → t('report.quality_score')
   "Análisis Detallado" → t('report.detailed_analysis')
   "Picos Detectados" → t('peaks.title')
   
   "Flúor Total" → t('results.fluor')
   "PFAS" → t('results.pfas')
   "Concentración PFAS" → t('results.concentration')
   "Calidad" → t('results.quality')
   
   "%" → t('units.percentage')
   "% del Flúor" → t('units.percent_fluor')
   "mM" → t('units.millimolar')
   "a.u." → t('units.arbitrary')
   "/10" → t('units.over_ten')


6. PARA TEXTOS CON PARÁMETROS:

   ANTES:
       f"Análisis Comparativo de {len(samples)} Muestras"
   
   DESPUÉS:
       t('comparison.subtitle', {'count': len(samples)})


7. EN LAS TABLAS:

   ANTES:
       summary_data = [
           ['Parámetro', 'Valor', 'Unidad'],
           ['Flúor Total', f"{...:.2f}", '%'],
           ['PFAS', f"{...:.2f}", '% del Flúor'],
       ]
   
   DESPUÉS:
       summary_data = [
           [t('report.parameter'), t('report.value'), t('report.unit')],
           [t('results.fluor'), f"{...:.2f}", t('units.percentage')],
           [t('results.pfas'), f"{...:.2f}", t('units.percent_fluor')],
       ]


===========================================
LISTA COMPLETA DE CLAVES DE TRADUCCIÓN
===========================================

report.title
report.subtitle
report.sample
report.date
report.spectrum
report.executive_summary
report.parameter
report.value
report.unit
report.quality_score
report.detailed_analysis
report.chemical_composition
report.detailed_statistics
report.limits
report.detected_peaks
report.quick_info
report.metric

results.fluor
results.pfas
results.concentration
results.quality
results.total_area
results.fluor_area
results.pfas_area
results.sample_concentration

peaks.title
peaks.ppm
peaks.intensity
peaks.relative_intensity
peaks.width
peaks.region
peaks.none

comparison.title
comparison.subtitle (usa {count})
comparison.samples_included
comparison.chart
comparison.table

dashboard.title
dashboard.subtitle
dashboard.general_stats
dashboard.charts
dashboard.trend
dashboard.distribution
dashboard.total_analyses
dashboard.avg_fluor
dashboard.avg_pfas
dashboard.avg_concentration
dashboard.avg_quality
dashboard.high_quality
dashboard.last_week
dashboard.avg_snr

units.percentage
units.percent_fluor
units.millimolar
units.arbitrary
units.over_ten

===========================================
NOTA: Aplica estos cambios a TODOS los métodos:
- export_pdf
- export_docx
- export_csv
- export_comparison_pdf
- export_comparison_docx
- export_comparison_csv
- export_dashboard_pdf
- export_dashboard_docx
===========================================
"""

print(CHANGES)
print("\n✅ Guarda este archivo como referencia para modificar export_utils.py")
print("📝 Cada texto hardcodeado debe reemplazarse por t('clave.traduccion')")