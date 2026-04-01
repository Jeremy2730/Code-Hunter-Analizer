"""
engine.py

Motor central de análisis de CodeHunter.

Objetivo:
- Orquestar todos los analyzers
- Centralizar la lógica de ejecución
- Devolver resultados unificados

Este es el NUEVO cerebro del sistema.
"""

from CodeHunter.analyzers.bug_detector import detect_bugs
from CodeHunter.analyzers.code_smell_detector import detect_code_smells
from CodeHunter.analyzers.vulnerability_scanner import detect_vulnerabilities


class AnalysisEngine:
    """Motor principal de análisis"""

    def __init__(self):
        self.analyzers = [
            detect_bugs,
            detect_code_smells,
            detect_vulnerabilities,
            detect_code_smells
        ]

    def run(self, files):
        findings = []

        for file in files:
            for analyzer in self.analyzers:
                try:
                    findings.extend(analyzer(file))
                except Exception as e:
                    print(f"⚠️ Error en {analyzer.__name__}: {e}")

        return findings