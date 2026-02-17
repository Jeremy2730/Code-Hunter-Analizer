import os
from difflib import SequenceMatcher
from .utils.project_walker import walk_project


def is_similar(a, b, threshold=0.6):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


def search_code(project_path, keyword):
    results = []

    for root, files in walk_project(project_path):

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_number, line in enumerate(f, start=1):
                        clean_line = line.strip()

                        # Coincidencia exacta
                        if keyword.lower() in clean_line.lower():
                            results.append({
                                "file": file_path,
                                "line": line_number,
                                "content": clean_line,
                                "type": "exacta"
                            })
                            continue

                        # Coincidencia aproximada
                        for token in clean_line.split():
                            if is_similar(keyword, token):
                                results.append({
                                    "file": file_path,
                                    "line": line_number,
                                    "content": clean_line,
                                    "type": "similar"
                                })
                                break

            except Exception:
                pass

    return results
