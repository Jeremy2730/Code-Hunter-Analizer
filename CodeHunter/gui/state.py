"""
CodeHunter GUI - Estado Compartido
Objeto que viaja entre vistas para sincronizar datos del análisis.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    # Ruta del proyecto seleccionado
    project_path: str = ""

    # Resultado crudo del backend
    diagnosis_data: dict = field(default_factory=dict)

    # Hallazgos procesados
    findings: list = field(default_factory=list)

    # Score de salud (0-100)
    health_score: float = 0.0

    # Estado general
    status: str = "IDLE"   # IDLE | RUNNING | DONE | ERROR

    # Callbacks para notificar a las vistas cuando cambia el estado
    _listeners: list = field(default_factory=list, repr=False)

    def subscribe(self, callback):
        """Registra una función que se llama cuando el estado cambia."""
        self._listeners.append(callback)

    def notify(self, event: str = "update", data: Any = None):
        """Notifica a todos los suscriptores."""
        for cb in self._listeners:
            try:
                cb(event, data)
            except Exception:
                pass

    def reset(self):
        self.diagnosis_data = {}
        self.findings = []
        self.health_score = 0.0
        self.status = "IDLE"
        self.notify("reset")
