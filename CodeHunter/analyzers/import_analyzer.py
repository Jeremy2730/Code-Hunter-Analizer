import sys 
import importlib.util
import ast


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}
        self.used_names = set()
        self.type_hint_names = set()
        self.duplicate_imports = []
        self.imports_inside_functions = []
        self.wildcard_imports = []
        self.current_function = False

    def visit_FunctionDef(self, node):
        prev = self.current_function
        self.current_function = True
        self.generic_visit(node)
        self.current_function = prev

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]

            if name in self.imports:
                self.duplicate_imports.append((name, node.lineno))

            self.imports[name] = node.lineno

            if self.current_function:
                self.imports_inside_functions.append((name, node.lineno))

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if any(alias.name == "*" for alias in node.names):
            self.wildcard_imports.append((node.module, node.lineno))
            return

        for alias in node.names:
            name = alias.asname or alias.name

            if name in self.imports:
                self.duplicate_imports.append((name, node.lineno))

            self.imports[name] = node.lineno

            if self.current_function:
                self.imports_inside_functions.append((name, node.lineno))

        self.generic_visit(node)

    def visit_Name(self, node):
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

    def visit_arg(self, node):
        if isinstance(node.annotation, ast.Name):
            self.type_hint_names.add(node.annotation.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.annotation, ast.Name):
            self.type_hint_names.add(node.annotation.id)
        self.generic_visit(node)


def detect_unused_imports(tree):
    visitor = ImportVisitor()
    visitor.visit(tree)

    unused = []
    type_hint_only = []

    for name, line in visitor.imports.items():
        if name not in visitor.used_names:
            if name in visitor.type_hint_names:
                type_hint_only.append((name, line))
            else:
                unused.append((name, line))

    return (
        unused,
        visitor.duplicate_imports,
        visitor.imports_inside_functions,
        type_hint_only,
        visitor.wildcard_imports,
    )


def classify_import(name, project_path):
    # 1️⃣ Librería estándar
    if name in sys.builtin_module_names:
        return "INFO"

    spec = importlib.util.find_spec(name)

    if spec is None:
        return "WARNING"

    module_path = spec.origin or ""

    # 2️⃣ Interno del proyecto
    if project_path in module_path:
        return "WARNING"

    # 3️⃣ Librería estándar instalada
    if "site-packages" not in module_path:
        return "INFO"

    # 4️⃣ Terceros
    return "WARNING"