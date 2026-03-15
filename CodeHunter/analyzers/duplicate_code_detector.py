import ast
import os
import hashlib

from ..core.models import AdvancedFinding, Severity, Category

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


def detect_duplicate_functions(tree, file_path, lines):

    findings = []

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):

            # ignorar funciones muy pequeñas
            if len(node.body) < 3:
                continue

            func_hash = structural_hash(node)

            if func_hash in GLOBAL_FUNCTION_HASHES:

                original = GLOBAL_FUNCTION_HASHES[func_hash]

                snippet = lines[node.lineno - 1].strip()

                findings.append(
                    AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.CODE_SMELL,
                        message=(
                            f"Función duplicada '{node.name}' "
                            f"similar a '{original['name']}' "
                            f"({os.path.basename(original['file'])})"
                        ),
                        file=file_path,
                        line=node.lineno,
                        suggestion="Extraer lógica común en función reutilizable.",
                        code_snippet=snippet
                    )
                )

            else:

                GLOBAL_FUNCTION_HASHES[func_hash] = {
                    "name": node.name,
                    "file": file_path,
                    "line": node.lineno
                }

    return findings