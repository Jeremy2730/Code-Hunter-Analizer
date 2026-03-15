import ast
from ..utils.project_walker import walk_python_files

from .bug_detector import run_bug_detectors
from .vulnerability_scanner import run_vulnerability_detectors
from .code_smell_detector import run_smell_detectors
from .security_hotspots import run_hotspot_detectors
from .duplicate_block_detector import detect_duplicate_blocks
from .duplicate_code_detector import detect_duplicate_functions
from .duplicate_code_detector import GLOBAL_FUNCTION_HASHES
from .duplicate_block_detector import GLOBAL_BLOCK_HASHES


MAX_FILE_LINES = 100000


def run_project_analysis(project_path, config):

    GLOBAL_BLOCK_HASHES.clear()
    GLOBAL_FUNCTION_HASHES.clear()

    findings = []

    for file_path in walk_python_files(project_path):

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            if source.count("\n") > MAX_FILE_LINES:
                continue

            tree = ast.parse(source)
            lines = source.split("\n")

        except Exception:
            continue

        # ejecutar detectores
        findings.extend(run_bug_detectors(tree, file_path, lines, config))
        findings.extend(run_vulnerability_detectors(tree, file_path, lines, config))
        findings.extend(run_smell_detectors(tree, file_path, lines, config))
        findings.extend(run_hotspot_detectors(tree, file_path, lines, config))
        findings.extend(detect_duplicate_functions(tree, file_path, lines))
        findings.extend(detect_duplicate_blocks(tree, file_path, lines))

    return findings