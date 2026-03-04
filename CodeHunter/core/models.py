import os
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    """Nivel de severidad del hallazgo"""
    BLOCKER = "BLOCKER"      # 🔴 Debe arreglarse inmediatamente
    CRITICAL = "CRITICAL"    # 🔴 Muy grave, arreglar pronto
    MAJOR = "MAJOR"          # 🟠 Importante
    MINOR = "MINOR"          # 🟡 Menor importancia
    INFO = "INFO"            # 🔵 Informativo


class Category(str, Enum):
    """Categoría del hallazgo"""
    BUG = "BUG"                          # 🐛 Error lógico
    VULNERABILITY = "VULNERABILITY"       # 🔒 Vulnerabilidad de seguridad
    CODE_SMELL = "CODE_SMELL"            # 👃 Mal diseño o código difícil de mantener
    SECURITY_HOTSPOT = "SECURITY_HOTSPOT" # 🔥 Requiere revisión de seguridad
    MAINTAINABILITY = "MAINTAINABILITY"   # 🔧 Problemas de mantenibilidad


# Mantener Level por compatibilidad con código existente
class Level(str, Enum):
    """Nivel de hallazgo (legacy - usar Severity en nuevos análisis)"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    """Hallazgo básico (legacy - para compatibilidad)"""
    level: Level
    message: str
    file: str
    line: int
    suggestion: str

    def __post_init__(self):
        # Convertir string a Enum automáticamente
        if isinstance(self.level, str):
            self.level = Level(self.level)

        # Normalizar ruta
        self.file = os.path.relpath(self.file)

    def __str__(self):
        return f"[{self.level.value}] {self.message} ({self.file}:{self.line})"


@dataclass
class AdvancedFinding:
    """Hallazgo avanzado con categorización profesional"""
    severity: Severity       # BLOCKER, CRITICAL, MAJOR, MINOR, INFO
    category: Category       # BUG, VULNERABILITY, CODE_SMELL, SECURITY_HOTSPOT
    message: str            # Descripción del problema
    file: str               # Ruta del archivo
    line: int               # Número de línea
    suggestion: str         # Cómo arreglarlo
    code_snippet: str = ""  # Fragmento de código problemático (opcional)
    cwe_id: str = ""        # CWE ID si aplica (ej: "CWE-89" para SQL injection)

    def __post_init__(self):
        # Convertir strings a Enums automáticamente
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)
        
        if isinstance(self.category, str):
            self.category = Category(self.category)

        # Normalizar ruta
        self.file = os.path.relpath(self.file)

    def __str__(self):
        icon = {
            Category.BUG: "🐛",
            Category.VULNERABILITY: "🔒",
            Category.CODE_SMELL: "👃",
            Category.SECURITY_HOTSPOT: "🔥",
            Category.MAINTAINABILITY: "🔧"
        }.get(self.category, "•")
        
        return f"{icon} [{self.severity.value}] {self.message} ({self.file}:{self.line})"

    def to_dict(self):
        """Convertir a diccionario para reportes"""
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