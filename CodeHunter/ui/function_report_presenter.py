from collections import defaultdict


def report_search(function_name, results):
    if not results:
        print(f"❌ Función '{function_name}' no encontrada")
        return

    print(f"\n🔍 Función '{function_name}' encontrada en:")
    for r in results:
        print(f" - {r['file']} (línea {r['line']})")


def report_duplicates(duplicates):
    if not duplicates:
        print("\n✅ No hay funciones duplicadas")
        return

    print("\n⚠️ Funciones duplicadas detectadas:")
    for name, locations in duplicates.items():
        print(f"\n🔁 {name}:")
        for loc in locations:
            print(f" - {loc['file']} (línea {loc['line']})")


def report_all_functions(index):
    print("\nFUNCIONES ENCONTRADAS:\n")
    for name, locations in sorted(index.items()):
        print(f"🔹 {name} ({len(locations)})")


def report_by_file(index):
    files = defaultdict(list)

    for functions in index.values():
        for fn in functions:
            key = f"{fn['folder']}/{fn['file']}"
            files[key].append(fn)

    print("\nFUNCIONES AGRUPADAS POR ARCHIVO")
    #print("═" * 50)

    for file, funcs in sorted(files.items()):
        print()
        print("─" * 50)
        print(f"\n{file}\n")

        for fn in funcs:
            print(f"      • {fn['signature']}")
            print(f"         ─ línea {fn['line']}")

    print("\nFin del listado\n")

