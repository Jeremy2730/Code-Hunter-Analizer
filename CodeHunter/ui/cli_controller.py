import os

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\n↩️ Presiona ENTER para volver al menú")

