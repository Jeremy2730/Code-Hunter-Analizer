from .project_profiler import build_project_profile
from .health_calculator import calculate_health


def build_full_diagnosis_data(project_path, analysis_data):

    if not analysis_data:
        return None

    profile = build_project_profile(project_path)
    findings = analysis_data.get("findings", [])

    # Calcular health usando los findings
    health = calculate_health(findings)

    return {
        "project_path": project_path,
        "profile":      profile,
        "critical":     health["critical"],
        "warnings":     health["warnings"],
        "info":         health["info"],
        "score":        health["score"],
        "status":       health["status"],
        "findings":     findings
    }