"""
Duplicate Detector - Detecta código duplicado inteligente
"""

import re
from typing import List
from CodeHunter.core.models import AdvancedFinding, Severity, Category


# ═══════════════════════════════════════════════════════════
# ⚙️ CONFIG
# ═══════════════════════════════════════════════════════════

MIN_LINES_DUPLICATE = 4

IGNORED_PATTERNS = [
    "create_finding(",
    "findings.append(",
]


# ═══════════════════════════════════════════════════════════
# 🧠 HELPERS
# ═══════════════════════════════════════════════════════════

def normalize(line: str) -> str:
    line = line.strip()
    line = re.sub(r'\s+', ' ', line)
    return line


def is_ignored_line(line: str) -> bool:
    return any(pattern in line for pattern in IGNORED_PATTERNS)


def get_blocks(lines, size=MIN_LINES_DUPLICATE):
    for i in range(len(lines) - size + 1):
        yield i, tuple(lines[i:i + size])


# ═══════════════════════════════════════════════════════════
# 🚀 ENTRY POINT
# ═══════════════════════════════════════════════════════════

def detect_duplicates(file_path: str) -> List[AdvancedFinding]:
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()

    except Exception:
        return findings

    # 🔥 limpiar líneas
    lines = [
        normalize(line)
        for line in raw_lines
        if line.strip() and not is_ignored_line(line)
    ]

    seen_blocks = {}

    for index, block in get_blocks(lines):

        # ignorar bloques pequeños o vacíos
        if len(block) < MIN_LINES_DUPLICATE:
            continue

        key = hash(block)

        if key in seen_blocks:
            prev_index = seen_blocks[key]

            findings.append(AdvancedFinding(
                severity=Severity.MINOR,
                category=Category.CODE_SMELL,
                message="Posible código duplicado detectado",
                file=file_path,
                line=index + 1,
                suggestion=f"Bloque similar encontrado también en línea {prev_index + 1}",
                code_snippet="\n".join(block)
            ))
        else:
            seen_blocks[key] = index

    return findings