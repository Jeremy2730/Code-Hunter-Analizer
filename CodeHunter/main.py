import os
from .ui.cli_controller import run_cli


def main():
    """Función principal de CodeHunter"""
    print("\n🧠 CodeHunter Analyzer\n")

    project_path = input("📂 Ruta del proyecto a analizar:\n> ").strip()

    if not project_path or not os.path.exists(project_path):
        print("❌ Ruta inválida")
        return

    # Ejecutar el CLI principal
    run_cli(project_path)


if __name__ == "__main__":
    main()