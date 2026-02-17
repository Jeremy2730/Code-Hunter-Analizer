"""
CodeHunter - Full Professional Diagnosis Presenter
Nivel: Profesional
"""

from datetime import datetime
from typing import Dict, Any


def print_full_diagnosis_report(report: Dict[str, Any]) -> None:
    """
    Renderiza un diagnóstico profesional completo del sistema.
    Espera el dict generado por build_full_diagnosis_data().
    """

    print("\n" + "=" * 70)
    print("🧠 CODE DOCTOR — DIAGNÓSTICO PROFESIONAL")
    print("=" * 70)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Perfil del proyecto ──────────────────────────────────────────────
    profile = report.get("profile", {})
    structure = profile.get("structure", {})

    print(f"📁 Proyecto  : {profile.get('name', 'N/A')}")
    print(f"🧠 Tipo      : {profile.get('type', 'No detectado')}")
    print()
    print(f"📊 Estructura:")
    print(f"   • Archivos Python : {structure.get('python_files', 0)}")
    print(f"   • Funciones       : {structure.get('functions', 0)}")
    print(f"   • Clases          : {structure.get('classes', 0)}")
    print()

    # ── Índice de salud ──────────────────────────────────────────────────
    score  = report.get("score", 0)
    status = report.get("status", "HEALTHY")

    status_icon = {
        "CRITICAL": "🔴 CRITICAL — Refactorización necesaria",
        "WARNING":  "🟡 WARNING  — Requiere atención",
        "HEALTHY":  "🟢 HEALTHY  — Sin problemas graves",
    }.get(status, status)

    print(f"📈 Índice de Salud : {score}/100")
    print(f"🏷  Estado          : {status_icon}")
    print("-" * 70)

    # ── Contadores ───────────────────────────────────────────────────────
    print(f"🚨 Críticos    : {report.get('critical', 0)}")
    print(f"⚠️  Advertencias: {report.get('warnings', 0)}")
    print(f"ℹ️  Informativos: {report.get('info', 0)}")
    print()

    # ── Detalle de hallazgos ─────────────────────────────────────────────
    findings = report.get("findings", [])

    print("🔍 Hallazgos detallados:")
    print("-" * 70)

    if not findings:
        print("   ✔ No se detectaron problemas relevantes.")
    else:
        for i, f in enumerate(findings, 1):
            level = f.level.value if hasattr(f.level, "value") else f.level
            icon  = {"CRITICAL": "❌", "WARNING": "⚠️ ", "INFO": "ℹ️ "}.get(level, "•")

            print(f"  {i:>3}. {icon} [{level}] {f.message}")
            print(f"        📄 {f.file}  (línea {f.line})")
            print(f"        💡 {f.suggestion}")
            print()

    # ── Descripción narrativa ────────────────────────────────────────────
    description = profile.get("description", "")
    if description:
        print("-" * 70)
        print("📝 Descripción del sistema analizado:")
        print()
        for line in description.split(". "):
            if line.strip():
                print(f"   {line.strip()}.")
        print()

    print("=" * 70)
    print("✔ Diagnóstico completado.")
    print("=" * 70)