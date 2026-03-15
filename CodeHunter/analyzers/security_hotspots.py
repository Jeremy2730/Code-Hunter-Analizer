"""
Security Hotspots - Identifica código sensible que requiere revisión manual
"""

import os
import ast
import logging
from typing import List
from ..core.models import AdvancedFinding, Severity, Category
from ..utils.project_walker import walk_python_files

logger = logging.getLogger(__name__)

class SecurityHotspotVisitor(ast.NodeVisitor):

    def __init__(self, file_path, lines):

        self.file_path = file_path
        self.lines = lines
        self.findings = []

    def get_snippet(self, line):
        if line <= len(self.lines):
            return self.lines[line - 1].strip()
        return ""

    def visit_Call(self, node):

        # detect_http_without_timeout
        if isinstance(node.func, ast.Attribute):

            if isinstance(node.func.value, ast.Name):

                if node.func.value.id == "requests":

                    http_methods = ['get','post','put','delete','patch','head','options']

                    if node.func.attr in http_methods:

                        has_timeout = any(kw.arg == "timeout" for kw in node.keywords)

                        if not has_timeout:

                            self.findings.append(
                                AdvancedFinding(
                                    severity=Severity.MINOR,
                                    category=Category.SECURITY_HOTSPOT,
                                    message="Request HTTP sin timeout",
                                    file=self.file_path,
                                    line=node.lineno,
                                    suggestion="Agregar timeout (ej: timeout=30).",
                                    code_snippet=self.get_snippet(node.lineno)
                                )
                            )

        # detect_ssl_verification_disabled
        for keyword in node.keywords:

            if keyword.arg == "verify":

                if isinstance(keyword.value, ast.Constant) and keyword.value.value is False:

                    self.findings.append(
                        AdvancedFinding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY_HOTSPOT,
                            message="Verificación SSL deshabilitada",
                            file=self.file_path,
                            line=node.lineno,
                            suggestion="No usar verify=False en producción.",
                            code_snippet=self.get_snippet(node.lineno),
                            cwe_id="CWE-295"
                        )
                    )

        self.generic_visit(node)

    def visit_Import(self, node):

        for alias in node.names:

            if alias.name == "random":

                self.findings.append(
                    AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="Uso de random detectado, verificar si es para seguridad",
                        file=self.file_path,
                        line=node.lineno,
                        suggestion="Usar módulo secrets para tokens o crypto.",
                        code_snippet=self.get_snippet(node.lineno)
                    )
                )

        self.generic_visit(node)


def run_hotspot_detectors(tree, file_path, lines, config):

    visitor = SecurityHotspotVisitor(file_path, lines)
    visitor.visit(tree)

    return visitor.findings


def detect_random_for_security(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta uso de random en lugar de secrets para seguridad"""
    findings = []
    
    has_random_import = False
    has_secrets_import = False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'random':
                        has_random_import = True
                    if alias.name == 'secrets':
                        has_secrets_import = True
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'random':
                    has_random_import = True
                if node.module == 'secrets':
                    has_secrets_import = True

    if has_random_import and not has_secrets_import:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == 'random'):
                        
                        line_num = node.lineno
                        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                        findings.append(AdvancedFinding(
                            severity=Severity.MAJOR,
                            category=Category.SECURITY_HOTSPOT,
                            message="Uso de 'random' detectado - verificar si se usa para seguridad",
                            file=file_path,
                            line=line_num,
                            suggestion="Si es para tokens, passwords o crypto, usar el módulo 'secrets' en su lugar.",
                            code_snippet=snippet
                        ))

    return findings


def detect_files_without_context(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta archivos abiertos sin usar context manager (with)"""
    findings = []

    class FileOpenDetector(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            self.in_with = False
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

        def visit_With(self, node):
            self.in_with = True
            self.generic_visit(node)
            self.in_with = False

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                if not self.in_with:
                    line_num = node.lineno
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                    self.findings.append(AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.SECURITY_HOTSPOT,
                        message="Archivo abierto sin context manager (with)",
                        file=file_path,
                        line=line_num,
                        suggestion="Usar 'with open(...) as f:' para garantizar cierre del archivo.",
                        code_snippet=snippet
                    ))

            self.generic_visit(node)

    try:
        detector = FileOpenDetector()
        detector.visit(tree)
        findings.extend(detector.findings)

    except RecursionError:
        logger.warning(f"RecursionError en detect_files_without_context: {file_path}")
        return findings

    return findings


def detect_ssl_verification_disabled(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta deshabilitación de verificación SSL"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == 'verify':
                    if isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                        line_num = node.lineno
                        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                        findings.append(AdvancedFinding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY_HOTSPOT,
                            message="Verificación SSL deshabilitada (verify=False)",
                            file=file_path,
                            line=line_num,
                            suggestion="Habilitar verificación SSL. Solo deshabilitar en desarrollo con advertencia clara.",
                            code_snippet=snippet,
                            cwe_id="CWE-295"
                        ))

    return findings


def detect_debug_mode(tree: ast.AST, file_path: str, lines: List[str], source: str) -> List[AdvancedFinding]:
    """Detecta modo debug activado - SOLO en archivos de configuración"""
    findings = []
    
    # 🛡️ SOLO buscar en archivos de configuración/settings
    filename = os.path.basename(file_path).lower()
    if not any(x in filename for x in ['settings', 'config', 'configuration', 'env']):
        return findings

    debug_patterns = [
        'DEBUG = True',
        'DEBUG=True',
        'debug = True',
        'debug=True',
    ]

    for i, line in enumerate(lines, 1):
        # Ignorar comentarios y docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
            
        for pattern in debug_patterns:
            if pattern in line:
                findings.append(AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.SECURITY_HOTSPOT,
                    message="Modo DEBUG activado - verificar que no esté en producción",
                    file=file_path,
                    line=i,
                    suggestion="Asegurar que DEBUG esté en False en producción. Usar variables de entorno.",
                    code_snippet=line.strip()
                ))
                break

    return findings


def detect_permissive_cors(tree: ast.AST, file_path: str, lines: List[str], source: str) -> List[AdvancedFinding]:
    """Detecta configuraciones CORS permisivas"""
    findings = []

    cors_patterns = [
        'Access-Control-Allow-Origin": "*"',
        "Access-Control-Allow-Origin': '*'",
        'CORS(origins=["*"]',
        "CORS(origins=['*']",
    ]

    for i, line in enumerate(lines, 1):
        for pattern in cors_patterns:
            if pattern in line:
                findings.append(AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.SECURITY_HOTSPOT,
                    message="CORS configurado con wildcard (*) - permite cualquier origen",
                    file=file_path,
                    line=i,
                    suggestion="Especificar orígenes permitidos explícitamente en producción.",
                    code_snippet=line.strip(),
                    cwe_id="CWE-942"
                ))
                break

    return findings


def detect_unsafe_file_permissions(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta permisos de archivo demasiado permisivos"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'os' and 
                    node.func.attr == 'chmod'):
                    
                    if len(node.args) >= 2:
                        perm_arg = node.args[1]
                        if isinstance(perm_arg, ast.Constant):
                            if perm_arg.value in [0o777, 511, 0o666, 438]:
                                line_num = node.lineno
                                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                                findings.append(AdvancedFinding(
                                    severity=Severity.MAJOR,
                                    category=Category.SECURITY_HOTSPOT,
                                    message="Permisos de archivo demasiado permisivos",
                                    file=file_path,
                                    line=line_num,
                                    suggestion="Usar permisos más restrictivos (ej: 0o644 para archivos, 0o755 para ejecutables).",
                                    code_snippet=snippet,
                                    cwe_id="CWE-732"
                                ))

    return findings


def detect_temp_file_usage(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta uso de archivos temporales sin mkstemp/NamedTemporaryFile"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant):
                        if isinstance(first_arg.value, str) and '/tmp/' in first_arg.value:
                            line_num = node.lineno
                            snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                            findings.append(AdvancedFinding(
                                severity=Severity.MINOR,
                                category=Category.SECURITY_HOTSPOT,
                                message="Archivo temporal creado manualmente en /tmp/",
                                file=file_path,
                                line=line_num,
                                suggestion="Usar tempfile.NamedTemporaryFile() o tempfile.mkstemp() para seguridad.",
                                code_snippet=snippet,
                                cwe_id="CWE-377"
                            ))

    return findings


def detect_http_without_timeout(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta requests HTTP sin timeout"""
    findings = []

    http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'requests' and 
                    node.func.attr in http_methods):
                    
                    has_timeout = any(kw.arg == 'timeout' for kw in node.keywords)
                    
                    if not has_timeout:
                        line_num = node.lineno
                        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                        findings.append(AdvancedFinding(
                            severity=Severity.MINOR,
                            category=Category.SECURITY_HOTSPOT,
                            message=f"Request HTTP sin timeout - puede colgar indefinidamente",
                            file=file_path,
                            line=line_num,
                            suggestion="Agregar timeout (ej: timeout=30) para evitar bloqueos.",
                            code_snippet=snippet
                        ))

    return findings