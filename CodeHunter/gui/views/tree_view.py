"""
TreeView - Explorador visual del proyecto (tipo VSCode)

Responsabilidad:
- Mostrar estructura de carpetas y archivos
- Permitir navegación interactiva (expandir/colapsar)
- Mostrar preview de archivos seleccionados
- Resaltar líneas con errores (findings)

Características:
- Ignora carpetas basura (venv, cache, etc)
- Hover UI tipo editor moderno
- Preview integrado (sin abrir ventanas nuevas)
- Soporte para múltiples highlights

Extras:
- Exportación del árbol del proyecto a PDF

Depende de:
- AppState (estado global)
- project_walker (filtrado de archivos)
- tree_pdf_exporter (exportación)
"""



import os
import customtkinter as ctk
from tkinter import messagebox
from CodeHunter.utils.project_walker import IGNORE_DIRS
from CodeHunter.infrastructure.tree_pdf_exporter import export_tree_to_pdf


class TreeView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)

        self.state = state
        self.colors = colors
        self.expanded = set()

        # 🔥 FIX LAYOUT GLOBAL
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.state.subscribe(self._on_tree_update)

    # ───────────────── UI ─────────────────
    def _build_ui(self):
        C = self.colors

        # ───────── TOP BAR
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(5, 0))

        btn_export = ctk.CTkButton(
            top_bar,
            text="🌳 Exportar Árbol",
            height=36,
            command=self.export_tree_pdf
        )
        btn_export.pack(side="left")

        # ───────── CONTENEDOR
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # 🔥 PROPORCIÓN REAL
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=7)
        container.grid_rowconfigure(0, weight=1)

        # ───── TREE
        self.tree_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=C["bg_panel"],
            corner_radius=12
        )
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # ───── PREVIEW
        right = ctk.CTkFrame(container, fg_color=C["bg_panel"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.preview_title = ctk.CTkLabel(
            right,
            text="📄 Preview",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=C["text_primary"]
        )
        self.preview_title.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.preview_box = ctk.CTkTextbox(right)
        self.preview_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.preview_box.insert("0.0", "Selecciona un archivo")

        self._render_tree()

    # ───────────────── TREE ─────────────────
    def _render_tree(self):
        for w in self.tree_frame.winfo_children():
            w.destroy()

        path = self.state.project_path
        if not path:
            return

        self._create_item(self.tree_frame, path, os.path.basename(path), 0, True)

    def _create_item(self, parent, path, name, level, is_dir):
        C = self.colors

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")

        indent = level * 20

        container = ctk.CTkFrame(row, fg_color="transparent")
        container.pack(fill="x", padx=(indent, 0))

        arrow = "▼" if path in self.expanded else "▶" if is_dir else " "
        icon = "📂" if path in self.expanded else "📁" if is_dir else "📄"

        line = ctk.CTkFrame(container, fg_color="transparent")
        line.pack(fill="x")

        name_label = ctk.CTkLabel(
            line,
            text=f"{arrow} {icon} {name}",
            anchor="w",
            cursor="hand2",
            text_color=C["accent"] if is_dir else C["text_primary"],
        )
        name_label.pack(side="left", fill="x", expand=True)

        if is_dir and path not in self.expanded:
            hint_label = ctk.CTkLabel(
                line,
                text="  (click para expandir)",
                font=ctk.CTkFont(size=11),
                text_color=C["text_muted"]
            )
            hint_label.pack(side="left")

        def _hover_in(e): row.configure(fg_color=C["bg_hover"])
        def _hover_out(e): row.configure(fg_color="transparent")

        row.bind("<Enter>", _hover_in)
        row.bind("<Leave>", _hover_out)

        if is_dir:
            name_label.bind("<Button-1>", lambda e, p=path: self._toggle(p))
        else:
            name_label.bind("<Button-1>", lambda e, p=path: self.open_file(p))

        if is_dir and path in self.expanded:
            self._render_children(parent, path, level + 1)

    # ───────────────── PREVIEW ─────────────────
    def open_file(self, path, highlight_lines=None):
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            self.preview_box.delete("0.0", "end")

            for i, content in enumerate(lines, start=1):
                self.preview_box.insert("end", f"{i:4} | {content}")

            self.preview_title.configure(text=f"📄 {os.path.basename(path)}")

            # limpiar tags
            self.preview_box.tag_remove("critical", "0.0", "end")
            self.preview_box.tag_remove("warning", "0.0", "end")
            self.preview_box.tag_remove("info", "0.0", "end")

            # highlight (si viene del analyzer)
            if highlight_lines:
                for ln, level in highlight_lines:
                    if ln > 0:
                        self.preview_box.tag_add(level, f"{ln}.0", f"{ln}.end")

                self.preview_box.see(f"{highlight_lines[0][0]}.0")

            # colores
            self.preview_box.tag_config("critical", background="#5A1E1E")
            self.preview_box.tag_config("warning", background="#5A4B1E")
            self.preview_box.tag_config("info", background="#1E3A5A")

        except Exception as e:
            self.preview_box.delete("0.0", "end")
            self.preview_box.insert("0.0", str(e))


    def _render_children(self, parent, path, level):
        try:
            entries = sorted(
                os.scandir(path),
                key=lambda e: (not e.is_dir(), e.name.lower())
            )
        except Exception:
            return

        for entry in entries:
            if entry.name in IGNORE_DIRS or entry.name.startswith("."):
                continue

            self._create_item(parent, entry.path, entry.name, level, entry.is_dir())

    def _toggle(self, path):
        if path in self.expanded:
            self.expanded.remove(path)
        else:
            self.expanded.add(path)

        self._render_tree()

    # ───────────────── EXPORT ─────────────────
    def export_tree_pdf(self):
        path = self.state.project_path

        if not path:
            messagebox.showwarning("Sin proyecto", "Selecciona una carpeta primero.")
            return

        try:
            file = export_tree_to_pdf(path)

            if file:
                messagebox.showinfo("✅ Exportado", f"PDF guardado en:\n{file}")
            else:
                messagebox.showwarning("Cancelado", "No se seleccionó ubicación.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ───────────────── EVENTOS ─────────────────
    def _on_tree_update(self, event, data):
        if event in ("folder_selected", "analysis_done", "reset"):
            self.after(0, self._render_tree)