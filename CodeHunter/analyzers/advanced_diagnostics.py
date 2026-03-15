"""
Advanced Diagnostics - Orquestador de análisis avanzado
Integra todos los detectores: Bugs, Vulnerabilidades, Code Smells y Security Hotspots
"""
import time
from typing import List, Dict
from ..core.models import AdvancedFinding, Severity, Category
from ..core.config_loader import load_config
from .analysis_engine import run_project_analysis
from collections import defaultdict
from ..utils.finding_utils import group_findings_by_category

# Penalizaciones para quality score
PENALTY_BLOCKER = 25
PENALTY_CRITICAL = 15
PENALTY_MAJOR = 5
PENALTY_MINOR = 2
PENALTY_INFO = 0.5

# Umbrales de estado
MAX_VULNERABILITIES_CRITICAL = 3
MAX_CRITICAL_WARNINGS = 5
SCORE_WARNING_THRESHOLD = 50
SCORE_ATTENTION_THRESHOLD = 80

# Otros valores
DEFAULT_SORT_WEIGHT = 99
TOP_FILES_LIMIT = 10

SEVERITY_ORDER_BLOCKER = 0
SEVERITY_ORDER_CRITICAL = 1
SEVERITY_ORDER_MAJOR = 2
SEVERITY_ORDER_MINOR = 3
SEVERITY_ORDER_INFO = 4

def group_findings_by_category(findings):

    grouped = defaultdict(list)

    for finding in findings:
        grouped[finding.category].append(finding)

    return grouped


def run_advanced_analysis(project_path: str) -> Dict:
    """
    Ejecuta análisis avanzado completo del proyecto
    """

    config = load_config(project_path)

    print("🔍 Iniciando análisis avanzado...")

    start = time.time()

    # 🚀 nuevo motor de análisis (1 solo recorrido del AST)
    all_findings = run_project_analysis(project_path, config)

    elapsed = time.time() - start

    # separar por categoría
    grouped = group_findings_by_category(all_findings)

    bugs = grouped[Category.BUG]
    vulnerabilities = grouped[Category.VULNERABILITY]
    smells = grouped[Category.CODE_SMELL]
    hotspots = grouped[Category.SECURITY_HOTSPOT]

    print(f"  🐛 Bugs: {len(bugs)}")
    print(f"  🔒 Vulnerabilidades: {len(vulnerabilities)}")
    print(f"  👃 Code Smells: {len(smells)}")
    print(f"  🔥 Hotspots: {len(hotspots)}")

    print(f"✅ Análisis completado en {elapsed:.2f}s - {len(all_findings)} hallazgos\n")

    metrics = calculate_advanced_metrics(all_findings)

    return {
        "findings": all_findings,
        "metrics": metrics,
        "by_category": {
            "bugs": bugs,
            "vulnerabilities": vulnerabilities,
            "code_smells": smells,
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
    
    score -= metrics["blocker"] * PENALTY_BLOCKER
    score -= metrics["critical"] * PENALTY_CRITICAL
    score -= metrics["major"] * PENALTY_MAJOR
    score -= metrics["minor"] * PENALTY_MINOR
    score -= metrics["info"] * PENALTY_INFO
    
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
    if blocker > 0 or vulnerabilities > MAX_VULNERABILITIES_CRITICAL:
        return "CRITICAL"
    
    # Score bajo o muchos críticos = warning
    if score < SCORE_WARNING_THRESHOLD or critical > MAX_CRITICAL_WARNINGS:
        return "WARNING"
    
    # Score medio = needs attention
    if score < SCORE_ATTENTION_THRESHOLD:
        return "NEEDS_ATTENTION"
    
    # Todo bien
    return "HEALTHY"


def get_findings_by_severity(findings: List[AdvancedFinding], severity: Severity) -> List[AdvancedFinding]:
    """Filtra findings por severidad"""
    return [f for f in findings if f.severity == severity]


def get_findings_by_category(findings: List[AdvancedFinding], category: Category) -> List[AdvancedFinding]:
    """Filtra findings por categoría"""
    return [f for f in findings if f.category == category]


def get_top_issues(findings: List[AdvancedFinding], limit: int = TOP_FILES_LIMIT) -> List[AdvancedFinding]:
    """
    Obtiene los issues más importantes (ordenados por severidad)
    """

    severity_order = {
        Severity.BLOCKER: SEVERITY_ORDER_BLOCKER,
        Severity.CRITICAL: SEVERITY_ORDER_CRITICAL,
        Severity.MAJOR: SEVERITY_ORDER_MAJOR,
        Severity.MINOR: SEVERITY_ORDER_MINOR,
        Severity.INFO: SEVERITY_ORDER_INFO
    }

    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(f.severity, DEFAULT_SORT_WEIGHT)
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
    
    return dict(sorted_files[:TOP_FILES_LIMIT])  # Top 10
