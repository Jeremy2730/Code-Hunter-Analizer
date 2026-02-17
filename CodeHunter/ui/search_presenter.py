def print_search_results(results):
    if not results:
        print("❌ No se encontraron coincidencias")
        return

    print(f"\n🔎 Coincidencias encontradas: {len(results)}\n")

    for r in results:
        print("─" * 50)
        print(f"📄 Archivo : {r['file']}")
        print(f"📍 Línea   : {r['line']}")
        print(f"🧠 Tipo    : {r['type']}")
        print(f"💬 Código  : {r['content']}")