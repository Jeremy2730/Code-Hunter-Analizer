import os
import ast
from pathlib import Path
from ..utils.project_walker import walk_project



def find_python_files(root_path):
    py_files = []

    for root, files in walk_project(root_path):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    return py_files



def extract_imports(file_path, project_root):
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def is_internal_module(module_path: Path, project_root: Path) -> bool:
    try:
        return module_path.resolve().is_relative_to(project_root.resolve())
    except AttributeError:
        return str(project_root.resolve()) in str(module_path.resolve())


def detect_circular_imports(project_path):
    project_root = Path(project_path)
    import_graph = {}

    # 1️⃣ Construir grafo de imports SOLO internos
    for root, files in walk_project(project_root):

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file
            module_name = file_path.relative_to(project_root)

            import_graph[module_name] = set()

            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported = project_root / (alias.name.replace(".", "/") + ".py")
                        if imported.exists() and is_internal_module(imported, project_root):
                            import_graph[module_name].add(imported.relative_to(project_root))

                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = project_root / (node.module.replace(".", "/") + ".py")
                    if imported.exists() and is_internal_module(imported, project_root):
                        import_graph[module_name].add(imported.relative_to(project_root))


    # 2️⃣ Detectar ciclos
    return find_cycles(import_graph)


def find_cycles(graph):
    visited = set()
    stack = []
    cycles = []

    def visit(node):
        if node in stack:
            idx = stack.index(node)
            cycles.append([str(n) for n in stack[idx:]])
            return
        if node in visited:
            return

        visited.add(node)
        stack.append(node)

        for neighbor in graph.get(node, []):
            visit(neighbor)

        stack.pop()

    for node in graph:
        visit(node)

    return cycles
