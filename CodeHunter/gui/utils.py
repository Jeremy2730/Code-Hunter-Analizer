"""
CodeHunter GUI - Utilidades compartidas entre vistas.
Compatible con objetos AdvancedFinding y dicts legacy.
"""

def get_level(f) -> str:
    """Extrae el nivel como string en minúsculas desde Finding o dict."""
    
    # 🧠 NUEVO MODELO (AdvancedFinding)
    if hasattr(f, "severity"):
        severity = f.severity
        if hasattr(severity, "value"):
            return severity.value.lower()
        return str(severity).lower()

    # 🧓 LEGACY (dict)
    if isinstance(f, dict):
        return str(f.get("level", "info")).lower()

    return "info"


def get_attr(f, key, default=""):
    """Lee un atributo de Finding o clave de dict de forma segura."""
    
    if hasattr(f, key):
        return getattr(f, key) or default

    if isinstance(f, dict):
        return f.get(key, default)

    return default


def subscribe_to_state(view, state):
    state.subscribe(view.on_state_change)