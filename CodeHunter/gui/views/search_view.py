"""
CodeHunter GUI - Vista Búsqueda
Buscador de texto en el código del proyecto.
"""

import os
import threading
import customtkinter as ctk


class SearchView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.state  = state
        self.colors = colors

        self._build()

    def _build(self):
        C = self.colors

        ctk.CTkLabel(
            self, text="Buscar en el código",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=C["text_primary"],
        ).grid(row=0, column=0, padx=30, pady=(28, 16), sticky="w")

        # ── Barra de búsqueda ─────────────────────────────────────────────────
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.grid(row=1, column=0, padx=30, pady=(0, 16), sticky="ew")
        search_bar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="🔍  Busca funciones, variables, imports...",
            font=ctk.CTkFont(size=13),
            height=42,
            fg_color=C["bg_card"],
            border_color=C["border"],
            text_color=C["text_primary"],
            corner_radius=8,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        ctk.CTkButton(
            search_bar,
            text="Buscar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            width=100,
            fg_color=C["accent"],
            hover_color="#1F6FEB",
            corner_radius=8,
            command=self._do_search,
        ).grid(row=0, column=1)

        # ── Resultados ────────────────────────────────────────────────────────
        self.results_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["bg_dark"], corner_radius=0
        )
        self.results_frame.grid(row=2, column=0, padx=30, pady=(0, 24), sticky="nsew")

        self._hint = ctk.CTkLabel(
            self.results_frame,
            text="Escribe algo y presiona Enter o haz clic en Buscar.",
            font=ctk.CTkFont(size=13),
            text_color=C["text_muted"],
        )
        self._hint.pack(pady=40)

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        if not self.state.project_path:
            self._show_message("Selecciona un proyecto primero.")
            return

        self._show_message("🔍  Buscando...")
        threading.Thread(
            target=self._search_files, args=(query,), daemon=True
        ).start()

    def _search_files(self, query: str):
        results = []
        root = self.state.project_path
        query_lower = query.lower()

        try:
            for dirpath, _, files in os.walk(root):
                # Ignorar carpetas de dependencias
                dirpath_parts = dirpath.replace("\\", "/").split("/")
                if any(p in ("__pycache__", ".venv", "venv", ".git") for p in dirpath_parts):
                    continue

                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, encoding="utf-8", errors="ignore") as f:
                            for lineno, line in enumerate(f, 1):
                                if query_lower in line.lower():
                                    rel = os.path.relpath(fpath, root)
                                    results.append({
                                        "file":    rel,
                                        "line":    lineno,
                                        "content": line.rstrip(),
                                    })
                                    if len(results) >= 200:
                                        break
                    except Exception:
                        pass
                if len(results) >= 200:
                    break
        except Exception:
            pass

        self.after(0, lambda: self._render_results(query, results))

    def _render_results(self, query: str, results: list):
        C = self.colors
        for w in self.results_frame.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self.results_frame,
                text=f'No se encontró "{query}" en el proyecto.',
                font=ctk.CTkFont(size=13),
                text_color=C["text_muted"],
            ).pack(pady=40)
            return

        ctk.CTkLabel(
            self.results_frame,
            text=f'  {len(results)} resultado(s) para "{query}"',
            font=ctk.CTkFont(size=12),
            text_color=C["text_muted"],
        ).pack(anchor="w", pady=(4, 12))

        for r in results:
            row = ctk.CTkFrame(
                self.results_frame, fg_color=C["bg_card"], corner_radius=8
            )
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=f"📄 {r['file']}  :  línea {r['line']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=C["accent"],
                anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")

            ctk.CTkLabel(
                row,
                text=r["content"][:120],
                font=ctk.CTkFont(family="Courier New", size=12),
                text_color=C["text_primary"],
                anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

    def _show_message(self, msg: str):
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame,
            text=msg,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"],
        ).pack(pady=40)
