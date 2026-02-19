"""
CodeHunter GUI - Utilidades compartidas entre vistas.
Centraliza helpers para evitar duplicación detectada por el analizador.
"""


def get_level(f) -> str:
    """Extrae el nivel como string en minúsculas desde Finding o dict."""
    if hasattr(f, "level"):
        v = f.level
        return (v.value if hasattr(v, "value") else str(v)).lower()
    return str(f.get("level", "info")).lower()


def get_attr(f, key, default=""):
    """Lee un atributo de Finding o clave de dict de forma segura."""
    if hasattr(f, key):
        return getattr(f, key) or default
    return f.get(key, default)


def subscribe_to_state(view, state):
    """
    Registra la vista en el estado compartido.
    La vista debe implementar on_state_change(event, data).
    """
    state.subscribe(view.on_state_change)