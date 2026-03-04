from .ui.cli_controller import run_cli

def main():
    project_path = input("📁 Ingresa la ruta del proyecto a analizar: ").strip()

    if not project_path:
        print("❌ Debes ingresar una ruta válida")
        return

    run_cli(project_path)