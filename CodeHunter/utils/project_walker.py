"""
CodeHunter - Project Walker
Utilidad centralizada para recorrer archivos Python del proyecto,
excluyendo entornos virtuales, cachés y carpetas de build.
"""

import os
from pathlib import Path

# Nombre exportado como IGNORE_DIRS (usado por file_analyzer, project_scanner, etc.)
IGNORE_DIRS = {
    # Entornos virtuales (todas las variantes comunes)
    "venv", ".venv", "env", ".env",
    "virtualenv", ".virtualenv",
    # Control de versiones
    ".git", ".hg", ".svn",
    # Caché Python
    "__pycache__", ".mypy_cache", ".ruff_cache",
    ".pytest_cache", ".hypothesis",
    # Build / distribución
    "build", "dist", ".eggs", "site-packages",
    # Otros
    "node_modules", ".tox",
    "cache", "memory", "recall",
}

# Alias para compatibilidad con código que use el nombre anterior
IGNORED_DIRS = IGNORE_DIRS


def walk_project(project_path):
    """
    Generador que recorre el proyecto haciendo yield de (root, files),
    sin entrar en entornos virtuales, cachés ni carpetas de build.
    """
    for root, dirs, files in os.walk(project_path):

        # Saltar si alguna parte de la ruta ya es una carpeta ignorada
        if any(part in IGNORE_DIRS for part in Path(root).parts):
            continue

        # Filtrar subcarpetas para que os.walk no descienda en ellas
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS and not d.endswith(".egg-info")
        ]

        yield root, files


def walk_python_files(project_path: str):
    """
    Generador que hace yield de la ruta absoluta de cada .py en el proyecto.
    """
    for root, files in walk_project(project_path):
        for fname in files:
            if fname.endswith(".py"):
                yield os.path.join(root, fname)
