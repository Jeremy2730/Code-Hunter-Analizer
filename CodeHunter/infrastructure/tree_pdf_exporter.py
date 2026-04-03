"""
CodeHunter - Tree PDF Exporter

🎯 Propósito:
Exportar la estructura del proyecto en formato árbol a PDF.

🧠 Qué hace:
- Recorre el proyecto usando walk_project (fuente única)
- Genera estructura tipo:
    📂 proyecto
     ├── archivo.py
     └── carpeta/
- Exporta usando reportlab

🔥 No depende de la UI
"""

import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from CodeHunter.utils.project_walker import walk_project


def build_tree_lines(project_path):
    lines = []
    root_name = os.path.basename(project_path)

    lines.append(f"📂 {root_name}/")

    def walk(dir_path, prefix=""):
        entries = []
        try:
            entries = sorted(os.listdir(dir_path))
        except Exception:
            return

        entries = [e for e in entries if not e.startswith(".")]

        for i, name in enumerate(entries):
            full_path = os.path.join(dir_path, name)
            is_last = (i == len(entries) - 1)

            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}{name}"
            lines.append(line)

            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                walk(full_path, prefix + extension)

    walk(project_path)
    return lines


def export_tree_to_pdf(project_path):
    project_name = os.path.basename(project_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    filename = os.path.join(
        downloads_path,
        f"CodeHunter_Tree_{project_name}_{timestamp}.pdf"
    )

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    elements = []

    # Título
    elements.append(Paragraph("CODE HUNTER", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Estructura del Proyecto", styles["Heading2"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Árbol
    lines = build_tree_lines(project_path)

    for line in lines:
        elements.append(Paragraph(f"<font name='Courier'>{line}</font>", normal))
        elements.append(Spacer(1, 0.12 * inch))

    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Italic"]
    ))

    doc.build(elements)
    return filename