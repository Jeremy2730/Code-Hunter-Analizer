from .project_scanner import scan_project
from .file_analyzer import detect_empty_python_files, detect_empty_folders
from .circular_imports import detect_circular_imports
from .health_calculator import calculate_health
from ..core.models import Finding


def run_code_doctor(project_path):
    """Ejecuta diagnóstico completo del sistema"""

    findings = scan_project(project_path)
    findings.extend(detect_empty_python_files(project_path))
    findings.extend(detect_empty_folders(project_path))

    cycles = detect_circular_imports(project_path)
    for cycle in cycles:
        findings.append(
            Finding(
                level="CRITICAL",
                message="Dependencia circular detectada",
                file=" → ".join(cycle),
                line="-",
                suggestion="Reorganizar imports para eliminar la dependencia circular."
            )
        )

    health = calculate_health(findings)

    return {
        "findings": findings,
        **health
    }