"""
CodeHunter GUI - Entry Point
"""

import sys
import os

# Apunta al directorio que CONTIENE la carpeta CodeHunter
ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(ROOT)

sys.path.insert(0, ROOT)    # Para importar gui/
sys.path.insert(0, PARENT)  # Para importar CodeHunter.infrastructure...

from gui.app import CodeHunterApp

if __name__ == "__main__":
    app = CodeHunterApp()
    app.mainloop()