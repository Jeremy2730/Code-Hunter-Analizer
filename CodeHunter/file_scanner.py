import os

IGNORE_DIRS = {
    ".venv", "__pycache__", ".git", ".idea", ".vscode",
    "node_modules", "site-packages", "cache", "memory", "recall"
}

def build_project_tree(root_path, prefix=""):
    lines = []
    items = sorted(os.listdir(root_path))

    for index, item in enumerate(items):
        full_path = os.path.join(root_path, item)

        if item in IGNORE_DIRS:
            continue

        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "

        if os.path.isdir(full_path):
            lines.append(prefix + connector + item + "/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_project_tree(full_path, new_prefix))
        else:
            lines.append(prefix + connector + item)

    return lines
