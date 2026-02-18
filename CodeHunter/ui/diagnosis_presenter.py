def print_diagnosis_report(data):
    """Diagnóstico rápido - Solo muestra si hay problemas"""
    
    print("\n" + "🩺 Ejecutando Code Doctor...")
    print("="*60)
    
    critical = data.get('critical', 0)
    warnings = data.get('warnings', 0)
    status = data.get('status', 'HEALTHY')
    
    # Solo mostrar si hay problemas
    if critical == 0 and warnings == 0:
        print("✅ Sistema saludable - No se detectaron problemas")
    else:
        print(f"🚨 Críticos: {critical}")
        print(f"⚠️  Advertencias: {warnings}")
        print(f"📊 Estado: {status}")
        print("\n🔍 Hallazgos:")
        
        for finding in data.get("findings", []):
            level = finding.level.value if hasattr(finding.level, "value") else finding.level
            icon = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(level, "•")
            print(f"  {icon} [{level}] {finding.message}")
            print(f"     📄 {finding.file} (línea {finding.line})")
            print(f"     💡 {finding.suggestion}\n")
    
    print("="*60)