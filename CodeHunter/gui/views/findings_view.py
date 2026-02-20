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
        
        self.bind("<Map>", lambda e: self._render_findings())

    def _build_findings(self):
        C = self.colors

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")

        ctk.CTkLabel(header, text="Hallazgos",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C["text_primary"],
        ).pack(side="left")

        # ── Filtros ───────────────────────────────────────────────────────────
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
                fg_color=C["accent"] if fid == "all" else C["bg_card"],
                hover_color=C["bg_hover"],
                text_color="#FFFFFF" if fid == "all" else color,
                corner_radius=6,
                command=lambda f=fid: self._set_filter(f),
            )
            btn.pack(side="left", padx=4)
            self._filter_btns[fid] = btn

        # ── Lista ─────────────────────────────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg_dark"], corner_radius=0)
        self.list_frame.grid(row=2, column=0, padx=30, pady=(0, 24), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.list_frame,
            text="Ejecuta un diagnóstico para ver los hallazgos.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"],
        ).pack(pady=40)

    def _set_filter(self, filter_id: str):
        C = self.colors
        self._filter = filter_id
        level_colors = {"all": C["text_primary"], "critical": C["accent_red"],
                        "warning": C["accent_yellow"], "info": C["accent"]}
        for fid, btn in self._filter_btns.items():
            if fid == filter_id:
                btn.configure(fg_color=C["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=C["bg_card"], text_color=level_colors.get(fid, C["text_muted"]))
        self._render_findings()

    def _render_findings(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        C        = self.colors
        finds    = self.state.findings
        filtered = finds if self._filter == "all" else [f for f in finds if _level(f) == self._filter]

        if not filtered:
            if not finds:
                msg  = "Ejecuta un diagnóstico para ver los hallazgos."
                color = C["text_muted"]
            elif self._filter == "all":
                msg  = "✅  No se detectaron problemas en el proyecto."
                color = C["accent_green"]
            else:
                msg  = f"No hay hallazgos de tipo '{self._filter}' en este proyecto."
                color = C["text_muted"]

            ctk.CTkLabel(self.list_frame,
                text=msg, font=ctk.CTkFont(size=36), text_color=color,
            ).pack(pady=40)
            return

        level_meta = {
            "critical": ("🔴", C["accent_red"],    "CRÍTICO"),
            "warning":  ("🟡", C["accent_yellow"], "WARNING"),
            "info":     ("🔵", C["accent"],        "INFO"),
        }

        for finding in filtered:
            level = _level(finding)
            icon, color, label = level_meta.get(level, ("⚪", C["text_muted"], "INFO"))

            row = ctk.CTkFrame(self.list_frame, fg_color=C["bg_card"], corner_radius=10)
            row.pack(fill="x", pady=5)
            row.grid_columnconfigure(1, weight=1)

            indicator = ctk.CTkFrame(row, width=4, fg_color=color, corner_radius=2)
            indicator.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 12))
            indicator.grid_propagate(False)

            ctk.CTkLabel(row, text=f"{icon} {label}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=color,
            ).grid(row=0, column=1, pady=(12, 2), sticky="w")

            ctk.CTkLabel(row, text=str(_attr(finding, "message")),
                font=ctk.CTkFont(size=13), text_color=C["text_primary"],
                anchor="w", wraplength=600,
            ).grid(row=1, column=1, pady=(0, 12), sticky="w")

            file_info = str(_attr(finding, "file"))
            line_info = _attr(finding, "line", 0)
            if file_info:
                location = f"📄 {file_info}" + (f"  :  línea {line_info}" if line_info else "")
                ctk.CTkLabel(row, text=location,
                    font=ctk.CTkFont(size=11), text_color=C["text_muted"],
                ).grid(row=0, column=2, rowspan=2, padx=16, pady=12, sticky="e")

    def _on_findings_update(self, event, data):
        if event in ("analysis_done", "reset"):
            self.after(0, self._render_findings)
