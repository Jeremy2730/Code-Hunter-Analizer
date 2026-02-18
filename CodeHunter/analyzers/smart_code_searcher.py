import os
import ast
from ..utils.project_walker import walk_project


STRUCTURE_KEYWORDS = {
    "def": ast.FunctionDef,
    "class": ast.ClassDef,
    "if": ast.If,
    "for": ast.For,
    "while": ast.While,
    "import": (ast.Import, ast.ImportFrom),
}


def search_code(project_path, query):  # ← CAMBIAR NOMBRE A search_code
    """Búsqueda inteligente de código"""
    query = query.strip()
    results = []

    # 1️⃣ carpeta (si existe)
    folder_path = os.path.join(project_path, query)
    if os.path.isdir(folder_path):
        results.extend(search_in_folder(folder_path))

    # 2️⃣ keyword estructural
    if query in STRUCTURE_KEYWORDS:
        results.extend(
            search_structure(project_path, STRUCTURE_KEYWORDS[query], query)
        )

    # 3️⃣ función o clase
    if is_valid_identifier(query):
        results.extend(search_function_or_class(project_path, query))

    # 4️⃣ texto plano SIEMPRE
    results.extend(search_text(project_path, query))

    return results


def search_in_folder(folder_path, query=None):
    """Buscar dentro de carpeta"""
    results = []

    for root, files in walk_project(folder_path):
        for file in files:
            if file.endswith(".py"):
                results.append({
                    "file": os.path.join(root, file),
                    "line": "-",
                    "content": "archivo en carpeta",
                    "type": "folder"
                })

    return results


def search_structure(project_path, node_types, label):
    """Buscar estructuras"""
    results = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, node_types):
                    results.append({
                        "file": path,
                        "line": node.lineno,
                        "content": label,
                        "type": "structure"
                    })

    return results


def search_function_or_class(project_path, name):
    """Buscar clase o nombre"""
    results = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    results.append({
                        "file": path,
                        "line": node.lineno,
                        "content": f"def {name}",
                        "type": "function"
                    })

                if isinstance(node, ast.ClassDef) and node.name.lower() == name.lower():
                    results.append({
                        "file": path,
                        "line": node.lineno,
                        "content": f"class {node.name}",
                        "type": "class"
                    })

    return results


def search_text(project_path, text):
    """Fallback texto plano"""
    results = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if text in line:
                            results.append({
                                "file": path,
                                "line": i,
                                "content": line.strip(),
                                "type": "text"
                            })
            except Exception:
                continue

    return results


def is_valid_identifier(text):
    """Identificador válido"""
    return text.isidentifier()