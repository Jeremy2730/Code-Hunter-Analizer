from .project_profiler import build_project_profile
from .health_calculator import calculate_health  # ← AGREGAR ESTE IMPORT


def build_full_diagnosis_data(project_path, analysis_data):

    if not analysis_data:
        return None

    profile = build_project_profile(project_path)

    findings = analysis_data.get("findings", [])
    critical = analysis_data.get("critical", 0)
    warnings = analysis_data.get("warnings", 0)
    score    = analysis_data.get("score", 0)     # ← AGREGAR
    info     = analysis_data.get("info", 0)      # ← AGREGAR

    if critical == 0 and warnings == 0:
        status = "HEALTHY"
    elif critical == 0:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return {
        "project_path": project_path,
        "profile":      profile,
        "critical":     critical,
        "warnings":     warnings,
        "info":         info,       # ← AGREGAR
        "score":        score,      # ← AGREGAR
        "status":       status,
        "findings":     findings
    }