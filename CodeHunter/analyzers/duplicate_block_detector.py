import ast
import hashlib
import os

from ..core.models import AdvancedFinding, Severity, Category


GLOBAL_BLOCK_HASHES = {}


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

    try:
        normalized = normalizer.visit(ast.parse(ast.unparse(node)))
        normalized = ast.fix_missing_locations(normalized)

        return hashlib.blake2b(
            ast.dump(normalized, annotate_fields=False).encode(),
            digest_size=16
        ).hexdigest()

    except Exception:
        return None


def detect_duplicate_blocks(tree, file_path, lines):

    findings = []

    for node in ast.walk(tree):

        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):

            # ignorar bloques muy pequeños
            if len(node.body) < 2:
                continue

            block_hash = structural_hash(node)

            if not block_hash:
                continue

            if block_hash in GLOBAL_BLOCK_HASHES:

                original = GLOBAL_BLOCK_HASHES[block_hash]

                snippet = lines[node.lineno - 1].strip()

                findings.append(
                    AdvancedFinding(
                        severity=Severity.MAJOR,
                        category=Category.CODE_SMELL,
                        message=(
                            f"Bloque de código duplicado similar a "
                            f"{os.path.basename(original['file'])}:{original['line']}"
                        ),
                        file=file_path,
                        line=node.lineno,
                        suggestion="Extraer este bloque en una función reutilizable.",
                        code_snippet=snippet
                    )
                )

            else:

                GLOBAL_BLOCK_HASHES[block_hash] = {
                    "file": file_path,
                    "line": node.lineno
                }

    return findings