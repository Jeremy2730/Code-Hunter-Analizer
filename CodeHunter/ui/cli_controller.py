import os
from CodeHunter.ui.menu_controller import show_main_menu
from CodeHunter.ui.project_presenter import print_project_tree
from CodeHunter.ui.search_presenter import print_search_results
from CodeHunter.ui.diagnosis_presenter import print_diagnosis_report
from CodeHunter.ui.full_report_presenter import print_full_diagnosis_report, ask_export_pdf
from CodeHunter.infrastructure.pdf_exporter import export_report_to_pdf

from CodeHunter.analyzers.project_scanner import scan_project_structure
from CodeHunter.analyzers.smart_code_searcher import search_code
from CodeHunter.analyzers.system_doctor import run_code_doctor
from CodeHunter.analyzers.full_report import build_full_diagnosis_data


def clear_screen():
    """Limpia la pantalla de la terminal"""
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    """Pausa hasta que el usuario presione ENTER"""
    input("\n↩️ Presiona ENTER para volver al menú")


def run_cli(project_path):
    """Controlador principal del CLI"""
    while True:
        clear_screen()
        print("\n🎯 CODE HUNTER - ANALIZADOR PROFESIONAL DE PROYECTOS PYTHON\n")
        
        option = show_main_menu()

        if option == "1":
            clear_screen()
            tree = scan_project_structure(project_path)
            print_project_tree(tree)
            pause()

        elif option == "2":
            clear_screen()
            query = input("🔎 Buscar código (palabra clave): ").strip()
            if query:
                results = search_code(project_path, query)
                print_search_results(results)
            pause()

        elif option == "3":
            clear_screen()
            analysis_data = run_code_doctor(project_path)
            print_diagnosis_report(analysis_data)
            pause()

        elif option == "4":
            clear_screen()
            analysis_data = run_code_doctor(project_path)
            full_report = build_full_diagnosis_data(project_path, analysis_data)
            
            if full_report:
                print_full_diagnosis_report(full_report)
                
                # Preguntar si quiere PDF
                if ask_export_pdf():
                    try:
                        profile = full_report.get("profile", {})
                        description = profile.get("description", "Sin descripción")
                        
                        pdf_path = export_report_to_pdf(
                            project_path,
                            description,
                            full_report
                        )
                        print(f"\n✅ PDF generado exitosamente:")
                        print(f"   📁 {pdf_path}")
                    except Exception as e:
                        print(f"\n❌ Error al generar PDF: {e}")
            
            pause()

        elif option == "0":
            print("\n👋 ¡Hasta luego!\n")
            break

        else:
            print("\n⚠️ Opción no válida")
            pause()