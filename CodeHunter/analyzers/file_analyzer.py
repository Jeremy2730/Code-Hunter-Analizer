"""
CodeHunter - File Analyzer
Detecta archivos Python vacíos y carpetas realmente vacías.
"""

import os
from .function_analyzer import Finding
from ..utils.project_walker import walk_project, IGNORE_DIRS


def detect_empty_python_files(project_path):
    """Detecta archivos .py sin código útil (vacíos o solo con imports)."""
    findings = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            if file == "__init__.py":
                continue

            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
            except Exception:
                continue

            lines = [
                line for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

            only_imports = bool(lines) and all(
                line.startswith("import") or line.startswith("from")
                for line in lines
            )

            if not lines or only_imports:
                findings.append(Finding(
                    level="WARNING",
                    message="Archivo Python vacío o sin código útil",
                    file=path,
                    line=1,
                    suggestion="Eliminar el archivo o implementar su lógica.",
                ))

    return findings


def detect_empty_folders(project_path):
    """
    Detecta carpetas completamente vacías (sin archivos ni subcarpetas),
    respetando las exclusiones de project_walker.
    """
    findings = []

    for root, dirs, files in os.walk(project_path):
        # Aplicar las mismas exclusiones que walk_project
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS and not d.endswith(".egg-info")
        ]

        # Solo reportar si no hay archivos Y no quedan subcarpetas tras filtrar
        if not files and not dirs:
            findings.append(Finding(
                level="WARNING",
                message="Carpeta vacía detectada",
                file=root,
                line=0,
                suggestion="Eliminar la carpeta si no se utiliza.",
            ))

    return findings
