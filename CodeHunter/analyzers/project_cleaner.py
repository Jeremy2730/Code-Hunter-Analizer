import os
import shutil

BASURA = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "build",
    "dist"
]

EXTENSIONES = [".pyc", ".pyo", ".log", ".tmp"]


def limpiar_proyecto(ruta=".", verbose=True):
    eliminados = 0
    espacio_liberado = 0

    for root, dirs, files in os.walk(ruta):

        # 🗑️ Eliminar carpetas basura
        for carpeta in dirs:
            if carpeta in BASURA:
                full_path = os.path.join(root, carpeta)
                try:
                    tamaño = obtener_tamaño_carpeta(full_path)
                    shutil.rmtree(full_path, ignore_errors=True)

                    eliminados += 1
                    espacio_liberado += tamaño

                    if verbose:
                        print("🗑️ Carpeta eliminada:", full_path)
                except:
                    pass

        # 🧹 Eliminar archivos basura
        for archivo in files:
            if any(archivo.endswith(ext) for ext in EXTENSIONES):
                full_path = os.path.join(root, archivo)
                try:
                    tamaño = os.path.getsize(full_path)
                    os.remove(full_path)

                    eliminados += 1
                    espacio_liberado += tamaño

                    if verbose:
                        print("🧹 Archivo eliminado:", full_path)
                except:
                    pass

    return {
        "eliminados": eliminados,
        "espacio_liberado": round(espacio_liberado / (1024**2), 2)
    }


def obtener_tamaño_carpeta(ruta):
    total = 0
    for root, dirs, files in os.walk(ruta):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except:
                pass
    return total