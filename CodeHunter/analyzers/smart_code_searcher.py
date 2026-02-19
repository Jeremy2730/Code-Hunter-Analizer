import os
import ast
from ..utils.project_walker import walk_project


def search_code(project_path, query):
    """Búsqueda inteligente de código - busca solo lo que el usuario escribe"""
    query = query.strip()
    results = []

    # 1️⃣ Si es una carpeta específica, mostrar archivos
    folder_path = os.path.join(project_path, query)
    if os.path.isdir(folder_path):
        results.extend(search_in_folder(folder_path))
        return results  # Solo mostrar contenido de carpeta

    # 2️⃣ Si es un keyword estructural exacto (def, class, if, etc.)
    if query.lower() in ["def", "class", "if", "elif", "else", "for", "while", "try", "except", "with", "return", "yield", "import", "from", "lambda", "async", "await"]:
        results.extend(search_keyword(project_path, query.lower()))

    # 3️⃣ Si es un identificador válido, buscar funciones/clases/variables con ese nombre
    elif is_valid_identifier(query):
        results.extend(search_definitions(project_path, query))

    # 4️⃣ Búsqueda de texto plano (para todo lo demás)
    else:
        results.extend(search_text(project_path, query))

    # Si no encontró nada como definición, buscar como texto también
    if not results:
        results.extend(search_text(project_path, query))

    # Eliminar duplicados
    seen = set()
    unique_results = []
    for r in results:
        key = (r['file'], r['line'], r['content'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    return unique_results


def search_in_folder(folder_path):
    """Listar archivos Python en una carpeta"""
    results = []

    for root, files in walk_project(folder_path):
        for file in files:
            if file.endswith(".py"):
                results.append({
                    "file": os.path.join(root, file),
                    "line": "-",
                    "content": f"📄 Archivo Python en carpeta",
                    "type": "folder"
                })

    return results


def search_keyword(project_path, keyword):
    """Buscar keywords estructurales (def, class, if, return, etc.)"""
    results = []
    
    keyword_map = {
        "def": ast.FunctionDef,
        "class": ast.ClassDef,
        "if": ast.If,
        "elif": ast.If,
        "else": ast.If,
        "for": ast.For,
        "while": ast.While,
        "try": ast.Try,
        "except": ast.ExceptHandler,
        "with": ast.With,
        "return": ast.Return,
        "yield": ast.Yield,
        "import": (ast.Import, ast.ImportFrom),
        "from": ast.ImportFrom,
        "lambda": ast.Lambda,
        "async": ast.AsyncFunctionDef,
        "await": ast.Await,
    }

    node_type = keyword_map.get(keyword)
    if not node_type:
        return results

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    source = f.read()
                    tree = ast.parse(source)
                    lines = source.split('\n')
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, node_type):
                    line_num = node.lineno
                    content = lines[line_num - 1].strip() if line_num <= len(lines) else keyword
                    
                    results.append({
                        "file": path,
                        "line": line_num,
                        "content": content,
                        "type": "keyword"
                    })

    return results


def search_definitions(project_path, name):
    """Buscar funciones, clases o variables con un nombre específico"""
    results = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    source = f.read()
                    tree = ast.parse(source)
                    lines = source.split('\n')
            except Exception:
                continue

            for node in ast.walk(tree):
                line_num = None
                content = None
                result_type = None

                # Funciones
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                    line_num = node.lineno
                    result_type = "function"

                # Clases
                elif isinstance(node, ast.ClassDef) and node.name == name:
                    line_num = node.lineno
                    result_type = "class"

                # Variables (asignaciones)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == name:
                            line_num = node.lineno
                            result_type = "variable"
                            break

                if line_num:
                    content = lines[line_num - 1].strip() if line_num <= len(lines) else name
                    results.append({
                        "file": path,
                        "line": line_num,
                        "content": content,
                        "type": result_type
                    })

    return results


def search_text(project_path, text):
    """Búsqueda de texto plano (coincidencia parcial)"""
    results = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        # Búsqueda case-insensitive
                        if text.lower() in line.lower():
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
    """Verificar si es un identificador Python válido"""
    return text.isidentifier()