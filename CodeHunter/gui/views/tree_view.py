"""
CodeHunter GUI - Vista Árbol del Proyecto
Muestra la estructura con líneas tipo ├── └──
"""

import os
import customtkinter as ctk


class TreeView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.state  = state
        self.colors = colors
        self._build_tree()
        self.state.subscribe(self._on_tree_update)

    def _build_tree(self):
        C = self.colors

        ctk.CTkLabel(self, text="Árbol del Proyecto",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C["text_primary"],
        ).grid(row=0, column=0, padx=30, pady=(28, 16), sticky="w")

        self.tree_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg_panel"], corner_radius=12)
        self.tree_frame.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")

        ctk.CTkLabel(self.tree_frame,
            text="Selecciona una carpeta de proyecto para ver su estructura.",
            font=ctk.CTkFont(family="Courier New", size=13), text_color=C["text_muted"],
        ).pack(pady=40)

    def _render_tree(self):
        for w in self.tree_frame.winfo_children():
            w.destroy()

        path = self.state.project_path
        if not path or not os.path.isdir(path):
            ctk.CTkLabel(self.tree_frame,
                text="Selecciona una carpeta de proyecto.",
                font=ctk.CTkFont(family="Courier New", size=13),
                text_color=self.colors["text_muted"],
            ).pack(pady=40)
            return

        # Nombre raíz del proyecto
        C = self.colors
        root_name = os.path.basename(path)
        ctk.CTkLabel(self.tree_frame,
            text=f"📁 {root_name}/",
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            text_color=C["accent"], anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 2))

        self._render_dir(path, prefix="")

    def _render_dir(self, dir_path, prefix):
        C = self.colors
        IGNORE = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"}

        try:
            entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name))
            entries = [e for e in entries if e.name not in IGNORE and not e.name.startswith(".")]
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            is_dir  = entry.is_dir()

            # Conector ├── o └──
            connector = "└── " if is_last else "├── "
            icon      = self._file_icon(entry.name, is_dir)

            # Color según tipo
            if is_dir:
                color  = C["accent"]
                weight = "bold"
                name   = entry.name + "/"
            else:
                color  = C["text_primary"]
                weight = "normal"
                name   = entry.name

            line = f"{prefix}{connector}{icon} {name}"

            ctk.CTkLabel(self.tree_frame,
                text=line,
                font=ctk.CTkFont(family="Courier New", size=12, weight=weight),
                text_color=color, anchor="w",
            ).pack(fill="x", padx=12, pady=0)

            # Recursión con el prefijo correcto
            if is_dir and prefix.count("│") + prefix.count(" ") // 4 < 4:
                extension = "    " if is_last else "│   "
                self._render_dir(entry.path, prefix + extension)

    def _file_icon(self, name: str, is_dir: bool) -> str:
        if is_dir:
            return "📁"
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        return {
            "py":   "🐍",
            "txt":  "📄",
            "md":   "📝",
            "json": "🔧",
            "yaml": "🔧",
            "yml":  "🔧",
            "toml": "🔧",
            "cfg":  "⚙",
            "ini":  "⚙",
            "pdf":  "📕",
            "png":  "🖼",
            "jpg":  "🖼",
        }.get(ext, "📄")

    def _on_tree_update(self, event, data):
        if event in ("folder_selected", "analysis_done", "reset"):
            self.after(0, self._render_tree)