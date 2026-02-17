import os
from .function_analyzer import Finding
from ..utils.project_walker import walk_project


def detect_empty_python_files(project_path):
    findings = []

    for root, files in walk_project(project_path):

        for file in files:
            if not file.endswith(".py"):
                continue

            if file == "__init__.py":
                continue

            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
            except Exception:
                continue

            lines = [
                line for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

            only_imports = all(
                line.startswith("import") or line.startswith("from")
                for line in lines
            )

            if not lines or only_imports:
                findings.append(Finding(
                    level="WARNING",
                    message="Archivo Python vacío o sin código útil",
                    file=path,
                    line=1,
                    suggestion="Eliminar el archivo o implementar su lógica."
                ))

    return findings



def detect_empty_folders(project_path):
    findings = []

    for root, files in walk_project(project_path):

        # Verificar si la carpeta realmente está vacía
        if not files:
            findings.append(Finding(
                level="WARNING",
                message="Carpeta vacía detectada",
                file=root,
                line=0,
                suggestion="Eliminar la carpeta si no se utiliza."
            ))

    return findings
