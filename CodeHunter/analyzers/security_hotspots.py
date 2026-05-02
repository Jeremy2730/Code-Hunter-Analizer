"""
Security Hotspots - Identifica código sensible que requiere revisión manual
"""

import ast
from typing import List
from CodeHunter.core.models import AdvancedFinding, Severity, Category


# 🔹 ENTRY POINT (LO LLAMA EL ENGINE)
def detect_security_hotspots(file_path: str) -> List[AdvancedFinding]:
    return analyze_file_for_hotspots(file_path)


# 🔹 ANALIZADOR PRINCIPAL
def analyze_file_for_hotspots(file_path: str) -> List[AdvancedFinding]:
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            tree = ast.parse(source)
            lines = source.split("\n")
    except Exception:
        return findings

    findings.extend(detect_random_for_security(tree, file_path, lines))
    findings.extend(detect_files_without_context(tree, file_path, lines))
    findings.extend(detect_ssl_verification_disabled(tree, file_path, lines))
    findings.extend(detect_debug_mode(file_path, lines))
    findings.extend(detect_permissive_cors(file_path, lines))
    findings.extend(detect_unsafe_file_permissions(tree, file_path, lines))
    findings.extend(detect_temp_file_usage(tree, file_path, lines))
    findings.extend(detect_http_without_timeout(tree, file_path, lines))

    return findings


# 🔹 DETECTORES

def detect_random_for_security(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    has_random = False
    has_secrets = False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in getattr(node, "names", []):
                if alias.name == "random":
                    has_random = True
                if alias.name == "secrets":
                    has_secrets = True

    if has_random and not has_secrets:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
                    line = node.lineno
                    snippet = lines[line - 1].strip()

                    findings.append(AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="Uso de random en posible contexto sensible",
                        file=file_path,
                        line=line,
                        suggestion="Usar 'secrets' para tokens/seguridad.",
                        code_snippet=snippet
                    ))

    return findings


def detect_files_without_context(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.in_with = False
            self.results = []

        def visit_With(self, node):
            prev = self.in_with
            self.in_with = True
            self.generic_visit(node)
            self.in_with = prev

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                if not self.in_with:
                    line = node.lineno
                    snippet = lines[line - 1].strip()

                    self.results.append(AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="open() sin 'with'",
                        file=file_path,
                        line=line,
                        suggestion="Usar 'with open(...)'.",
                        code_snippet=snippet
                    ))

            self.generic_visit(node)

    v = Visitor()
    v.visit(tree)
    findings.extend(v.results)

    return findings


def detect_ssl_verification_disabled(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    line = node.lineno
                    snippet = lines[line - 1].strip()

                    findings.append(AdvancedFinding(
                        severity=Severity.CRITICAL,
                        category=Category.SECURITY_HOTSPOT,
                        message="SSL verification deshabilitado",
                        file=file_path,
                        line=line,
                        suggestion="No usar verify=False en producción.",
                        code_snippet=snippet,
                        cwe_id="CWE-295"
                    ))

    return findings


def detect_debug_mode(file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    patterns = ["DEBUG = True", "debug=True", "debug = True"]

    for i, line in enumerate(lines, 1):
        if any(p in line for p in patterns):
            findings.append(AdvancedFinding(
                severity=Severity.MAJOR,
                category=Category.SECURITY_HOTSPOT,
                message="Modo DEBUG activo",
                file=file_path,
                line=i,
                suggestion="Desactivar en producción.",
                code_snippet=line.strip()
            ))

    return findings


def detect_permissive_cors(file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    patterns = ['"*"', "'*'"]

    for i, line in enumerate(lines, 1):
        if "CORS" in line and any(p in line for p in patterns):
            findings.append(AdvancedFinding(
                severity=Severity.MAJOR,
                category=Category.SECURITY_HOTSPOT,
                message="CORS permisivo (*)",
                file=file_path,
                line=i,
                suggestion="Restringir orígenes.",
                code_snippet=line.strip()
            ))

    return findings


def detect_unsafe_file_permissions(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "chmod" and len(node.args) >= 2:
                perm = node.args[1]

                if isinstance(perm, ast.Constant) and perm.value in [0o777, 511]:
                    line = node.lineno
                    snippet = lines[line - 1].strip()

                    findings.append(AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="Permisos demasiado abiertos",
                        file=file_path,
                        line=line,
                        suggestion="Usar permisos más restrictivos.",
                        code_snippet=snippet
                    ))

    return findings


def detect_temp_file_usage(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "open" and node.args:
                arg = node.args[0]

                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "/tmp/" in arg.value:
                    line = node.lineno
                    snippet = lines[line - 1].strip()

                    findings.append(AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="Uso manual de /tmp/",
                        file=file_path,
                        line=line,
                        suggestion="Usar tempfile.",
                        code_snippet=snippet
                    ))

    return findings


def detect_http_without_timeout(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    findings = []

    methods = {"get", "post", "put", "delete", "patch"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "requests":
                if node.func.attr in methods:

                    has_timeout = any(kw.arg == "timeout" for kw in node.keywords)

                    if not has_timeout:
                        line = node.lineno
                        snippet = lines[line - 1].strip()

                        findings.append(AdvancedFinding(
                            severity=Severity.MINOR,
                            category=Category.SECURITY_HOTSPOT,
                            message="Request sin timeout",
                            file=file_path,
                            line=line,
                            suggestion="Agregar timeout.",
                            code_snippet=snippet
                        ))

    return findings