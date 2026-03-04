"""
CodeHunter - File Scanner
Genera el árbol de estructura del proyecto.
"""

import os
from CodeHunter.utils.project_walker import IGNORE_DIRS


def build_project_tree(root_path, prefix=""):
    """Genera el árbol visual de archivos del proyecto."""
    lines = []
    try:
        items = sorted(os.listdir(root_path))
    except PermissionError:
        return lines

    # Filtrar carpetas ignoradas de la lista visible
    visible = [i for i in items if i not in IGNORE_DIRS]

    for index, item in enumerate(visible):
        full_path = os.path.join(root_path, item)
        is_last   = index == len(visible) - 1
        connector = "└── " if is_last else "├── "

        if os.path.isdir(full_path):
            lines.append(prefix + connector + item + "/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_project_tree(full_path, new_prefix))
        else:
            lines.append(prefix + connector + item)

    return lines
