"""
CodeHunter GUI - Vista Hallazgos
Lista filtrable de todos los problemas detectados con botón de exportar PDF.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox


class FindingsView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.state   = state
        self.colors  = colors
        self._filter = "all"

        self._build()
        self.state.subscribe(self._on_state_change)

    # ──────────────────────────────────────────────────────────────────────────
    def _build(self):
        C = self.colors

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Hallazgos",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=C["text_primary"],
        ).grid(row=0, column=0, sticky="w")

        # Botón exportar PDF
        self.export_btn = ctk.CTkButton(
            header,
            text="📄  Exportar PDF",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color=C["bg_card"],
            hover_color=C["bg_hover"],
            text_color=C["accent"],
            corner_radius=8,
            border_width=1,
            border_color=C["border"],
            command=self._export_pdf,
        )
        self.export_btn.grid(row=0, column=1, sticky="e")

        # ── Filtros ───────────────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.grid(row=1, column=0, padx=30, pady=16, sticky="w")

        self._filter_btns = {}
        filters = [
            ("all",      "Todos",     C["text_primary"]),
            ("critical", "Críticos",  C["accent_red"]),
            ("warning",  "Warnings",  C["accent_yellow"]),
            ("info",     "Info",      C["accent"]),
        ]
        for fid, label, color in filters:
            btn = ctk.CTkButton(
                filter_bar,
                text=label,
                font=ctk.CTkFont(size=12),
                height=30,
                width=90,
                fg_color=C["bg_card"] if fid != "all" else C["accent"],
                hover_color=C["bg_hover"],
                text_color="#FFFFFF" if fid == "all" else color,
                corner_radius=6,
                command=lambda f=fid: self._set_filter(f),
            )
            btn.pack(side="left", padx=4)
            self._filter_btns[fid] = btn

        # ── Lista ─────────────────────────────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["bg_dark"], corner_radius=0
        )
        self.list_frame.grid(row=2, column=0, padx=30, pady=(0, 24), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self.list_frame,
            text="Ejecuta un diagnóstico para ver los hallazgos.",
            font=ctk.CTkFont(size=13),
            text_color=C["text_muted"],
        )
        self._empty_label.pack(pady=40)

    # ──────────────────────────────────────────────────────────────────────────
    def _set_filter(self, filter_id: str):
        C = self.colors
        self._filter = filter_id

        for fid, btn in self._filter_btns.items():
            if fid == filter_id:
                btn.configure(fg_color=C["accent"], text_color="#FFFFFF")
            else:
                level_colors = {
                    "all":      C["text_primary"],
                    "critical": C["accent_red"],
                    "warning":  C["accent_yellow"],
                    "info":     C["accent"],
                }
                btn.configure(
                    fg_color=C["bg_card"],
                    text_color=level_colors.get(fid, C["text_muted"])
                )

        self._render_findings()

    def _render_findings(self):
        # Limpiar lista
        for w in self.list_frame.winfo_children():
            w.destroy()

        C       = self.colors
        finds   = self.state.findings
        filtered = (
            finds if self._filter == "all"
            else [f for f in finds if f.get("level") == self._filter]
        )

        if not filtered:
            ctk.CTkLabel(
                self.list_frame,
                text="No hay hallazgos en esta categoría." if finds else
                     "Ejecuta un diagnóstico para ver los hallazgos.",
                font=ctk.CTkFont(size=13),
                text_color=C["text_muted"],
            ).pack(pady=40)
            return

        level_meta = {
            "critical": ("🔴", C["accent_red"],    "CRÍTICO"),
            "warning":  ("🟡", C["accent_yellow"], "WARNING"),
            "info":     ("🔵", C["accent"],        "INFO"),
        }

        for i, finding in enumerate(filtered):
            level  = finding.get("level", "info")
            icon, color, label = level_meta.get(level, ("⚪", C["text_muted"], "INFO"))

            row = ctk.CTkFrame(
                self.list_frame, fg_color=C["bg_card"], corner_radius=10
            )
            row.pack(fill="x", pady=5)
            row.grid_columnconfigure(1, weight=1)

            # Indicador lateral de color
            indicator = ctk.CTkFrame(row, width=4, fg_color=color, corner_radius=2)
            indicator.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 12), pady=0)
            indicator.grid_propagate(False)

            # Nivel + mensaje
            ctk.CTkLabel(
                row,
                text=f"{icon} {label}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
            ).grid(row=0, column=1, padx=0, pady=(12, 2), sticky="w")

            ctk.CTkLabel(
                row,
                text=finding.get("message", ""),
                font=ctk.CTkFont(size=13),
                text_color=C["text_primary"],
                anchor="w",
                wraplength=600,
            ).grid(row=1, column=1, padx=0, pady=(0, 12), sticky="w")

            # Archivo y línea
            file_info = finding.get("file", "")
            line_info = finding.get("line", 0)
            if file_info:
                location = f"📄 {file_info}" + (f"  :  línea {line_info}" if line_info else "")
                ctk.CTkLabel(
                    row,
                    text=location,
                    font=ctk.CTkFont(size=11),
                    text_color=C["text_muted"],
                ).grid(row=0, column=2, rowspan=2, padx=16, pady=12, sticky="e")

    def _export_pdf(self):
        if not self.state.findings:
            messagebox.showwarning("Sin datos", "Ejecuta un análisis antes de exportar.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="codehunter_report.pdf",
            title="Guardar reporte PDF",
        )
        if not save_path:
            return

        try:
            from CodeHunter.infrastructure.pdf_exporter import export_report_to_pdf
            export_report_to_pdf(self.state.diagnosis_data, save_path)
            messagebox.showinfo("Exportado", f"Reporte guardado en:\n{save_path}")
        except ImportError:
            messagebox.showinfo(
                "Demo",
                f"Backend no disponible.\nEn producción el PDF se guardaría en:\n{save_path}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    # ──────────────────────────────────────────────────────────────────────────
    def _on_state_change(self, event, data):
        if event in ("analysis_done", "reset"):
            self.after(0, self._render_findings)
