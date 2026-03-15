"""
Bug Detector - Detecta errores lógicos en el código
"""

import ast
import logging
import os
from typing import List
from ..core.models import AdvancedFinding, Severity, Category
from ..utils.project_walker import walk_python_files



MAX_FILE_LINES = 100000
MAX_AST_DEPTH = 200


def detect_bugs(project_path: str) -> List[AdvancedFinding]:
    """Detecta bugs lógicos en el proyecto"""

    findings = []
    file_count = 0

    for file_path in walk_python_files(project_path):

        file_count += 1
        if file_count % 10 == 0:
            print(f"    📄 Procesados {file_count} archivos...")

        findings.extend(analyze_file_for_bugs(file_path))

    return findings

def analyze_file_for_bugs(file_path: str) -> List[AdvancedFinding]:
    """Analiza un archivo en busca de bugs"""
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            
            # 🛡️ Saltar archivos muy grandes (>100k líneas)
            line_count = source.count('\n')
            if line_count > MAX_FILE_LINES:
                print(f"  ⚠️  Archivo muy grande ({line_count} líneas), saltando: {os.path.basename(file_path)}")
                return findings
            
            tree = ast.parse(source)
            lines = source.split('\n')

    except Exception as e:
        logging.warning(f"Error analizando {os.path.basename(file_path)}: {e}")


    # 🔍 Ejecutar detecciones con protección individual
    detectors = [
        ("except_pass", detect_except_pass),
        ("unused_variables", detect_unused_variables),
        ("constant_conditions", detect_constant_conditions),
        ("unreachable_code", detect_unreachable_code),
        ("missing_return", detect_missing_return),
        ("mutable_default_args", detect_mutable_default_args),
    ]
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

            line_count = source.count('\n')
            if line_count > MAX_FILE_LINES:
                return findings

            tree = ast.parse(source)
            lines = source.split('\n')

    except Exception as e:
        logging.warning(f"Error analizando {os.path.basename(file_path)}: {e}")
        return findings


def detect_except_pass(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta except: pass (silenciar errores sin manejo)"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
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
            self.assigned = {}
            self.used = set()
            self.depth = 0
            self.max_depth = MAX_AST_DEPTH # 🛡️ Límite de recursión

        def visit(self, node):
            self.depth += 1
            if self.depth > self.max_depth:
                return
            try:
                super().visit(node)
            finally:
                self.depth -= 1

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

    try:
        analyzer.visit(tree)
    except RecursionError:
        return findings

    for var_name, line_num in analyzer.assigned.items():

        if var_name not in analyzer.used and not var_name.startswith('_'):
            if var_name.isupper():
                continue
                    
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
            self.depth = 0
            self.max_depth = 200

        def visit(self, node):
            self.depth += 1
            if self.depth > self.max_depth:
                return
            try:
                super().visit(node)
            finally:
                self.depth -= 1

        def visit_FunctionDef(self, node):
            self.check_body(node.body)
            # NO llamar generic_visit para evitar recursión profunda

        def check_body(self, body):
            for i, stmt in enumerate(body):
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
            self.depth = 0
            self.max_depth = MAX_AST_DEPTH

        def visit(self, node):
            self.depth += 1
            if self.depth > self.max_depth:
                return
            try:
                super().visit(node)
            finally:
                self.depth -= 1

        def visit_FunctionDef(self, node):
            # Ignorar __init__
            if node.name == "__init__":
                return  # 🛡️ NO continuar visitando

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
            
            # 🛡️ NO llamar generic_visit()

    try:
        analyzer = ReturnAnalyzer()
        analyzer.visit(tree)
        findings.extend(analyzer.findings)
    except RecursionError:
        # Silenciar errores de recursión explícitamente si es necesario
        return findings
    except Exception as e:
        logging.warning(
            f"Error en detect_missing_return para {os.path.basename(file_path)}: {e}"
        )

    return findings
    
    

def detect_mutable_default_args(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta argumentos mutables por defecto ([], {})"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for i, default in enumerate(node.args.defaults):
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