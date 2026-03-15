"""
CodeHunter - Project Walker
Fuente única de verdad para recorrer el proyecto.
Todos los analizadores deben usar walk_project() o walk_python_files().
"""

import os
from pathlib import Path


IGNORE_DIRS = {
    "venv", ".venv", "env", ".env", "virtualenv", ".virtualenv",
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".hypothesis",
    "build", "dist", ".eggs", "site-packages",
    "node_modules", ".tox", "cache", "memory", "recall",
}

IGNORE_FILE_PATTERNS = (
    "test_",
    "_test.py",
)

IGNORED_DIRS = IGNORE_DIRS


def _should_ignore(path: str) -> bool:
    """Retorna True si cualquier parte de la ruta es ignorada."""
    return any(
        part in IGNORE_DIRS or part.endswith(".egg-info")
        for part in Path(path).parts
    )


def walk_project(project_path: str):
    """
    Recorre el proyecto haciendo yield de (root, files).
    Nunca entra en entornos virtuales, cachés ni carpetas de build.
    """
    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS
            and not d.endswith(".egg-info")
            and not d.startswith(".")
        ]

        if _should_ignore(root):
            continue

        yield root, files


def walk_python_files(project_path: str):
    """
    Hace yield de la ruta absoluta de cada archivo .py válido.
    """
    for root, files in walk_project(project_path):

        for fname in files:

            if not fname.endswith(".py"):
                continue

            lower = fname.lower()

            if any(pattern in lower for pattern in IGNORE_FILE_PATTERNS):
                continue

            yield os.path.join(root, fname)