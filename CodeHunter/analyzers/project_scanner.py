import os
import ast

from ..core.models import Finding
from ..utils.project_walker import walk_project

from .import_analyzer import detect_unused_imports, classify_import
from .function_analyzer import analyze_function, detect_duplicate_functions


def scan_project(project_path):
    findings = []
    function_index = {}

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            analyze_file(file_path, findings, function_index, project_path)

    detect_duplicate_functions(function_index, findings)

    return findings



def analyze_file(file_path, findings, function_index, project_path):

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        tree = ast.parse(source)


        # 🔍 1️⃣ Detectar imports no usados
        unused_imports, duplicate_imports, imports_inside_functions, type_hint_only, wildcard_imports = detect_unused_imports(tree)

        

        for imp, line in unused_imports:
            level = classify_import(imp, project_path)

            findings.append(Finding(
                level,
                f"Import no utilizado: {imp}",
                file_path,
                line,
                "Eliminar import si no es necesario."
            ))


        for imp, line in duplicate_imports:
            findings.append(Finding(
                "WARNING",
                f"Import duplicado detectado: {imp}",
                file_path,
                line,
                "Eliminar una de las declaraciones repetidas."
            ))



        for imp, line in imports_inside_functions:
            findings.append(Finding(
                "WARNING",
                f"Import dentro de función detectado: {imp}",
                file_path,
                line,
                "Mover el import al inicio del archivo."
            ))

        for imp, line in type_hint_only:
            findings.append(Finding(
                "INFO",
                f"Import usado solo en anotaciones de tipo: {imp}",
                file_path,
                line,
                "Considerar usar 'from __future__ import annotations' o TYPE_CHECKING."
            ))


        for module, line in wildcard_imports:
            findings.append(Finding(
                "WARNING",
                f"Import con wildcard detectado: from {module} import *",
                file_path,
                line,
                "Evitar wildcard imports para mantener claridad y evitar conflictos."
            ))



        # 🔍 2️⃣ Analizar funciones
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analyze_function(node, file_path, source, findings, function_index)

    except Exception as e:
        findings.append(Finding(
            "WARNING",
            f"No se pudo analizar el archivo ({e.__class__.__name__})",
            file_path,
            0,
            "Revisar sintaxis o codificación del archivo."
        ))