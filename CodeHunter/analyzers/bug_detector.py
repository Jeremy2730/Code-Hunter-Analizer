"""
Bug Detector - Detecta errores lógicos en el código
"""

import ast
from typing import List
from ..core.models import AdvancedFinding, Severity, Category
from ..utils.project_walker import walk_project
import os


def detect_bugs(project_path: str) -> List[AdvancedFinding]:
    """Detecta bugs lógicos en el proyecto"""
    findings = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            findings.extend(analyze_file_for_bugs(file_path))

    return findings


def analyze_file_for_bugs(file_path: str) -> List[AdvancedFinding]:
    """Analiza un archivo en busca de bugs"""
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            tree = ast.parse(source)
            lines = source.split('\n')

    except Exception:
        return findings

    # 🔍 Ejecutar detecciones
    findings.extend(detect_except_pass(tree, file_path, lines))
    findings.extend(detect_unused_variables(tree, file_path, lines))
    findings.extend(detect_constant_conditions(tree, file_path, lines))
    findings.extend(detect_unreachable_code(tree, file_path, lines))
    findings.extend(detect_missing_return(tree, file_path, lines))
    findings.extend(detect_mutable_default_args(tree, file_path, lines))

    return findings


def detect_except_pass(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta except: pass (silenciar errores sin manejo)"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # Verificar si el cuerpo solo tiene 'pass'
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                findings.append(AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.BUG,
                    message="Excepción capturada pero ignorada con 'pass'",
                    file=file_path,
                    line=line_num,
                    suggestion="Registra el error con logging o maneja apropiadamente la excepción.",
                    code_snippet=snippet
                ))

    return findings


def detect_unused_variables(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta variables asignadas pero nunca usadas"""
    findings = []

    class VariableAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.assigned = {}  # {nombre: línea}
            self.used = set()

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.assigned[target.id] = node.lineno
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                self.used.add(node.id)
            self.generic_visit(node)

    analyzer = VariableAnalyzer()
    analyzer.visit(tree)

    # Variables asignadas pero no usadas
    for var_name, line_num in analyzer.assigned.items():
        if var_name not in analyzer.used and not var_name.startswith('_'):
            snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            findings.append(AdvancedFinding(
                severity=Severity.MINOR,
                category=Category.CODE_SMELL,
                message=f"Variable '{var_name}' asignada pero nunca usada",
                file=file_path,
                line=line_num,
                suggestion=f"Eliminar la variable '{var_name}' si no es necesaria, o usar _ para indicar que es intencional.",
                code_snippet=snippet
            ))

    return findings


def detect_constant_conditions(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta condiciones que siempre son True o False"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Verificar si la condición es un literal True o False
            if isinstance(node.test, ast.Constant):
                if node.test.value is True or node.test.value is False:
                    line_num = node.lineno
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                    findings.append(AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.BUG,
                        message=f"Condición siempre es {node.test.value}",
                        file=file_path,
                        line=line_num,
                        suggestion="Revisar la lógica. Esta condición nunca cambia.",
                        code_snippet=snippet
                    ))

    return findings


def detect_unreachable_code(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta código inalcanzable después de return/raise"""
    findings = []

    class UnreachableDetector(ast.NodeVisitor):
        def __init__(self):
            self.findings = []

        def visit_FunctionDef(self, node):
            self.check_body(node.body)
            self.generic_visit(node)

        def check_body(self, body):
            for i, stmt in enumerate(body):
                # Si hay return o raise, el código siguiente es inalcanzable
                if isinstance(stmt, (ast.Return, ast.Raise)):
                    if i + 1 < len(body):
                        next_stmt = body[i + 1]
                        line_num = next_stmt.lineno
                        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                        self.findings.append(AdvancedFinding(
                            severity=Severity.MAJOR,
                            category=Category.BUG,
                            message="Código inalcanzable después de return/raise",
                            file=file_path,
                            line=line_num,
                            suggestion="Eliminar el código inalcanzable o revisar la lógica.",
                            code_snippet=snippet
                        ))
                        break

    detector = UnreachableDetector()
    detector.visit(tree)
    findings.extend(detector.findings)

    return findings


def detect_missing_return(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta funciones que a veces retornan valor y a veces no"""
    findings = []

    class ReturnAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.findings = []

        def visit_FunctionDef(self, node):
            # Ignorar __init__ y funciones decoradas con @property
            if node.name == "__init__":
                return

            has_return_with_value = False
            has_return_without_value = False

            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    if child.value is not None:
                        has_return_with_value = True
                    else:
                        has_return_without_value = True

            # Si tiene ambos tipos de return, es inconsistente
            if has_return_with_value and has_return_without_value:
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                self.findings.append(AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.BUG,
                    message=f"Función '{node.name}' retorna valor en algunos casos pero no en otros",
                    file=file_path,
                    line=line_num,
                    suggestion="Asegurar que todos los caminos de ejecución retornen un valor o ninguno.",
                    code_snippet=snippet
                ))

    analyzer = ReturnAnalyzer()
    analyzer.visit(tree)
    findings.extend(analyzer.findings)

    return findings


def detect_mutable_default_args(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta argumentos mutables por defecto ([], {})"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for i, default in enumerate(node.args.defaults):
                # Detectar listas o diccionarios como defaults
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    line_num = node.lineno
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                    findings.append(AdvancedFinding(
                        severity=Severity.CRITICAL,
                        category=Category.BUG,
                        message=f"Argumento mutable como valor por defecto en función '{node.name}'",
                        file=file_path,
                        line=line_num,
                        suggestion="Usar None como default y crear el objeto dentro de la función.",
                        code_snippet=snippet,
                        cwe_id="CWE-1188"
                    ))

    return findings