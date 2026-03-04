"""
System Doctor - Diagnóstico completo del sistema
Usa análisis avanzado con categorización profesional
"""

from .advanced_diagnostics import run_advanced_analysis
from .file_analyzer import detect_empty_python_files, detect_empty_folders
from .circular_imports import detect_circular_imports
from ..core.models import Finding, AdvancedFinding, Severity, Category


def run_code_doctor(project_path: str) -> dict:
    """
    Ejecuta diagnóstico completo del sistema
    Combina análisis legacy y avanzado
    """
    
    print("\n🩺 Ejecutando Code Doctor...")
    print("="*60)
    
    # ═══════════════════════════════════════════════════════════
    # ANÁLISIS AVANZADO (nuevo)
    # ═══════════════════════════════════════════════════════════
    advanced_result = run_advanced_analysis(project_path)
    advanced_findings = advanced_result["findings"]
    metrics = advanced_result["metrics"]
    
    # ═══════════════════════════════════════════════════════════
    # ANÁLISIS LEGACY (compatibilidad con código existente)
    # ═══════════════════════════════════════════════════════════
    
    # Archivos vacíos
    empty_files = detect_empty_python_files(project_path)
    empty_folders = detect_empty_folders(project_path)
    
    # Dependencias circulares
    cycles = detect_circular_imports(project_path)
    
    # Convertir findings legacy a AdvancedFinding
    legacy_findings = []
    
    for finding in empty_files + empty_folders:
        legacy_findings.append(AdvancedFinding(
            severity=Severity.MINOR if "vacío" in finding.message else Severity.MAJOR,
            category=Category.MAINTAINABILITY,
            message=finding.message,
            file=finding.file,
            line=finding.line,
            suggestion=finding.suggestion
        ))
    
    for cycle in cycles:
        legacy_findings.append(AdvancedFinding(
            severity=Severity.CRITICAL,
            category=Category.BUG,
            message="Dependencia circular detectada",
            file=" → ".join(cycle),
            line=0,
            suggestion="Reorganizar imports para eliminar la dependencia circular.",
            cwe_id="CWE-1047"
        ))
    
    # Combinar findings avanzados y legacy
    all_advanced_findings = advanced_findings + legacy_findings
    
    # Recalcular métricas con todos los findings
    final_metrics = calculate_final_metrics(all_advanced_findings)
    
    # ═══════════════════════════════════════════════════════════
    # CONVERSIÓN A FORMATO LEGACY (para compatibilidad)
    # ═══════════════════════════════════════════════════════════
    
    legacy_findings_list = convert_to_legacy_findings(all_advanced_findings)
    
    return {
        # Formato legacy (para compatibilidad)
        "findings": legacy_findings_list,
        "critical": final_metrics["blocker"] + final_metrics["critical"],
        "warnings": final_metrics["major"],
        "info": final_metrics["minor"] + final_metrics["info"],
        "score": final_metrics["quality_score"],
        "status": final_metrics["status"],
        
        # Formato avanzado (nuevo)
        "advanced_findings": all_advanced_findings,
        "metrics": final_metrics,
        "by_severity": {
            "blocker": final_metrics["blocker"],
            "critical": final_metrics["critical"],
            "major": final_metrics["major"],
            "minor": final_metrics["minor"],
            "info": final_metrics["info"]
        },
        "by_category": {
            "bugs": final_metrics["bugs"],
            "vulnerabilities": final_metrics["vulnerabilities"],
            "code_smells": final_metrics["code_smells"],
            "security_hotspots": final_metrics["security_hotspots"],
            "maintainability": final_metrics["maintainability"]
        }
    }


def calculate_final_metrics(findings: list) -> dict:
    """Calcula métricas finales con todos los findings"""
    
    metrics = {
        "blocker": 0,
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0,
        "bugs": 0,
        "vulnerabilities": 0,
        "code_smells": 0,
        "security_hotspots": 0,
        "maintainability": 0,
        "total": len(findings),
        "quality_score": 100,
        "status": "HEALTHY"
    }
    
    for finding in findings:
        # Severidad
        severity = finding.severity.value.lower()
        if severity in metrics:
            metrics[severity] += 1
        
        # Categoría
        category = finding.category.value.lower()
        if category in metrics:
            metrics[category] += 1
    
    # Calcular score
    score = 100
    score -= metrics["blocker"] * 25
    score -= metrics["critical"] * 15
    score -= metrics["major"] * 5
    score -= metrics["minor"] * 2
    score -= metrics["info"] * 0.5
    metrics["quality_score"] = max(int(score), 0)
    
    # Determinar estado
    if metrics["blocker"] > 0 or metrics["vulnerabilities"] > 3:
        metrics["status"] = "CRITICAL"
    elif metrics["quality_score"] < 50 or metrics["critical"] > 5:
        metrics["status"] = "WARNING"
    elif metrics["quality_score"] < 80:
        metrics["status"] = "NEEDS_ATTENTION"
    else:
        metrics["status"] = "HEALTHY"
    
    return metrics


def convert_to_legacy_findings(advanced_findings: list) -> list:
    """Convierte AdvancedFinding a Finding para compatibilidad"""
    
    legacy_findings = []
    
    for af in advanced_findings:
        # Mapear severidad avanzada a nivel legacy
        if af.severity in [Severity.BLOCKER, Severity.CRITICAL]:
            level = "CRITICAL"
        elif af.severity == Severity.MAJOR:
            level = "WARNING"
        else:
            level = "INFO"
        
        # Agregar icono de categoría al mensaje
        category_icons = {
            Category.BUG: "🐛",
            Category.VULNERABILITY: "🔒",
            Category.CODE_SMELL: "👃",
            Category.SECURITY_HOTSPOT: "🔥",
            Category.MAINTAINABILITY: "🔧"
        }
        
        icon = category_icons.get(af.category, "•")
        message = f"{icon} {af.message}"
        
        legacy_finding = Finding(
            level=level,
            message=message,
            file=af.file,
            line=af.line,
            suggestion=af.suggestion
        )
        
        legacy_findings.append(legacy_finding)
    
    return legacy_findings