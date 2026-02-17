def print_diagnosis_report(data):
    profile = data.get("profile", {})

    print("\n" + "="*60)
    print(f"📁 Proyecto: {profile.get('name', 'N/A')}")
    print("="*60)

    print("\n🧠 Tipo de sistema:")
    print(profile.get("type", "No detectado"))

    print("\n📝 Descripción:")
    print(profile.get("description", "Sin descripción"))

    print("\n📊 Estructura:")
    structure = profile.get("structure", {})
    print(f"  • Archivos Python: {structure.get('python_files', 0)}")
    print(f"  • Funciones: {structure.get('functions', 0)}")
    print(f"  • Clases: {structure.get('classes', 0)}")

    print("\n🚨 Diagnóstico:")
    print(f"  • Críticos: {data.get('critical', 0)}")
    print(f"  • Advertencias: {data.get('warnings', 0)}")
    print(f"  • Estado: {data.get('status', 'N/A')}")

    print("\n🔍 Hallazgos:")
    for finding in data.get("findings", []):
        print(f"  - {finding}")

    print("="*60 + "\n")
