"""
models.py

Define las estructuras de datos del sistema de análisis.

Objetivo:
- Representar hallazgos (issues) de forma consistente
- Separar modelo de datos de la lógica
- Permitir compatibilidad entre versiones (legacy y nueva)

Usado por:
- analyzers
- engine
- gui / cli
"""

import os
from dataclasses import dataclass
from enum import Enum


# ==============================
# 🚦 SEVERIDAD DEL PROBLEMA
# ==============================

class Severity(str, Enum):
    """Nivel de severidad del hallazgo"""
    BLOCKER = "BLOCKER"      # 🔴 Debe arreglarse inmediatamente
    CRITICAL = "CRITICAL"    # 🔴 Muy grave
    MAJOR = "MAJOR"          # 🟠 Importante
    MINOR = "MINOR"          # 🟡 Menor
    INFO = "INFO"            # 🔵 Informativo


# ==============================
# 📂 CATEGORÍA DEL PROBLEMA
# ==============================

class Category(str, Enum):
    """Categoría del hallazgo"""
    BUG = "BUG"
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"
    SECURITY_HOTSPOT = "SECURITY_HOTSPOT"
    MAINTAINABILITY = "MAINTAINABILITY"


# ==============================
# ⚠️ LEGACY (COMPATIBILIDAD)
# ==============================

class Level(str, Enum):
    """
    Nivel antiguo (mantener por compatibilidad)

    ⚠️ Usar Severity en nuevos desarrollos
    """
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    """
    Hallazgo básico (legacy)

    ⚠️ Mantener para compatibilidad con código antiguo
    """
    level: Level
    message: str
    file: str
    line: int
    suggestion: str

    def __post_init__(self):
        if isinstance(self.level, str):
            self.level = Level(self.level)

        self.file = os.path.relpath(self.file)

    def __str__(self):
        return f"[{self.level.value}] {self.message} ({self.file}:{self.line})"


# ==============================
# 🧠 MODELO PRINCIPAL (NUEVO)
# ==============================

@dataclass
class AdvancedFinding:
    """
    Hallazgo avanzado (modelo principal del sistema)

    Este debe ser el estándar para todos los analyzers nuevos.
    """
    severity: Severity
    category: Category
    message: str
    file: str
    line: int
    suggestion: str
    level: str = ""  # compatibilidad automática

    # Opcionales
    code_snippet: str = ""
    cwe_id: str = ""

    def __post_init__(self):
        # Normalizar enums
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)

        if isinstance(self.category, str):
            self.category = Category(self.category)

        # 🔥 SINCRONIZAR level AUTOMÁTICAMENTE
        severity_to_level = {
            Severity.BLOCKER: "critical",
            Severity.CRITICAL: "critical",
            Severity.MAJOR: "warning",
            Severity.MINOR: "warning",
            Severity.INFO: "info"
        }

        self.level = severity_to_level.get(self.severity, "info")

        # Normalizar ruta
        self.file = os.path.relpath(self.file)

    def __str__(self):
        icon_map = {
            Category.BUG: "🐛",
            Category.VULNERABILITY: "🔒",
            Category.CODE_SMELL: "👃",
            Category.SECURITY_HOTSPOT: "🔥",
            Category.MAINTAINABILITY: "🔧"
        }

        icon = icon_map.get(self.category, "•")

        return f"{icon} [{self.severity.value}] {self.message} ({self.file}:{self.line})"

    def to_dict(self):
        """Convertir a diccionario (para reportes, JSON, etc.)"""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id
        }