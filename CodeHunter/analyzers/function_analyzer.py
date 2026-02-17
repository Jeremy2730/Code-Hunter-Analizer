import ast
from ..core.models import Finding


IGNORED_FUNCTIONS = {
    "__init__",
    "__str__",
    "__repr__",
    "__eq__",
    "__hash__",
    "__len__"
}

MAX_FUNCTION_LINES = 80


def analyze_function(node, file_path, source, findings, function_index):
    if node.name in IGNORED_FUNCTIONS:
        return  # Ignorar métodos especiales

    start = node.lineno
    end = getattr(node, "end_lineno", start)
    size = end - start + 1

    body_text = ast.get_source_segment(source, node) or ""
    body_hash = hash(normalize_code(body_text))

    function_index.setdefault(node.name, []).append({
        "file": file_path,
        "line": start,
        "size": size,
        "hash": body_hash
    })

    if size > MAX_FUNCTION_LINES:
        findings.append(Finding(
            "WARNING",
            f"Función muy grande: {node.name} ({size} líneas)",
            file_path,
            start,
            "Divide la función en responsabilidades más pequeñas."
        ))


def detect_duplicate_functions(index, findings):
    for name, items in index.items():
        if len(items) > 1:
            hashes = {item["hash"] for item in items}

            level = "CRITICAL" if len(hashes) > 1 else "WARNING"
            msg = (
                f"Función '{name}' duplicada con implementaciones distintas"
                if level == "CRITICAL"
                else f"Función '{name}' duplicada en varios archivos"
            )

            for item in items:
                findings.append(Finding(
                    level,
                    msg,
                    item["file"],
                    item["line"],
                    "Centraliza esta función en un solo módulo."
                ))        


def normalize_code(code):
    return "\n".join(
        line.strip()
        for line in code.splitlines()
        if line.strip()
    )


def build_signature(node):
    args = [arg.arg for arg in node.args.args]
    return f"def {node.name}({', '.join(args)}):"

