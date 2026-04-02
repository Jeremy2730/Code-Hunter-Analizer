"""
Advanced Diagnostics - Orquestador de análisis avanzado

🎯 Propósito:
Coordinar la ejecución del análisis completo del proyecto usando AnalysisEngine.

🧠 Qué hace:
- Recorre los archivos del proyecto
- Ejecuta el engine central
- Filtra resultados según perfil (fast / full / security)
- Calcula métricas avanzadas
- Agrupa hallazgos por categoría

⚙️ Perfiles:
- fast → solo bugs
- full → todo
- security → solo seguridad

🔥 Importante:
El filtrado se hace AQUÍ, no en el engine, para mantenerlo modular.
"""

from typing import List, Dict
from ..core.models import AdvancedFinding
from CodeHunter.core.engine import AnalysisEngine
from CodeHunter.utils.project_walker import walk_python_files


# ═══════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════

def run_advanced_analysis(project_path: str, profile: str = "full") -> Dict:
    """
    Ejecuta análisis avanzado del proyecto con perfil configurable.
    """

    print(f"🔍 Iniciando análisis avanzado ({profile})...")

    files = list(walk_python_files(project_path))

    engine = AnalysisEngine(profile=profile)
    all_findings = engine.run(files)

    # 🔥 APLICAR PERFIL
    filtered_findings = apply_profile_filter(all_findings, profile)

    metrics = calculate_advanced_metrics(filtered_findings)

    print(f"✅ Análisis completado: {len(filtered_findings)} hallazgos detectados\n")

    return {
        "findings": filtered_findings,
        "metrics": metrics,
        "score": metrics["quality_score"],  # 🔥 necesario para el dashboard
        "by_category": group_by_category(filtered_findings)
    }


# ═══════════════════════════════════════
# 🧠 PERFIL
# ═══════════════════════════════════════

def apply_profile_filter(findings: List[AdvancedFinding], profile: str) -> List[AdvancedFinding]:
    """
    Filtra hallazgos según el perfil seleccionado.
    """

    if profile == "fast":
        # solo bugs
        return [f for f in findings if f.category.value.lower() == "bugs"]

    elif profile == "security":
        # solo seguridad
        return [
            f for f in findings
            if f.category.value.lower() in ("vulnerabilities", "security_hotspots")
        ]

    # full → todo
    return findings


# ═══════════════════════════════════════
# 🧠 AGRUPAR
# ═══════════════════════════════════════

def group_by_category(findings: List[AdvancedFinding]) -> Dict:
    grouped = {
        "bugs": [],
        "vulnerabilities": [],
        "code_smells": [],
        "security_hotspots": []
    }

    for f in findings:
        cat = f.category.value.lower()
        if cat in grouped:
            grouped[cat].append(f)

    return grouped


# ═══════════════════════════════════════
# 📊 MÉTRICAS
# ═══════════════════════════════════════

def calculate_advanced_metrics(findings: List[AdvancedFinding]) -> Dict:
    
    metrics = {
        "blocker": 0,
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0,
        "bugs": 0,
        "vulnerabilities": 0,
        "code_smells": 0,
        "total": len(findings),
        "quality_score": 100,
        "status": "HEALTHY"
    }
    
    for finding in findings:
        severity = finding.severity.value.lower()
        category = finding.category.value.lower()

        if severity in metrics:
            metrics[severity] += 1

        if category in metrics:
            metrics[category] += 1
    
    metrics["quality_score"] = calculate_quality_score(metrics)
    metrics["status"] = determine_status(metrics)
    
    return metrics


def calculate_quality_score(metrics: Dict) -> int:
    score = 100
    score -= metrics["blocker"] * 25
    score -= metrics["critical"] * 15
    score -= metrics["major"] * 5
    score -= metrics["minor"] * 2
    score -= metrics["info"] * 0.5
    return max(int(score), 0)


def determine_status(metrics: Dict) -> str:
    score = metrics["quality_score"]

    if metrics["blocker"] > 0 or metrics["vulnerabilities"] > 3:
        return "CRITICAL"
    if score < 50 or metrics["critical"] > 5:
        return "WARNING"
    if score < 80:
        return "NEEDS_ATTENTION"

    return "HEALTHY"