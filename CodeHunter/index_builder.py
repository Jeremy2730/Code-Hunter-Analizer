from .function_parser import extract_functions

def build_function_index(python_files, base_path):
    index = {}
    total = len(python_files)

    for i, file in enumerate(python_files, start=1):
        print(f"🔍 [{i}/{total}] Analizando: {file}")

        functions = extract_functions(file, base_path)

        for fn in functions:
            index.setdefault(fn["name"], []).append(fn)

    return index
