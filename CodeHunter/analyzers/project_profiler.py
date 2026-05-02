import os
import ast
from collections import Counter
from CodeHunter.utils.project_walker import walk_project


# 🔎 Palabras clave estratégicas
FRAMEWORK_KEYWORDS = {
    "flask": "Aplicación web basada en Flask",
    "fastapi": "API REST basada en FastAPI",
    "django": "Aplicación web basada en Django",
    "pygame": "Sistema interactivo o juego con Pygame",
    "tkinter": "Aplicación de escritorio con Tkinter",
    "openai": "Sistema con integración de Inteligencia Artificial (OpenAI)",
    "torch": "Sistema basado en Machine Learning (PyTorch)",
    "tensorflow": "Sistema basado en Machine Learning (TensorFlow)",
    "argparse": "Aplicación de línea de comandos (CLI)",
    "click": "Aplicación CLI profesional",
    "requests": "Sistema con integración a servicios externos vía HTTP"
}


def build_project_profile(project_path):

    project_name = os.path.basename(project_path)

    total_py_files = 0
    total_functions = 0
    total_classes = 0
    imports_detected = []

    for root, files in walk_project(project_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            total_py_files += 1
            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                tree = ast.parse(content)

            except Exception:
                continue

            for node in ast.walk(tree):

                # Contar funciones
                if isinstance(node, ast.FunctionDef):
                    total_functions += 1

                # Contar clases
                if isinstance(node, ast.ClassDef):
                    total_classes += 1

                # Detectar imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_detected.append(alias.name.lower())

                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_detected.append(node.module.lower())

    detected_type = infer_system_type(imports_detected)

    description = generate_professional_description(
        project_name,
        detected_type,
        total_py_files,
        total_functions,
        total_classes
    )

    return {
        "name": project_name,
        "type": detected_type,
        "description": description,
        "structure": {
            "python_files": total_py_files,
            "functions": total_functions,
            "classes": total_classes
        }
    }


def infer_system_type(imports_list):

    counter = Counter()

    for imp in imports_list:
        for keyword, label in FRAMEWORK_KEYWORDS.items():
            if keyword in imp:
                counter[label] += 1

    if counter:
        return counter.most_common(1)[0][0]

    return "Sistema modular desarrollado en Python"


def generate_professional_description(
    project_name,
    system_type,
    total_files,
    total_functions,
    total_classes
):

    return (
        f"{system_type} denominado '{project_name}', "
        f"compuesto por {total_files} módulos Python, "
        f"{total_functions} funciones y {total_classes} clases. "
        f"La arquitectura del sistema evidencia una organización modular "
        f"orientada a la separación de responsabilidades, mantenibilidad "
        f"y escalabilidad estructural. "
        f"El proyecto fue analizado mediante inspección estática "
        f"para evaluar calidad, riesgos técnicos y coherencia interna."
    )
