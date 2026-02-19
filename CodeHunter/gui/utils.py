"""Helpers compartidos entre vistas."""

def level(f) -> str:
    if hasattr(f, "level"):
        v = f.level
        return (v.value if hasattr(v, "value") else str(v)).lower()
    return str(f.get("level", "info")).lower()

def attr(f, key, default=""):
    if hasattr(f, key):
        return getattr(f, key) or default
    return f.get(key, default)
