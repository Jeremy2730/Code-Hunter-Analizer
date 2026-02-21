"""
CodeHunter GUI - Vista Hallazgos
Lista filtrable de todos los problemas detectados.
"""

import customtkinter as ctk
from gui.utils import get_level as _level, get_attr as _attr


class FindingsView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.state   = state
        self.colors  = colors
        self._filter = "all"
        self._build_findings()
        self.state.subscribe(self._on_findings_update)
        # ── Se actualiza automáticamente cada vez que se navega a esta vista ──
        self.bind("<Map>", lambda e: self._render_findings())

    def _build_findings(self):
        C = self.colors

        # ── Título de la vista ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")

        ctk.CTkLabel(header, text="Hallazgos",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C["text_primary"],
        ).pack(side="left")

        # ── Botones de filtro por nivel ───────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, padx=30, pady=16, sticky="w")

        self._filter_btns = {}
        filters = [
            ("all",      "Todos",    C["text_primary"]),
            ("critical", "Críticos", C["accent_red"]),
            ("warning",  "Warnings", C["accent_yellow"]),
            ("info",     "Info",     C["accent"]),
        ]
        for fid, label, color in filters:
            btn = ctk.CTkButton(filter_bar, text=label,
                font=ctk.CTkFont(size=12), height=30, width=90,
                # El filtro activo se resalta en azul
                fg_color=C["accent"] if fid == "all" else C["bg_card"],
                hover_color=C["bg_hover"],
                text_color="#FFFFFF" if fid == "all" else color,
                corner_radius=6,
                command=lambda f=fid: self._set_filter(f),
            )
            btn.pack(side="left", padx=4)
            self._filter_btns[fid] = btn

        # ── Lista scrolleable de hallazgos ────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["bg_dark"], corner_radius=0
        )
        self.list_frame.grid(row=2, column=0, padx=30, pady=(0, 24), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        # Mensaje inicial antes de ejecutar análisis
        ctk.CTkLabel(self.list_frame,
            text="Ejecuta un diagnóstico para ver los hallazgos.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"],
        ).pack(pady=40)

    def _set_filter(self, filter_id: str):
        C = self.colors
        self._filter = filter_id

        # ── Resalta el botón activo y apaga los demás ─────────────────────────
        level_colors = {
            "all":      C["text_primary"],
            "critical": C["accent_red"],
            "warning":  C["accent_yellow"],
            "info":     C["accent"],
        }
        for fid, btn in self._filter_btns.items():
            if fid == filter_id:
                btn.configure(fg_color=C["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=C["bg_card"], text_color=level_colors.get(fid, C["text_muted"]))

        self._render_findings()

    def _render_findings(self):
        # ── Limpia la lista antes de redibujar ────────────────────────────────
        for w in self.list_frame.winfo_children():
            w.destroy()

        C      = self.colors
        finds  = self.state.findings
        status = self.state.status

        # ── Filtra según el botón activo ──────────────────────────────────────
        filtered = (
            finds if self._filter == "all"
            else [f for f in finds if _level(f) == self._filter]
        )

        # ── Mensaje si no hay hallazgos ───────────────────────────────────────
        if not filtered:
            if status != "DONE":
                # Aún no se ejecutó ningún análisis
                msg, color = "Ejecuta un diagnóstico para ver los hallazgos.", C["text_muted"]
            elif self._filter == "all":
                # Se ejecutó y el proyecto está limpio
                msg, color = "✅  No se detectaron problemas en el proyecto.", C["accent_green"]
            else:
                # Se ejecutó pero no hay de este tipo específico
                msg, color = f"No hay hallazgos de tipo '{self._filter}'.", C["text_muted"]

            ctk.CTkLabel(self.list_frame, text=msg,
                font=ctk.CTkFont(size=13), text_color=color,
            ).pack(pady=40)
            return

        # ── Metadatos de cada nivel (ícono, color, etiqueta) ──────────────────
        level_meta = {
            "critical": ("🔴", C["accent_red"],    "CRÍTICO"),
            "warning":  ("🟡", C["accent_yellow"], "WARNING"),
            "info":     ("🔵", C["accent"],        "INFO"),
        }

        for finding in filtered:
            level = _level(finding)
            icon, color, label = level_meta.get(level, ("⚪", C["text_muted"], "INFO"))

            # ── Card compacta: UNA sola fila (nivel + mensaje juntos) ─────────
            # Antes eran 2 filas (nivel arriba, mensaje abajo) → mucho alto
            # Ahora todo en fila 0 → card de altura mínima
            # Card estilo dashboard - 2 filas con padding moderado
            row = ctk.CTkFrame(self.list_frame, fg_color=C["bg_card"], corner_radius=8)
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)

            indicator = ctk.CTkFrame(row, width=4, fg_color=color, corner_radius=2)
            indicator.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 12))
            indicator.grid_propagate(False)

            # Fila 1 - nivel
            ctk.CTkLabel(row,
                text=f"{icon} {label}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=color,
            ).grid(row=0, column=1, pady=(8, 2), sticky="w")

            # Fila 2 - mensaje
            ctk.CTkLabel(row,
                text=str(_attr(finding, "message")),
                font=ctk.CTkFont(size=12), text_color=C["text_primary"],
                anchor="w", wraplength=580,
            ).grid(row=1, column=1, pady=(0, 8), sticky="w")

            # Archivo y línea a la derecha
            file_info = str(_attr(finding, "file"))
            line_info = _attr(finding, "line", 0)
            if file_info:
                location = f"📄 {file_info}" + (f" : {line_info}" if line_info else "")
                ctk.CTkLabel(row, text=location,
                    font=ctk.CTkFont(size=10), text_color=C["text_muted"],
                ).grid(row=0, column=2, rowspan=2, padx=12, pady=8, sticky="e")

    def _on_findings_update(self, event, data):
        # ── Redibuja cuando llega un nuevo análisis o se resetea ──────────────
        if event in ("analysis_done", "reset"):
            self.after(0, self._render_findings)
