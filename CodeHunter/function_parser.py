import ast
import os

def extract_functions(file_path, base_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    functions = []
    relative_path = os.path.relpath(file_path, base_path)
    folder, file = os.path.split(relative_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            signature = f"def {node.name}({', '.join(args)})"

            functions.append({
                "name": node.name,
                "signature": signature,
                "line": node.lineno,
                "file": file,
                "folder": folder or "."
            })

    return functions
