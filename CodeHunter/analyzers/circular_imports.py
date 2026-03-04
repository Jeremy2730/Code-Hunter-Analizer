"""
CodeHunter - Circular Imports Detector
Detecta ciclos de importación dentro del proyecto usando DFS iterativo.
Soporta imports absolutos y relativos.
"""

import os
import ast
from pathlib import Path
from ..utils.project_walker import walk_project


# ──────────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────────

def find_python_files(root_path):
    """Retorna lista de rutas absolutas de todos los .py del proyecto."""
    py_files = []
    for root, files in walk_project(root_path):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def extract_imports(file_path, project_root):
    """Extrae los nombres de módulos importados en un archivo."""
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
    """Retorna True si la ruta pertenece al proyecto (no es librería externa)."""
    try:
        return module_path.resolve().is_relative_to(project_root.resolve())
    except AttributeError:
        return str(project_root.resolve()) in str(module_path.resolve())


def _resolve_import_node(node, file_path: Path, project_root: Path):
    """
    Resuelve un nodo Import o ImportFrom a una ruta .py interna.
    Soporta imports absolutos y relativos (level > 0).
    Retorna Path relativo al project_root, o None si es externo/no resuelto.
    """
    candidates = []

    if isinstance(node, ast.Import):
        for alias in node.names:
            candidates.append(
                project_root / (alias.name.replace(".", os.sep) + ".py")
            )

    elif isinstance(node, ast.ImportFrom) and node.module:
        if node.level and node.level > 0:
            # Import relativo: subir `level` directorios desde el archivo actual
            base = file_path.parent
            for _ in range(node.level - 1):
                base = base.parent
            candidates.append(
                base / (node.module.replace(".", os.sep) + ".py")
            )
        else:
            # Import absoluto
            candidates.append(
                project_root / (node.module.replace(".", os.sep) + ".py")
            )

    results = []
    for candidate in candidates:
        if candidate.exists() and is_internal_module(candidate, project_root):
            results.append(candidate.resolve().relative_to(project_root.resolve()))
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Detección de ciclos
# ──────────────────────────────────────────────────────────────────────────────

def detect_circular_imports(project_path):
    """
    Construye el grafo de imports internos y detecta ciclos.
    Retorna lista de ciclos, donde cada ciclo es una lista de strings de rutas.
    """
    project_root = Path(project_path)
    import_graph: dict[Path, set[Path]] = {}

    # 1. Construir grafo de imports internos
    for root, files in walk_project(project_root):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file

            try:
                rel = file_path.resolve().relative_to(project_root.resolve())
            except ValueError:
                continue

            import_graph[rel] = set()

            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for resolved in _resolve_import_node(node, file_path, project_root):
                        if resolved != rel:  # evitar auto-referencias
                            import_graph[rel].add(resolved)

    # 2. Detectar ciclos con DFS iterativo (sin riesgo de recursión infinita)
    return _find_cycles_iterative(import_graph)


def _find_cycles_iterative(graph: dict) -> list[list[str]]:
    """
    DFS iterativo para detección de ciclos.
    Evita RecursionError en proyectos grandes y no produce duplicados.
    """
    visited:  set = set()
    cycles:   list = []
    reported: set = set()  # evita reportar el mismo ciclo en distintas entradas

    for start_node in graph:
        if start_node in visited:
            continue

        # Pila DFS: (nodo_actual, path_hasta_aqui)
        stack = [(start_node, [start_node])]

        while stack:
            node, path = stack.pop()

            if node in visited and node not in path:
                continue

            for neighbor in graph.get(node, []):
                if neighbor in path:
                    # Ciclo encontrado
                    idx = path.index(neighbor)
                    cycle = [str(n) for n in path[idx:]]

                    # Normalizar para evitar duplicados (ciclo rotado)
                    key = tuple(sorted(cycle))
                    if key not in reported:
                        reported.add(key)
                        cycles.append(cycle)

                elif neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))

        visited.add(start_node)

    return cycles
