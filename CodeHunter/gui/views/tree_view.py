"""
CodeHunter GUI - Vista Árbol del Proyecto
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

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 16), sticky="ew")

        ctk.CTkLabel(header, text="Árbol del Proyecto",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C["text_primary"],
        ).pack(side="left")

        self.project_title = ctk.CTkLabel(header, text="",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"],
        )
        self.project_title.pack(side="left", padx=16)

        self.tree_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg_panel"], corner_radius=12)
        self.tree_frame.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")

        self._placeholder = ctk.CTkLabel(self.tree_frame,
            text="Selecciona una carpeta de proyecto para ver su estructura.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"])
        self._placeholder.pack(pady=40)

    def _update_project_title(self):
        name = os.path.basename(self.state.project_path) if self.state.project_path else ""
        self.project_title.configure(text=f"📂  {name}" if name else "")

    def _render_tree(self):
        for w in self.tree_frame.winfo_children():
            w.destroy()

        self._update_project_title()

        path = self.state.project_path
        if not path or not os.path.isdir(path):
            ctk.CTkLabel(self.tree_frame,
                text="Selecciona una carpeta de proyecto.",
                font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"],
            ).pack(pady=40)
            return

        self._render_dir(self.tree_frame, path, depth=0)

    def _render_dir(self, parent, dir_path, depth):
        C = self.colors
        IGNORE = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".vscode"}

        try:
            entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return

        for entry in entries:
            if entry.name in IGNORE or entry.name.startswith("."):
                continue

            indent  = depth * 18
            is_dir  = entry.is_dir()
            icon    = "📁" if is_dir else self._file_icon(entry.name)
            color   = C["accent"] if is_dir else C["text_primary"]
            weight  = "bold" if is_dir else "normal"

            row = ctk.CTkFrame(parent, fg_color="transparent", height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(row,
                text=f"{'  ' * depth}{icon}  {entry.name}",
                font=ctk.CTkFont(size=12, weight=weight),
                text_color=color, anchor="w",
            ).pack(side="left", padx=(8 + indent, 0))

            if is_dir and depth < 3:
                self._render_dir(parent, entry.path, depth + 1)

    def _file_icon(self, name: str) -> str:
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        return {
            "py": "🐍", "txt": "📄", "md": "📝",
            "json": "🔧", "yaml": "🔧", "yml": "🔧",
            "toml": "🔧", "cfg": "⚙", "ini": "⚙",
            "pdf": "📕", "png": "🖼", "jpg": "🖼",
        }.get(ext, "📄")

    def _on_tree_update(self, event, data):
        if event in ("folder_selected", "analysis_done", "reset"):
            self.after(0, self._render_tree)
