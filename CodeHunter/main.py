import os
from .ui.cli_controller import clear_screen, pause
from .ui.menu_controller import show_main_menu
from .ui.search_presenter import print_search_results
from .ui.project_presenter import print_project_tree
from .ui.diagnosis_presenter import print_diagnosis_report
from .ui.full_report_presenter import print_full_diagnosis_report
from .file_scanner import build_project_tree
from .analyzers.system_doctor import run_system_diagnosis
from .analyzers.smart_code_searcher import smart_search
from .analyzers.full_report import build_full_diagnosis_data



def main():
    clear_screen()
    print("\n🧠 CodeHunter Analyzer\n")

    project_path = input("📂 Ruta del proyecto a analizar:\n> ").strip()

    if not project_path or not os.path.exists(project_path):
        print("❌ Ruta inválida")
        return

    analysis_cache = None  # ← todavía no se ejecuta diagnóstico

    while True:
        option = show_main_menu()

        if option == "1":
            clear_screen()
            tree = build_project_tree(project_path)
            print_project_tree(tree)
            pause()

        elif option == "2":
            clear_screen()
            query = input("🔍 Buscar: ").strip()
            results = smart_search(project_path, query)
            print_search_results(results)
            pause()

        elif option == "3":
            clear_screen()
            print("🩺 Ejecutando Code Doctor...\n")
            analysis_cache = run_system_diagnosis(project_path)
            print_diagnosis_report(analysis_cache)
            pause()


        elif option == "4":
            clear_screen()

            if not analysis_cache:
                print("⚠️ Ejecuta primero el diagnóstico normal (opción 3).")
            else:
                data = build_full_diagnosis_data(project_path, analysis_cache)
                print_full_diagnosis_report(data)

            pause()

        elif option == "0":
            print("👋 Hasta luego, cazador de bugs.")
            break

        else:
            print("❌ Opción inválida")
            pause()
