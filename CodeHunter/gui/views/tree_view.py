"""
TreeView - Explorador visual del proyecto (tipo VSCode)

Sirve para:
- Mostrar carpetas y archivos
- Navegar (expandir/colapsar)
- Previsualizar archivos (texto o imagen)
- Exportar estructura a PDF

Vista previa:
- TEXTO → CTkTextbox
- IMAGEN → Canvas + zoom + scroll
"""

import os
import customtkinter as ctk
from tkinter import messagebox
from CodeHunter.utils.project_walker import IGNORE_DIRS
from CodeHunter.infrastructure.tree_pdf_exporter import export_tree_to_pdf
from PIL import Image, ImageTk

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


class TreeView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)

        self.state = state
        self.colors = colors
        self.expanded = set()

        # layout base
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self.state.subscribe(self._on_tree_update)

        self.level_colors = [
            "#58A6FF",
            "#7EE787",
            "#F2CC60",
            "#FF7B72",
            "#D2A8FF",
        ]

    # =========================================================
    # UI PRINCIPAL
    # =========================================================
    def _build_ui(self):
        C = self.colors

        # TOP BAR
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(5, 0))

        ctk.CTkButton(
            top_bar,
            text="🌳 Exportar Árbol",
            command=self.export_tree_pdf
        ).pack(side="left")

        # CONTENEDOR
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=7)
        container.grid_rowconfigure(0, weight=1)

        # TREE
        self.tree_frame = ctk.CTkScrollableFrame(container)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # PREVIEW
        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.preview_title = ctk.CTkLabel(right, text="📄 Preview")
        self.preview_title.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.preview_container = ctk.CTkFrame(right)
        self.preview_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # CANVAS (IMÁGENES)
        self.canvas = ctk.CTkCanvas(self.preview_container)
        self.canvas.pack(fill="both", expand=True)

        self.scroll_y = ctk.CTkScrollbar(
            self.preview_container, orientation="vertical", command=self.canvas.yview
        )
        self.scroll_y.pack(side="right", fill="y")

        self.scroll_x = ctk.CTkScrollbar(
            self.preview_container, orientation="horizontal", command=self.canvas.xview
        )
        self.scroll_x.pack(side="bottom", fill="x")

        self.canvas.configure(
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )

        # TEXTBOX (TEXTO)
        self.preview_box = ctk.CTkTextbox(self.preview_container)
        self.preview_box.place(relwidth=1, relheight=1)
        self.preview_box.lower()

        self.text_scroll = ctk.CTkScrollbar(self.preview_container, command=self.preview_box.yview)
        self.preview_box.configure(yscrollcommand=self.text_scroll.set)

        # estado imagen
        self.zoom = 1.0
        self.original_image = None

        self._render_tree()

    # =========================================================
    # TREE
    # =========================================================
    def _render_tree(self):
        for w in self.tree_frame.winfo_children():
            w.destroy()

        if not self.state.project_path:
            return

        self._create_item(self.tree_frame, self.state.project_path,
                          os.path.basename(self.state.project_path), 0, True)

    def _create_item(self, parent, path, name, level, is_dir):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x")

        container = ctk.CTkFrame(row)
        container.pack(fill="x", padx=(level * 20, 0))

        arrow = "▼" if path in self.expanded else "▶" if is_dir else " "
        icon = "📂" if path in self.expanded else "📁" if is_dir else "📄"

        label = ctk.CTkLabel(
            container,
            text=f"{arrow} {icon} {name}",
            anchor="w",
            cursor="hand2"
        )
        label.pack(fill="x")

        if is_dir:
            label.bind("<Button-1>", lambda e: self._toggle(path))
        else:
            label.bind("<Button-1>", lambda e: self.open_file(path))

        if is_dir and path in self.expanded:
            for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name in IGNORE_DIRS or entry.name.startswith("."):
                    continue
                self._create_item(parent, entry.path, entry.name, level + 1, entry.is_dir())

    def _toggle(self, path):
        if path in self.expanded:
            self.expanded.remove(path)
        else:
            self.expanded.add(path)
        self._render_tree()

    # =========================================================
    # PREVIEW PRINCIPAL
    # =========================================================
    def open_file(self, path):
        ext = os.path.splitext(path)[1].lower()

        self._reset_preview()

        if ext in IMAGE_EXTENSIONS:
            self._show_image_preview(path)
        else:
            self._show_text_preview(path)

    # =========================================================
    # RESET UI (clave para evitar bugs)
    # =========================================================
    def _reset_preview(self):
        self.canvas.delete("all")
        self.canvas.unbind("<MouseWheel>")

        self.preview_box.configure(state="normal")
        self.preview_box.delete("0.0", "end")
        self.preview_box.lower()

        self.text_scroll.place_forget()
        self.scroll_x.pack_forget()

    # =========================================================
    # TEXTO
    # =========================================================
    def _show_text_preview(self, path):
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            self.preview_title.configure(text=f"📄 {os.path.basename(path)}")

            self.preview_box.lift()
            self.text_scroll.place(relx=1, rely=0, relheight=1, anchor="ne")

            for i, line in enumerate(content.splitlines(), 1):
                self.preview_box.insert("end", f"{i:4} | {line}\n")

            self.preview_box.configure(state="disabled")

        except Exception as e:
            self.canvas.create_text(10, 10, anchor="nw", text=str(e))

    # =========================================================
    # IMAGEN
    # =========================================================
    def _show_image_preview(self, path):
        try:
            self.scroll_x.pack(side="bottom", fill="x")

            self.preview_title.configure(text=f"🖼️ {os.path.basename(path)}")

            self.original_image = Image.open(path)
            self.zoom = 1.0

            self._render_image()

            self.canvas.bind("<MouseWheel>", self._zoom_image)

        except Exception as e:
            self.canvas.create_text(10, 10, anchor="nw", text=str(e))

    def _render_image(self):
        img = self.original_image.copy()
        w, h = img.size
        img = img.resize((int(w * self.zoom), int(h * self.zoom)))

        self.tk_image = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _zoom_image(self, event):
        self.zoom *= 1.1 if event.delta > 0 else 0.9
        self.zoom = max(0.2, min(self.zoom, 5))
        self._render_image()

    # =========================================================
    # EXPORT
    # =========================================================
    def export_tree_pdf(self):
        if not self.state.project_path:
            messagebox.showwarning("Sin proyecto", "Selecciona una carpeta primero.")
            return

        try:
            file = export_tree_to_pdf(self.state.project_path)
            if file:
                messagebox.showinfo("Exportado", file)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # =========================================================
    # EVENTOS
    # =========================================================
    def _on_tree_update(self, event, data):
        if event in ("folder_selected", "analysis_done", "reset"):
            self.after(0, self._render_tree)