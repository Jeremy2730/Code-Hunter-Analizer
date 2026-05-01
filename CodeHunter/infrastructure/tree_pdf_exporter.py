"""
Tree PDF Exporter - Exportador de estructura del proyecto

Responsabilidad:
- Generar representación visual del árbol de archivos
- Exportarlo como documento PDF

Qué hace:
- Recorre el proyecto recursivamente
- Genera estructura tipo consola (├── └──)
- Mantiene formato legible en PDF

Características:
- No depende de la UI
- Compatible con cualquier proyecto
- Usa fuente monoespaciada para alineación

Entrada:
- project_path

Salida:
- PDF con estructura del proyecto
"""

import os
from datetime import datetime
from tkinter import filedialog
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from CodeHunter.utils.project_walker import IGNORE_DIRS


def build_tree_lines(project_path):
    lines = []
    root_name = os.path.basename(project_path)

    lines.append((f"{root_name}/", 0, True))

    def walk(dir_path, prefix="", level=1):
        try:
            entries = sorted(
                os.scandir(dir_path),
                key=lambda e: (not e.is_dir(), e.name.lower())
            )
        except Exception:
            return

        entries = [
            e for e in entries
            if e.name not in IGNORE_DIRS and not e.name.startswith(".")
        ]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)

            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            line = f"{prefix}{connector}{entry.name}"

            lines.append((line, level, entry.is_dir()))

            if entry.is_dir():
                walk(entry.path, prefix + extension, level + 1)

    walk(project_path)
    return lines


def export_tree_to_pdf(project_path):
    # 🔥 MISMO COMPORTAMIENTO QUE DASHBOARD
    save_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile="codehunter_tree.pdf",
        title="Guardar árbol del proyecto"
    )

    level_colors = [
        "#58A6FF",  # nivel 0 (raíz)
        "#7EE787",  # nivel 1
        "#F2CC60",  # nivel 2
        "#FF7B72",  # nivel 3
        "#D2A8FF",  # nivel 4+
    ]


    if not save_path:
        return None

    doc = SimpleDocTemplate(save_path)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    elements = []

    # ───── HEADER
    elements.append(Paragraph("CODE HUNTER", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Estructura del Proyecto", styles["Heading2"]))
    elements.append(Spacer(1, 0.3 * inch))

    # ───── TREE
    lines = build_tree_lines(project_path)

    for line, level, is_dir in lines:

        if is_dir:
            color = level_colors[min(level, len(level_colors)-1)]
        else:
            color = "#C9D1D9"  # archivos (gris elegante)

        elements.append(
            Paragraph(
                f"<font name='Courier' color='{color}'>{line}</font>",
                normal
            )
        )
        elements.append(Spacer(1, 0.12 * inch))

    # ───── FOOTER
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Italic"]
    ))

    doc.build(elements)

    return save_path