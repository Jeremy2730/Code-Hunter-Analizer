"""
Bug Detector - Detecta errores lógicos en el código
"""

import ast
from typing import List
from CodeHunter.core.models import AdvancedFinding, Severity, Category


# ═══════════════════════════════════════════════════════════
# 🧠 HELPER CENTRAL
# ═══════════════════════════════════════════════════════════

def create_finding(
    *,
    severity,
    category,
    message,
    file_path,
    line_num,
    lines,
    suggestion,
    code_snippet=None,
    cwe_id=None
) -> AdvancedFinding:

    snippet = code_snippet
    if snippet is None:
        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

    return AdvancedFinding(
        severity=severity,
        category=category,
        message=message,
        file=file_path,
        line=line_num,
        suggestion=suggestion,
        code_snippet=snippet,
        cwe_id=cwe_id
    )


# ═══════════════════════════════════════════════════════════
# 🚀 ENTRY POINT
# ═══════════════════════════════════════════════════════════

def detect_bugs(file_path: str) -> List[AdvancedFinding]:
    """
    Analiza UN archivo en busca de bugs
    (Compatible con AnalysisEngine)
    """
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


# ═══════════════════════════════════════════════════════════
# 🔍 DETECTORES
# ═══════════════════════════════════════════════════════════

def detect_except_pass(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                findings.append(create_finding(
                    severity=Severity.MAJOR,
                    category=Category.BUG,
                    message="Excepción capturada pero ignorada con 'pass'",
                    file_path=file_path,
                    line_num=node.lineno,
                    lines=lines,
                    suggestion="Registra el error o maneja la excepción correctamente."
                ))

    return findings


def detect_unused_variables(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    class VariableAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.assigned = {}
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

    for var_name, line_num in analyzer.assigned.items():
        if var_name not in analyzer.used and not var_name.startswith('_'):
            findings.append(create_finding(
                severity=Severity.MINOR,
                category=Category.CODE_SMELL,
                message=f"Variable '{var_name}' no usada",
                file_path=file_path,
                line_num=line_num,
                lines=lines,
                suggestion=f"Eliminar '{var_name}' o usar _ si es intencional."
            ))

    return findings


def detect_constant_conditions(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant):
            if node.test.value in [True, False]:
                findings.append(create_finding(
                    severity=Severity.MAJOR,
                    category=Category.BUG,
                    message=f"Condición siempre {node.test.value}",
                    file_path=file_path,
                    line_num=node.lineno,
                    lines=lines,
                    suggestion="Revisar lógica, condición constante."
                ))

    return findings


def detect_unreachable_code(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    class Detector(ast.NodeVisitor):
        def __init__(self):
            self.findings = []

        def visit_FunctionDef(self, node):
            for i, stmt in enumerate(node.body):
                if isinstance(stmt, (ast.Return, ast.Raise)) and i + 1 < len(node.body):
                    next_stmt = node.body[i + 1]

                    self.findings.append(create_finding(
                        severity=Severity.MAJOR,
                        category=Category.BUG,
                        message="Código inalcanzable",
                        file_path=file_path,
                        line_num=next_stmt.lineno,
                        lines=lines,
                        suggestion="Eliminar o revisar lógica."
                    ))
                    break

    detector = Detector()
    detector.visit(tree)
    findings.extend(detector.findings)

    return findings


def detect_missing_return(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name != "__init__":

            has_value = False
            has_empty = False

            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    if child.value:
                        has_value = True
                    else:
                        has_empty = True

            if has_value and has_empty:
                findings.append(create_finding(
                    severity=Severity.MAJOR,
                    category=Category.BUG,
                    message=f"Retornos inconsistentes en '{node.name}'",
                    file_path=file_path,
                    line_num=node.lineno,
                    lines=lines,
                    suggestion="Unificar retornos."
                ))

    return findings


def detect_mutable_default_args(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(create_finding(
                        severity=Severity.CRITICAL,
                        category=Category.BUG,
                        message=f"Argumento mutable en '{node.name}'",
                        file_path=file_path,
                        line_num=node.lineno,
                        lines=lines,
                        suggestion="Usar None y crear dentro.",
                        cwe_id="CWE-1188"
                    ))

    return findings
    