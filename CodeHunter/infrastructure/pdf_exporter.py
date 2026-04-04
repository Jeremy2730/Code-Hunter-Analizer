"""
PDF Exporter - Generador de reportes de diagnóstico

Responsabilidad:
- Convertir resultados del análisis en un informe PDF profesional
- Mostrar métricas generales (score, errores, advertencias)
- Listar hallazgos agrupados por archivo

Qué hace:
- Agrupa findings por archivo
- Muestra nivel, línea, mensaje y sugerencia
- Genera documento listo para compartir

Características:
- Soporte para modelos legacy y AdvancedFinding
- Manejo seguro de atributos (no rompe si faltan datos)
- Exportación automática a carpeta Downloads

Entrada:
- project_path
- profile_description
- analysis_data (dict con findings y métricas)

Salida:
- Archivo PDF generado
"""


import os
from datetime import datetime
from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def export_report_to_pdf(project_path, profile_description, analysis_data):
    project_name = os.path.basename(project_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(downloads_path):
        downloads_path = os.path.expanduser("~")

    filename = os.path.join(
        downloads_path,
        f"CodeHunter_Report_{project_name}_{timestamp}.pdf"
    )

    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()

    # ───── TÍTULO
    elements.append(Paragraph("CODE HUNTER", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Informe Profesional de Diagnóstico", styles["Heading2"]))
    elements.append(Spacer(1, 0.4 * inch))

    # ───── PERFIL
    elements.append(Paragraph("1. Perfil del Sistema Analizado", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    for line in profile_description.split("\n"):
        if line.strip():
            elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 0.15 * inch))

    elements.append(Spacer(1, 0.4 * inch))

    # ───── RESULTADOS
    elements.append(Paragraph("2. Resultado del Análisis", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(f"Índice de Salud: {analysis_data.get('score', 0)}/100", styles["Normal"]))
    elements.append(Paragraph(f"Problemas críticos: {analysis_data.get('critical', 0)}", styles["Normal"]))
    elements.append(Paragraph(f"Advertencias: {analysis_data.get('warnings', 0)}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # ───── DETALLE
    elements.append(Paragraph("3. Detalle de Hallazgos", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    findings = analysis_data.get("findings", [])

    grouped = defaultdict(list)
    for f in findings:
        file_path = getattr(f, "file", "unknown_file")
        grouped[file_path].append(f)

    for file_path in sorted(grouped.keys()):
        elements.append(Paragraph(f"📁 {file_path}", styles["Heading3"]))
        elements.append(Spacer(1, 0.15 * inch))

        for f in grouped[file_path]:
            level = getattr(f, "level", "info")
            message = getattr(f, "message", "Sin mensaje")
            line = getattr(f, "line", "?")
            suggestion = getattr(f, "suggestion", "Sin sugerencia")

            elements.append(Paragraph(f"[{level.upper()}] {message}", styles["Normal"]))
            elements.append(Paragraph(f"Línea: {line}", styles["Normal"]))
            elements.append(Paragraph(f"Sugerencia: {suggestion}", styles["Normal"]))
            elements.append(Spacer(1, 0.25 * inch))

        elements.append(Spacer(1, 0.3 * inch))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        f"Generado por CodeHunter — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Italic"]
    ))

    doc.build(elements)
    return filename