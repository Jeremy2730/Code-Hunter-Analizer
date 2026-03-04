"""
Advanced Diagnostics - Orquestador de análisis avanzado
Integra todos los detectores: Bugs, Vulnerabilidades, Code Smells y Security Hotspots
"""

from typing import List, Dict
from ..core.models import AdvancedFinding, Severity, Category

from .bug_detector import detect_bugs
from .vulnerability_scanner import detect_vulnerabilities
from .code_smell_detector import detect_code_smells
from .security_hotspots import detect_security_hotspots


def run_advanced_analysis(project_path: str) -> Dict:
    """
    Ejecuta análisis avanzado completo del proyecto
    
    Returns:
        Dict con findings categorizados y métricas
    """
    
    print("🔍 Iniciando análisis avanzado...")
    
    # Ejecutar todos los detectores
    print("  🐛 Detectando bugs...")
    bugs = detect_bugs(project_path)
    
    print("  🔒 Escaneando vulnerabilidades...")
    vulnerabilities = detect_vulnerabilities(project_path)
    
    print("  👃 Analizando code smells...")
    code_smells = detect_code_smells(project_path)
    
    print("  🔥 Identificando security hotspots...")
    hotspots = detect_security_hotspots(project_path)
    
    # Combinar todos los findings
    all_findings = bugs + vulnerabilities + code_smells + hotspots
    
    # Calcular métricas
    metrics = calculate_advanced_metrics(all_findings)
    
    print(f"✅ Análisis completado: {len(all_findings)} hallazgos detectados\n")
    
    return {
        "findings": all_findings,
        "metrics": metrics,
        "by_category": {
            "bugs": bugs,
            "vulnerabilities": vulnerabilities,
            "code_smells": code_smells,
            "security_hotspots": hotspots
        }
    }


def calculate_advanced_metrics(findings: List[AdvancedFinding]) -> Dict:
    """Calcula métricas detalladas del análisis"""
    
    metrics = {
        # Por severidad
        "blocker": 0,
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0,
        
        # Por categoría
        "bugs": 0,
        "vulnerabilities": 0,
        "code_smells": 0,
        "security_hotspots": 0,
        "maintainability": 0,
        
        # Total
        "total": len(findings),
        
        # Score de calidad (0-100)
        "quality_score": 100,
        
        # Estado general
        "status": "HEALTHY"
    }
    
    # Contar por severidad y categoría
    for finding in findings:
        # Severidad
        severity = finding.severity.value.lower()
        if severity in metrics:
            metrics[severity] += 1
        
        # Categoría
        category = finding.category.value.lower()
        if category in metrics:
            metrics[category] += 1
    
    # Calcular score de calidad
    metrics["quality_score"] = calculate_quality_score(metrics)
    
    # Determinar estado
    metrics["status"] = determine_status(metrics)
    
    return metrics


def calculate_quality_score(metrics: Dict) -> int:
    """
    Calcula score de calidad (0-100)
    
    Penalizaciones:
    - BLOCKER: -25 puntos cada uno
    - CRITICAL: -15 puntos cada uno
    - MAJOR: -5 puntos cada uno
    - MINOR: -2 puntos cada uno
    - INFO: -0.5 puntos cada uno
    """
    
    score = 100
    
    score -= metrics["blocker"] * 25
    score -= metrics["critical"] * 15
    score -= metrics["major"] * 5
    score -= metrics["minor"] * 2
    score -= metrics["info"] * 0.5
    
    # No puede ser negativo
    score = max(score, 0)
    
    return int(score)


def determine_status(metrics: Dict) -> str:
    """Determina el estado general del proyecto"""
    
    score = metrics["quality_score"]
    blocker = metrics["blocker"]
    critical = metrics["critical"]
    vulnerabilities = metrics["vulnerabilities"]
    
    # Blocker o vulnerabilidades críticas = estado crítico
    if blocker > 0 or vulnerabilities > 3:
        return "CRITICAL"
    
    # Score bajo o muchos críticos = warning
    if score < 50 or critical > 5:
        return "WARNING"
    
    # Score medio = needs attention
    if score < 80:
        return "NEEDS_ATTENTION"
    
    # Todo bien
    return "HEALTHY"


def get_findings_by_severity(findings: List[AdvancedFinding], severity: Severity) -> List[AdvancedFinding]:
    """Filtra findings por severidad"""
    return [f for f in findings if f.severity == severity]


def get_findings_by_category(findings: List[AdvancedFinding], category: Category) -> List[AdvancedFinding]:
    """Filtra findings por categoría"""
    return [f for f in findings if f.category == category]


def get_top_issues(findings: List[AdvancedFinding], limit: int = 10) -> List[AdvancedFinding]:
    """
    Obtiene los issues más importantes (ordenados por severidad)
    """
    
    severity_order = {
        Severity.BLOCKER: 0,
        Severity.CRITICAL: 1,
        Severity.MAJOR: 2,
        Severity.MINOR: 3,
        Severity.INFO: 4
    }
    
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(f.severity, 99)
    )
    
    return sorted_findings[:limit]


def get_files_with_most_issues(findings: List[AdvancedFinding]) -> Dict[str, int]:
    """Identifica archivos con más problemas"""
    
    file_counts = {}
    
    for finding in findings:
        file_path = finding.file
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    # Ordenar por cantidad de issues
    sorted_files = sorted(
        file_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return dict(sorted_files[:10])  # Top 10