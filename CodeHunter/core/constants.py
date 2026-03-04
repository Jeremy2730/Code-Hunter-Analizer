"""
CodeHunter - Constantes globales
Las listas de exclusión de directorios viven en project_walker.py.
Este módulo las re-exporta para compatibilidad con código legado.
"""

from CodeHunter.utils.project_walker import IGNORE_DIRS

# Alias legado — apunta al mismo objeto, no es una copia
IGNORED_DIRS = IGNORE_DIRS
