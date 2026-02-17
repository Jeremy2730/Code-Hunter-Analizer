import os
from pathlib import Path

IGNORED_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "site-packages",
    "cache",
    "memory",
    "recall"
}

def walk_project(project_path):
    for root, dirs, files in os.walk(project_path):

        # Si la ruta contiene carpeta ignorada → saltar
        if any(part in IGNORED_DIRS for part in Path(root).parts):
            continue

        # Filtrar subcarpetas
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS and not d.startswith(".")
        ]


        yield root, files
