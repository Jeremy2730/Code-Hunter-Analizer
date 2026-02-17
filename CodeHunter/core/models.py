import os
from dataclasses import dataclass
from enum import Enum


class Level(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
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
