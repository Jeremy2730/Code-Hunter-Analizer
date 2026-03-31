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

    def run(self, files):
        """
        Ejecuta todos los análisis sobre una lista de archivos

        :param files: lista de rutas de archivos
        :return: lista de hallazgos
        """

        findings = []

        try:
            findings.extend(detect_bugs(files))
        except Exception as e:
            print(f"⚠️ Error en bugs: {e}")

        try:
            findings.extend(detect_code_smells(files))
        except Exception as e:
            print(f"⚠️ Error en code smells: {e}")

        try:
            findings.extend(detect_vulnerabilities(files))
        except Exception as e:
            print(f"⚠️ Error en vulnerabilidades: {e}")

        return findings