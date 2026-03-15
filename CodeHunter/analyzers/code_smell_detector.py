"""
Code Smell Detector - Detecta problemas de diseño y mantenibilidad
"""
import os
import hashlib
import logging
import ast
from typing import List
from ..core.models import AdvancedFinding, Severity, Category


logger = logging.getLogger(__name__)

# Registro global de hashes de funciones (para detectar duplicados entre archivos)
GLOBAL_FUNCTION_HASHES = {}


class ASTNormalizer(ast.NodeTransformer):

    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id="var", ctx=node.ctx), node)

    def visit_arg(self, node):
        node.arg = "param"
        return node

    def visit_FunctionDef(self, node):
        node.name = "func"
        self.generic_visit(node)
        return node


def structural_hash(node):

    normalizer = ASTNormalizer()

    node_copy = ast.fix_missing_locations(
        normalizer.visit(ast.parse(ast.unparse(node)))
    )

    return hashlib.blake2b(
        ast.dump(node_copy, annotate_fields=False).encode(),
        digest_size=16
    ).hexdigest()

class GlobalAnalyzer(ast.NodeVisitor):

    def __init__(self, file_path, lines, findings, config):
        self.file_path = file_path
        self.lines = lines
        self.findings = findings
        self.config = config

    def visit_FunctionDef(self, node):

        # Detectar funciones largas
        start = node.lineno
        end = node.end_lineno if hasattr(node, "end_lineno") else start
        length = end - start

        if length > 50:

            snippet = self.lines[start-1].strip()

            self.findings.append(
                AdvancedFinding(
                    severity=Severity.MINOR if length < 100 else Severity.MAJOR,
                    category=Category.CODE_SMELL,
                    message=f"Función '{node.name}' muy larga ({length} líneas)",
                    file=self.file_path,
                    line=start,
                    suggestion="Dividir en funciones más pequeñas.",
                    code_snippet=snippet
                )
            )
        
        # Detectar demasiados parámetros
        params = len(node.args.args)

        if params > 5:

            snippet = self.lines[node.lineno-1].strip()

            self.findings.append(
                AdvancedFinding(
                    severity=Severity.MINOR,
                    category=Category.CODE_SMELL,
                    message=f"Función '{node.name}' tiene demasiados parámetros ({params})",
                    file=self.file_path,
                    line=node.lineno,
                    suggestion="Agrupar parámetros en objeto o dict.",
                    code_snippet=snippet
                )
            )

        # AST HASHING (duplicados)
        if len(node.body) > 200:
            return
        func_hash = structural_hash(node)


        if func_hash in GLOBAL_FUNCTION_HASHES:

            original = GLOBAL_FUNCTION_HASHES[func_hash]

            snippet = self.lines[node.lineno-1].strip()

            self.findings.append(
                AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.CODE_SMELL,
                    message=(
                        f"Función duplicada '{node.name}' y '{original['name']}' "
                        f"(archivo: {os.path.basename(original['file'])})"
                    ),
                    file=self.file_path,
                    line=node.lineno,
                    suggestion="Extraer lógica común en una función reutilizable.",
                    code_snippet=snippet
                )
            )

        else:

            GLOBAL_FUNCTION_HASHES[func_hash] = {
                "name": node.name,
                "line": node.lineno,
                "file": self.file_path
            }

        self.generic_visit(node)


    def visit_ClassDef(self, node):

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        if len(methods) > 20:

            snippet = self.lines[node.lineno-1].strip()

            self.findings.append(
                AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.CODE_SMELL,
                    message=f"Clase '{node.name}' tiene demasiados métodos ({len(methods)})",
                    file=self.file_path,
                    line=node.lineno,
                    suggestion="Dividir la clase en clases más pequeñas.",
                    code_snippet=snippet
                )
            )

        self.generic_visit(node)

    def visit_Constant(self, node):

        ignored_numbers = set(
            self.config.get("analysis", {}).get("ignored_numbers", [])
        )

        if isinstance(node.value, (int, float)):

            if node.value not in ignored_numbers:

                snippet = self.lines[node.lineno-1].strip()

                self.findings.append(
                    AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.CODE_SMELL,
                        message=f"Número mágico {node.value}",
                        file=self.file_path,
                        line=node.lineno,
                        suggestion="Definir constante con nombre.",
                        code_snippet=snippet
                    )
                )

        self.generic_visit(node)

def run_smell_detectors(tree, file_path, lines, config):

    findings = []

    analyzer = GlobalAnalyzer(file_path, lines, findings, config)
    analyzer.visit(tree)

    findings.extend(detect_deep_nesting(tree, file_path, lines))
    findings.extend(detect_poor_naming(tree, file_path, lines))
    findings.extend(detect_long_parameter_list(tree, file_path, lines))

    return findings


def analyze_file_for_smells(file_path: str, config: dict):
    """Analiza un archivo en busca de code smells"""
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            
            # 🛡️ Saltar archivos muy grandes
            line_count = source.count('\n')
            if line_count > 100000:
                print(f"  ⚠️  Archivo muy grande ({line_count} líneas), saltando: {os.path.basename(file_path)}")
                return findings
            
            tree = ast.parse(source)
            lines = source.split('\n')

    except Exception:
        return findings
    
    # 🚀 Nuevo análisis optimizado (1 sola pasada del AST)

    analyzer = GlobalAnalyzer(file_path, lines, findings, config)

    try:
        analyzer.visit(tree)

        findings.extend(detect_deep_nesting(tree, file_path, lines))
        findings.extend(detect_poor_naming(tree, file_path, lines))
        findings.extend(detect_long_parameter_list(tree, file_path, lines))
    except RecursionError:
        print(f"⚠️ RecursionError analizando {os.path.basename(file_path)}")

    return findings


def detect_deep_nesting(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta anidamiento profundo (más de 4 niveles)"""
    findings = []

    class NestingAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            self.current_depth = 0
            self.recursion_depth = 0
            self.max_recursion = 200

        def visit(self, node):
            self.recursion_depth += 1
            if self.recursion_depth > self.max_recursion:
                return
            try:
                super().visit(node)
            finally:
                self.recursion_depth -= 1

        def visit_If(self, node):
            self.check_depth(node)
            self.current_depth += 1
            self.generic_visit(node)
            self.current_depth -= 1

        def visit_For(self, node):
            self.check_depth(node)
            self.current_depth += 1
            self.generic_visit(node)
            self.current_depth -= 1

        def visit_While(self, node):
            self.check_depth(node)
            self.current_depth += 1
            self.generic_visit(node)
            self.current_depth -= 1

        def visit_With(self, node):
            self.check_depth(node)
            self.current_depth += 1
            self.generic_visit(node)
            self.current_depth -= 1

        def visit_Try(self, node):
            self.check_depth(node)
            self.current_depth += 1
            self.generic_visit(node)
            self.current_depth -= 1

        def check_depth(self, node):
            if self.current_depth > 4:
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                self.findings.append(AdvancedFinding(
                    severity=Severity.MAJOR,
                    category=Category.CODE_SMELL,
                    message=f"Anidamiento muy profundo (nivel {self.current_depth})",
                    file=file_path,
                    line=line_num,
                    suggestion="Extraer lógica a funciones auxiliares o usar early returns.",
                    code_snippet=snippet
                ))

    try:
        analyzer = NestingAnalyzer()
        analyzer.visit(tree)
        findings.extend(analyzer.findings)
    except RecursionError:
        logger.warning(f"RecursionError en detect_deep_nesting analizando {file_path}")

    return findings


def detect_poor_naming(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta nombres de variables poco descriptivos"""
    findings = []
    poor_names = {'a', 'b', 'c', 'd', 'x', 'y', 'z', 'temp', 'tmp', 'foo', 'bar', 'baz', 'data', 'obj', 'var'}

    class NamingAnalyzer(ast.NodeVisitor):
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
            if len(node.body) <= 2:
                return  # 🛡️ No continuar con funciones cortas

            for arg in node.args.args:
                if arg.arg in poor_names and arg.arg not in ['i', 'j', 'k']:
                    line_num = node.lineno
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                    self.findings.append(AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.CODE_SMELL,
                        message=f"Nombre poco descriptivo para parámetro: '{arg.arg}' en función '{node.name}'",
                        file=file_path,
                        line=line_num,
                        suggestion="Usar nombres descriptivos que indiquen el propósito de la variable.",
                        code_snippet=snippet
                    ))
            
            # 🛡️ NO llamar generic_visit

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in poor_names and len(target.id) == 1:
                        line_num = node.lineno
                        snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                        self.findings.append(AdvancedFinding(
                            severity=Severity.MINOR,
                            category=Category.CODE_SMELL,
                            message=f"Nombre poco descriptivo para variable: '{target.id}'",
                            file=file_path,
                            line=line_num,
                            suggestion="Usar nombres que describan el contenido o propósito de la variable.",
                            code_snippet=snippet
                        ))
            
            self.generic_visit(node)

    try:
        analyzer = NamingAnalyzer()
        analyzer.visit(tree)
        findings.extend(analyzer.findings)
    except RecursionError:
        logger.warning(f"RecursionError en detect_poor_naming analizando {file_path}")

    return findings


def detect_long_parameter_list(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta llamadas a funciones con muchos argumentos posicionales"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            num_args = len(node.args)

            if num_args > 5:
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                findings.append(AdvancedFinding(
                    severity=Severity.MINOR,
                    category=Category.CODE_SMELL,
                    message=f"Llamada a función con muchos argumentos ({num_args})",
                    file=file_path,
                    line=line_num,
                    suggestion="Considerar usar argumentos con nombre (kwargs) para mayor claridad.",
                    code_snippet=snippet
                ))

    return findings

