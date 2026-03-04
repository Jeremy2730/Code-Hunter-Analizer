"""
CodeHunter - Project Walker
Fuente única de verdad para recorrer el proyecto.
Todos los analizadores deben usar walk_project() o walk_python_files().
"""

import os
from pathlib import Path

IGNORE_DIRS = {
    # Entornos virtuales
    "venv", ".venv", "env", ".env", "virtualenv", ".virtualenv",
    # Control de versiones
    ".git", ".hg", ".svn",
    # Caché Python
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".hypothesis",
    # Build / distribución
    "build", "dist", ".eggs", "site-packages",
    # Otros
    "node_modules", ".tox", "cache", "memory", "recall",
}

# Alias de compatibilidad
IGNORED_DIRS = IGNORE_DIRS


def _should_ignore(path: str) -> bool:
    """
    Retorna True si CUALQUIER parte de la ruta es una carpeta ignorada.
    Funciona correctamente en Windows y Linux.
    """
    return any(part in IGNORE_DIRS or part.endswith(".egg-info")
               for part in Path(path).parts)


def walk_project(project_path: str):
    """
    Recorre el proyecto haciendo yield de (root, files).
    Nunca entra en entornos virtuales, cachés ni carpetas de build.
    """
    for root, dirs, files in os.walk(project_path):
        # Bloquear descenso en carpetas ignoradas (in-place)
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS and not d.endswith(".egg-info")
        ]

        # Saltar si la ruta actual contiene un segmento ignorado
        # (cubre casos donde os.walk ya entró antes del filtrado)
        if _should_ignore(root):
            continue

        yield root, files


def walk_python_files(project_path: str):
    """
    Hace yield de la ruta absoluta de cada .py en el proyecto.
    """
    for root, files in walk_project(project_path):
        for fname in files:
            if fname.endswith(".py"):
                yield os.path.join(root, fname)
