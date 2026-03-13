"""
Code Smell Detector - Detecta problemas de diseño y mantenibilidad
"""

import ast
from typing import List
from ..core.models import AdvancedFinding, Severity, Category
from ..utils.project_walker import walk_project
import os


def detect_code_smells(project_path: str) -> List[AdvancedFinding]:
    """Detecta code smells en el proyecto"""
    findings = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            findings.extend(analyze_file_for_smells(file_path))

    return findings


def analyze_file_for_smells(file_path: str) -> List[AdvancedFinding]:
    """Analiza un archivo"""
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
            
            # 🛡️ PROTECCIÓN: Saltar archivos muy grandes
            if len(source) > 500000:  # 500KB
                print(f"  ⚠️  Archivo muy grande, saltando: {file_path}")
                return findings
            
            tree = ast.parse(source)
            lines = source.split('\n')

    except Exception as e:
        print(f"  ❌ Error parseando {file_path}: {str(e)[:50]}")
        return findings

    # 🔍 Ejecutar detecciones con try-catch individual
    try:
        findings.extend(detect_except_pass(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_except_pass: {str(e)[:50]}")
    
    try:
        findings.extend(detect_unused_variables(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_unused_variables: {str(e)[:50]}")
    
    try:
        findings.extend(detect_constant_conditions(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_constant_conditions: {str(e)[:50]}")
    
    try:
        findings.extend(detect_unreachable_code(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_unreachable_code: {str(e)[:50]}")
    
    try:
        findings.extend(detect_missing_return(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_missing_return: {str(e)[:50]}")
    
    try:
        findings.extend(detect_mutable_default_args(tree, file_path, lines))
    except Exception as e:
        print(f"  ⚠️  Error en detect_mutable_default_args: {str(e)[:50]}")


    # 🔍 Ejecutar detecciones
    findings.extend(detect_long_functions(tree, file_path, lines))
    findings.extend(detect_too_many_parameters(tree, file_path, lines))
    findings.extend(detect_deep_nesting(tree, file_path, lines))
    findings.extend(detect_god_classes(tree, file_path, lines))
    findings.extend(detect_poor_naming(tree, file_path, lines))
    findings.extend(detect_magic_numbers(tree, file_path, lines))
    findings.extend(detect_long_parameter_list(tree, file_path, lines))
    findings.extend(detect_duplicate_code(tree, file_path, lines))

    return findings


def detect_long_functions(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta funciones muy largas (más de 50 líneas)"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Calcular longitud de la función
            start_line = node.lineno
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
            func_length = end_line - start_line + 1

            if func_length > 50:
                snippet = lines[start_line - 1].strip() if start_line <= len(lines) else ""

                severity = Severity.MAJOR if func_length > 100 else Severity.MINOR

                findings.append(AdvancedFinding(
                    severity=severity,
                    category=Category.CODE_SMELL,
                    message=f"Función '{node.name}' muy larga ({func_length} líneas)",
                    file=file_path,
                    line=start_line,
                    suggestion="Dividir en funciones más pequeñas. Una función debería hacer una sola cosa.",
                    code_snippet=snippet
                ))

    return findings


def detect_too_many_parameters(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta funciones con demasiados parámetros (más de 5)"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Contar parámetros
            num_params = len(node.args.args)
            
            # Excluir 'self' y 'cls'
            if num_params > 0:
                first_param = node.args.args[0].arg
                if first_param in ['self', 'cls']:
                    num_params -= 1

            if num_params > 5:
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                severity = Severity.MAJOR if num_params > 7 else Severity.MINOR

                findings.append(AdvancedFinding(
                    severity=severity,
                    category=Category.CODE_SMELL,
                    message=f"Función '{node.name}' tiene demasiados parámetros ({num_params})",
                    file=file_path,
                    line=line_num,
                    suggestion="Considerar agrupar parámetros relacionados en un objeto o diccionario.",
                    code_snippet=snippet
                ))

    return findings


def detect_deep_nesting(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta anidamiento profundo (más de 4 niveles)"""
    findings = []

    class NestingAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            self.current_depth = 0
            self.max_depth = 0
            self.deepest_line = 0

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
            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth
                self.deepest_line = node.lineno

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

    analyzer = NestingAnalyzer()
    analyzer.visit(tree)
    findings.extend(analyzer.findings)

    return findings


def detect_god_classes(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta clases con demasiados métodos (más de 20)"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Contar métodos
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            num_methods = len(methods)

            if num_methods > 20:
                line_num = node.lineno
                snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                severity = Severity.MAJOR if num_methods > 30 else Severity.MINOR

                findings.append(AdvancedFinding(
                    severity=severity,
                    category=Category.CODE_SMELL,
                    message=f"Clase '{node.name}' tiene demasiados métodos ({num_methods}) - God Class",
                    file=file_path,
                    line=line_num,
                    suggestion="Dividir la clase en clases más pequeñas con responsabilidades específicas (SRP).",
                    code_snippet=snippet
                ))

    return findings


def detect_poor_naming(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta nombres de variables poco descriptivos"""
    findings = []

    poor_names = {'a', 'b', 'c', 'd', 'x', 'y', 'z', 'temp', 'tmp', 'foo', 'bar', 'baz', 'data', 'obj', 'var'}

    class NamingAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.findings = []

        def visit_FunctionDef(self, node):
            # Ignorar funciones muy cortas (lambdas conceptuales)
            if len(node.body) <= 2:
                return

            # Revisar parámetros
            for arg in node.args.args:
                if arg.arg in poor_names and arg.arg not in ['i', 'j', 'k']:  # i,j,k ok en loops
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

            self.generic_visit(node)

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

    analyzer = NamingAnalyzer()
    analyzer.visit(tree)
    findings.extend(analyzer.findings)

    return findings


def detect_magic_numbers(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta números mágicos (constantes sin nombre)"""
    findings = []

    # Números que son obvios y no necesitan constantes
    allowed_numbers = {0, 1, -1, 2, 10, 100, 1000}

    class MagicNumberDetector(ast.NodeVisitor):
        def __init__(self):
            self.findings = []
            self.in_constant = False

        def visit_Assign(self, node):
            # Si es una asignación a MAYÚSCULAS, es probablemente una constante
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    self.in_constant = True
                    self.generic_visit(node)
                    self.in_constant = False
                    return
            self.generic_visit(node)

        def visit_Constant(self, node):
            # Solo números
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                if node.value not in allowed_numbers and not self.in_constant:
                    line_num = node.lineno
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""

                    self.findings.append(AdvancedFinding(
                        severity=Severity.MINOR,
                        category=Category.CODE_SMELL,
                        message=f"Número mágico: {node.value}",
                        file=file_path,
                        line=line_num,
                        suggestion="Definir como constante con nombre descriptivo (ej: MAX_RETRIES = 3).",
                        code_snippet=snippet
                    ))

            self.generic_visit(node)

    detector = MagicNumberDetector()
    detector.visit(tree)
    findings.extend(detector.findings)

    return findings


def detect_long_parameter_list(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta llamadas a funciones con muchos argumentos posicionales"""
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Contar argumentos posicionales
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


def detect_duplicate_code(tree: ast.AST, file_path: str, lines: List[str]) -> List[AdvancedFinding]:
    """Detecta bloques de código potencialmente duplicados"""
    findings = []

    # Buscar funciones muy similares (mismo número de líneas y estructura)
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno if hasattr(node, 'end_lineno') else start
            length = end - start
            
            functions.append({
                'name': node.name,
                'start': start,
                'end': end,
                'length': length,
                'num_statements': len(node.body)
            })

    # Comparar funciones
    for i, func1 in enumerate(functions):
        for func2 in functions[i+1:]:
            # Si tienen longitud similar y mismo número de statements
            if (abs(func1['length'] - func2['length']) <= 2 and 
                func1['num_statements'] == func2['num_statements'] and
                func1['length'] > 10):  # Solo funciones no triviales
                
                snippet = lines[func1['start'] - 1].strip() if func1['start'] <= len(lines) else ""

                findings.append(AdvancedFinding(
                    severity=Severity.MINOR,
                    category=Category.CODE_SMELL,
                    message=f"Posible código duplicado entre '{func1['name']}' y '{func2['name']}'",
                    file=file_path,
                    line=func1['start'],
                    suggestion="Extraer código común a una función auxiliar.",
                    code_snippet=snippet
                ))

    return findings