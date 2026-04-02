"""
engine.py

Motor central de análisis de CodeHunter.
Ahora soporta:
✔ Activar/desactivar analyzers
✔ Perfiles (rápido / completo / seguridad)
"""

from CodeHunter.analyzers.bug_detector import detect_bugs
from CodeHunter.analyzers.code_smell_detector import detect_code_smells
from CodeHunter.analyzers.vulnerability_scanner import detect_vulnerabilities
from CodeHunter.analyzers.duplicate_detector import detect_duplicates


class AnalysisEngine:
    """Motor principal de análisis configurable"""

    def __init__(self, profile: str = "full"):
        self.profile = profile
        self.analyzers = self._load_profile(profile)

    # ═══════════════════════════════════════
    # 🧠 PERFILES
    # ═══════════════════════════════════════

    def _load_profile(self, profile: str):
        profiles = {
            "fast": [
                detect_bugs,
            ],
            "full": [
                detect_bugs,
                detect_code_smells,
                detect_vulnerabilities,
                detect_duplicates,
            ],
            "security": [
                detect_vulnerabilities,
            ]
        }

        return profiles.get(profile, profiles["full"])

    # ═══════════════════════════════════════
    # 🚀 RUN
    # ═══════════════════════════════════════

    def run(self, files):
        findings = []

        for file in files:
            for analyzer in self.analyzers:
                try:
                    findings.extend(analyzer(file))
                except Exception as e:
                    print(f"⚠️ Error en {analyzer.__name__}: {e}")

        return findings