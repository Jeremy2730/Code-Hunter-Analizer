"""
CodeHunter GUI - Entry Point
Ejecutar desde la raíz del proyecto: python main_gui.py
"""

import sys
import os

# Asegura que el proyecto raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import CodeHunterApp

if __name__ == "__main__":
    app = CodeHunterApp()
    app.mainloop()
