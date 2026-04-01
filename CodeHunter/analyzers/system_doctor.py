"""
System Doctor - Diagnóstico completo del sistema

Arquitectura:
- Engine: ejecuta analyzers (cerebro)
- Walker: obtiene archivos
- Doctor: orquesta + métricas + compatibilidad legacy
"""

from CodeHunter.core.engine import AnalysisEngine
from CodeHunter.utils.project_walker import walk_python_files
from CodeHunter.core.models import Finding, Severity, Category


def run_code_doctor(project_path: str) -> dict:
    """
    Punto de entrada principal del análisis
    """

    print("\n🩺 Ejecutando Code Doctor...")
    print("=" * 60)

    # 🔍 Obtener archivos
    files = list(walk_python_files(project_path))

    # 🧠 Ejecutar engine
    engine = AnalysisEngine()
    findings = engine.run(files)

    # 📊 Calcular métricas
    metrics = calculate_final_metrics(findings)

    return {
        "findings": convert_to_legacy_findings(findings),
        "advanced_findings": findings,
        "metrics": metrics,
        "score": metrics["quality_score"],
        "status": metrics["status"]
    }


# ═══════════════════════════════════════════════════════════
# 📊 MÉTRICAS
# ═══════════════════════════════════════════════════════════

def calculate_final_metrics(findings: list) -> dict:
    """Calcula métricas finales"""

    metrics = {
        # severidad
        "blocker": 0,
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0,

        # categoría
        "bugs": 0,
        "vulnerabilities": 0,
        "code_smells": 0,
        "security_hotspots": 0,
        "maintainability": 0,

        # resumen
        "total": len(findings),
        "quality_score": 100,
        "status": "HEALTHY"
    }

    for f in findings:
        # contar severidad
        sev = f.severity.value.lower()
        if sev in metrics:
            metrics[sev] += 1

        # contar categoría
        cat = f.category.value.lower()
        if cat in metrics:
            metrics[cat] += 1

    # 🎯 score
    score = 100
    score -= metrics["blocker"] * 25
    score -= metrics["critical"] * 15
    score -= metrics["major"] * 5
    score -= metrics["minor"] * 2
    score -= metrics["info"] * 0.5

    metrics["quality_score"] = max(int(score), 0)

    # 🚦 estado
    if metrics["blocker"] > 0 or metrics["vulnerabilities"] > 3:
        metrics["status"] = "CRITICAL"
    elif metrics["quality_score"] < 50 or metrics["critical"] > 5:
        metrics["status"] = "WARNING"
    elif metrics["quality_score"] < 80:
        metrics["status"] = "NEEDS_ATTENTION"
    else:
        metrics["status"] = "HEALTHY"

    return metrics


# ═══════════════════════════════════════════════════════════
# 🔄 COMPATIBILIDAD LEGACY
# ═══════════════════════════════════════════════════════════

def convert_to_legacy_findings(findings: list) -> list:
    """Convierte AdvancedFinding → Finding"""

    legacy = []

    for f in findings:

        # mapear severidad
        if f.severity in [Severity.BLOCKER, Severity.CRITICAL]:
            level = "CRITICAL"
        elif f.severity == Severity.MAJOR:
            level = "WARNING"
        else:
            level = "INFO"

        # iconos
        icons = {
            Category.BUG: "🐛",
            Category.VULNERABILITY: "🔒",
            Category.CODE_SMELL: "👃",
            Category.SECURITY_HOTSPOT: "🔥",
            Category.MAINTAINABILITY: "🔧"
        }

        message = f"{icons.get(f.category, '•')} {f.message}"

        legacy.append(Finding(
            level=level,
            message=message,
            file=f.file,
            line=f.line,
            suggestion=f.suggestion
        ))

    return legacy