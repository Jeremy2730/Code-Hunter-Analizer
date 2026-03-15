"""
Script de diagnóstico - Ver dónde se cuelga el análisis
"""

import sys
import time
from CodeHunter.analyzers.advanced_diagnostics import run_advanced_analysis

SEPARATOR_WIDTH = 60
SEPARATOR_CHAR = "="


def test_analysis(project_path: str):
    """Prueba el análisis con timeouts y debug"""
    
    print(SEPARATOR_CHAR * SEPARATOR_WIDTH)
    print("🔍 INICIANDO DIAGNÓSTICO")
    print(SEPARATOR_CHAR * SEPARATOR_WIDTH)
    print(f"Proyecto: {project_path}\n")
    
    start_total = time.time()
    
    try:
        result = run_advanced_analysis(project_path)
        
        elapsed = time.time() - start_total
        print(f"\n✅ ANÁLISIS COMPLETADO en {elapsed:.2f}s")
        print(f"Total de hallazgos: {len(result.get('findings', []))}")
        
        metrics = result.get('metrics', {})
        print(f"\nMétricas:")
        print(f"  - Blocker: {metrics.get('blocker', 0)}")
        print(f"  - Critical: {metrics.get('critical', 0)}")
        print(f"  - Major: {metrics.get('major', 0)}")
        print(f"  - Minor: {metrics.get('minor', 0)}")
        print(f"  - Score: {metrics.get('quality_score', 0)}/100")
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_total
        print(f"\n\n⚠️  INTERRUMPIDO por usuario después de {elapsed:.2f}s")
        print("El análisis se colgó en algún detector.")
        
    except Exception as e:
        elapsed = time.time() - start_total
        print(f"\n\n❌ ERROR después de {elapsed:.2f}s:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_analysis.py <ruta_proyecto>")
        print("\nEjemplo:")
        print('  python test_analysis.py "C:/mi_proyecto"')
        sys.exit(1)
    
    project_path = sys.argv[1]
    test_analysis(project_path)