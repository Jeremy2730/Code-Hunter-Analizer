"""
constants.py

Contiene todas las constantes globales del sistema.

Objetivo:
- Evitar números mágicos en el código
- Centralizar configuraciones clave
- Facilitar ajustes sin modificar lógica

Este archivo es usado por:
- health_calculator
- analyzers
- engine (futuro)
"""

# ==============================
# 🎯 CONFIGURACIÓN DE SCORE
# ==============================

# Puntaje máximo de salud del proyecto
MAX_SCORE = 100

# Peso de cada tipo de problema en el score
BUG_WEIGHT = 5
SMELL_WEIGHT = 2
VULN_WEIGHT = 10


# ==============================
# 🚦 ESTADOS DEL SISTEMA
# ==============================

# Estado cuando el proyecto está saludable
STATUS_OK = "OK"

# Estado cuando hay advertencias
STATUS_WARNING = "WARNING"

# Estado crítico (muchos problemas)
STATUS_CRITICAL = "CRITICAL"