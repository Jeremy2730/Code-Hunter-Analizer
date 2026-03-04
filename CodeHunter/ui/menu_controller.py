def show_main_menu():
    print("\n=== CodeHunter CLI ===")
    print("1️⃣ Ver mapa del proyecto")
    print("2️⃣ Buscar código")
    print("3️⃣ Diagnóstico del sistema (Code Doctor)")
    print("4️⃣ Análisis profundo profesional")
    print("0️⃣ Salir")

    return input("\n👉 Selecciona una opción: ").strip()


def run_cli():
    while True:
        opcion = show_main_menu()

        if opcion == "1":
            print("Mostrando mapa del proyecto...")
            # llamar función real

        elif opcion == "2":
            print("Buscando código...")
            # llamar función real

        elif opcion == "3":
            print("Iniciando Code Doctor...")
            # diagnóstico

        elif opcion == "4":
            print("Ejecutando análisis profundo profesional...")
            # análisis profundo

        elif opcion == "0":
            print("Saliendo de CodeHunter...")
            break

        else:
            print("❌ Opción inválida")