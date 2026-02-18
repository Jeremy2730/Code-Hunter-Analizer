import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def export_report_to_pdf(project_path, profile_description, analysis_data):
    project_name = os.path.basename(project_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    filename = os.path.join(
        downloads_path,
        f"CodeHunter_Report_{project_name}_{timestamp}.pdf"
    )

    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    # TÍTULO
    elements.append(Paragraph("CODE HUNTER", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Informe Profesional de Diagnóstico", heading_style))
    elements.append(Spacer(1, 0.4 * inch))

    # PERFIL
    elements.append(Paragraph("1. Perfil del Sistema Analizado", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    for line in profile_description.split("\n"):
        if line.strip():
            elements.append(Paragraph(line, normal_style))
            elements.append(Spacer(1, 0.15 * inch))

    elements.append(Spacer(1, 0.4 * inch))

    # RESULTADOS
    elements.append(Paragraph("2. Resultado del Análisis", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    critical = analysis_data.get("critical", 0)
    warnings = analysis_data.get("warnings", 0)
    score = analysis_data.get("score", 0)

    elements.append(Paragraph(f"Índice de Salud: {score}/100", normal_style))
    elements.append(Paragraph(f"Problemas críticos: {critical}", normal_style))
    elements.append(Paragraph(f"Advertencias: {warnings}", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # DETALLE
    elements.append(Paragraph("3. Detalle de Hallazgos", heading_style))
    elements.append(Spacer(1, 0.2 * inch))

    findings = analysis_data.get("findings", [])

    if not findings:
        elements.append(Paragraph("No se detectaron problemas relevantes.", normal_style))
    else:
        for f in findings:
            level = f.level.value if hasattr(f.level, "value") else f.level
            elements.append(Paragraph(f"[{level}] {f.message}", normal_style))
            elements.append(Paragraph(f"Archivo: {f.file}", normal_style))
            elements.append(Paragraph(f"Línea: {f.line}", normal_style))
            elements.append(Paragraph(f"Sugerencia: {f.suggestion}", normal_style))
            elements.append(Spacer(1, 0.3 * inch))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        f"Documento generado por CodeHunter — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Italic"]
    ))

    doc.build(elements)
    return filename