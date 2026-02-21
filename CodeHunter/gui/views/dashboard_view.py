"""
CodeHunter GUI - Vista Dashboard
Gauge circular de salud + contadores + exportar PDF.
"""

import math
import customtkinter as ctk
from tkinter import filedialog, messagebox
from gui.utils import get_level as _level, get_attr as _attr
from CodeHunter.infrastructure.pdf_exporter import export_report_to_pdf


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.state  = state
        self.colors = colors
        self._build_dashboard()
        self.state.subscribe(self._on_analysis_update)

    def _build_dashboard(self):
        C = self.colors

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(side="left")

        ctk.CTkLabel(title_row, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C["text_primary"],
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(title_row, text="  SIN ANALIZAR  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C["bg_card"], text_color=C["text_muted"], corner_radius=6,
        )
        self.status_badge.pack(side="left", padx=16)

        self.export_btn = ctk.CTkButton(header,
            text="📄  Exportar PDF",
            font=ctk.CTkFont(size=12, weight="bold"), height=36,
            fg_color=C["bg_card"], hover_color=C["bg_hover"],
            text_color=C["accent"], corner_radius=8,
            border_width=1, border_color=C["border"],
            command=self._export_pdf,
        )
        self.export_btn.pack(side="right")

        # ── Gauge + contadores ────────────────────────────────────────────────
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=1, column=0, padx=30, pady=20, sticky="ew")
        top_row.grid_columnconfigure(1, weight=1)

        gauge_card = ctk.CTkFrame(top_row, fg_color=C["bg_card"], corner_radius=12)
        gauge_card.grid(row=0, column=0, padx=(0, 16), pady=0, sticky="ns")

        ctk.CTkLabel(gauge_card, text="Health Score",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=C["text_muted"],
        ).pack(pady=(16, 4))

        self.gauge_canvas = ctk.CTkCanvas(gauge_card, width=200, height=200,
            bg=C["bg_card"], highlightthickness=0)
        self.gauge_canvas.pack(padx=20, pady=4)

        self.score_label = ctk.CTkLabel(gauge_card, text="—",
            font=ctk.CTkFont(size=36, weight="bold"), text_color=C["text_primary"])
        self.score_label.pack(pady=(0, 16))
        self._draw_gauge(0)

        counters_col = ctk.CTkFrame(top_row, fg_color="transparent")
        counters_col.grid(row=0, column=1, sticky="nsew")
        counters_col.grid_rowconfigure((0, 1, 2), weight=1)

        self.counter_critical = self._counter_card(counters_col, "CRÍTICOS", "0", C["accent_red"],    row=0)
        self.counter_warning  = self._counter_card(counters_col, "WARNINGS", "0", C["accent_yellow"], row=1)
        self.counter_info     = self._counter_card(counters_col, "INFO",     "0", C["accent"],        row=2)

        # ── Hallazgos recientes ───────────────────────────────────────────────
        ctk.CTkLabel(self, text="Hallazgos recientes",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text_primary"],
        ).grid(row=2, column=0, padx=30, pady=(0, 8), sticky="w")

        self.recent_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg_dark"], corner_radius=0)
        self.recent_frame.grid(row=3, column=0, padx=30, pady=(0, 24), sticky="nsew")

        self._no_data_label = ctk.CTkLabel(self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"])
        self._no_data_label.pack(pady=40)

    def _counter_card(self, parent, label, value, color, row):
        c = ctk.CTkFrame(parent, fg_color=self.colors["bg_card"], corner_radius=12)
        c.grid(row=row, column=0, pady=6, sticky="ew")
        parent.grid_columnconfigure(0, weight=1)
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)
        ind = ctk.CTkFrame(inner, width=4, height=40, fg_color=color, corner_radius=2)
        ind.pack(side="left", padx=(0, 14))
        ind.pack_propagate(False)
        val_lbl = ctk.CTkLabel(inner, text=value,
            font=ctk.CTkFont(size=28, weight="bold"), text_color=color)
        val_lbl.pack(side="left")
        ctk.CTkLabel(inner, text=label,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_muted"],
        ).pack(side="left", padx=12, anchor="s", pady=(0, 4))
        return val_lbl

    def _draw_gauge(self, score: float):
        canvas = self.gauge_canvas
        canvas.delete("all")
        C = self.colors
        cx, cy, r, thickness = 100, 100, 75, 14
        self._arc(canvas, cx, cy, r, thickness, 135, 270, C["bg_hover"])
        color = C["accent_green"] if score >= 80 else C["accent_yellow"] if score >= 50 else C["accent_red"]
        extent = (score / 100) * 270
        if extent > 0:
            self._arc(canvas, cx, cy, r, thickness, 135, extent, color)
            angle_rad = math.radians(135 + extent)
            px = cx + r * math.cos(angle_rad)
            py = cy + r * math.sin(angle_rad)
            canvas.create_oval(px-6, py-6, px+6, py+6, fill=color, outline="")

    def _arc(self, canvas, cx, cy, r, thickness, start, extent, color):
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
            start=-start, extent=-extent, outline=color, width=thickness, style="arc")

    def _on_analysis_update(self, event, data):
        if event == "analysis_started": self.after(0, self._show_loading)
        elif event == "analysis_done":  self.after(0, self._refresh)
        elif event == "reset":          self.after(0, self._clear)

    def _show_loading(self):
        self.status_badge.configure(text="  ANALIZANDO...  ",
            fg_color=self.colors["accent"], text_color="#FFFFFF")

    def _refresh(self):
        C     = self.colors
        score = self.state.health_score
        finds = self.state.findings

        self._draw_gauge(score)
        self.score_label.configure(text=f"{score:.0f}")

        if score >= 80:   badge_color, badge_text = C["accent_green"],  "  HEALTHY  "
        elif score >= 50: badge_color, badge_text = C["accent_yellow"], "  WARNING  "
        else:             badge_color, badge_text = C["accent_red"],    "  CRITICAL  "
        self.status_badge.configure(text=badge_text, fg_color=badge_color, text_color="#0D1117")

        def count(level): return sum(1 for f in finds if _level(f) == level)
        self.counter_critical.configure(text=str(count("critical")))
        self.counter_warning.configure(text=str(count("warning")))
        self.counter_info.configure(text=str(count("info")))

        for w in self.recent_frame.winfo_children():
            w.destroy()

        level_colors = {"critical": C["accent_red"], "warning": C["accent_yellow"], "info": C["accent"]}

        if not finds:
            ctk.CTkLabel(self.recent_frame,
                text="✅  No se detectaron problemas en el proyecto.",
                font=ctk.CTkFont(size=13), text_color=C["accent_green"],
            ).pack(pady=40)
            return

        for finding in finds[:10]:
            row = ctk.CTkFrame(self.recent_frame, fg_color=C["bg_card"], corner_radius=8)
            row.pack(fill="x", pady=3)
            level = _level(finding)
            color = level_colors.get(level, C["text_muted"])

            ctk.CTkLabel(row, text=f"  {level.upper():8}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=color,
                width=90, anchor="w",
            ).pack(side="left", padx=(12, 0), pady=8)

            ctk.CTkLabel(row, text=str(_attr(finding, "message")),
                font=ctk.CTkFont(size=12), text_color=C["text_primary"], anchor="w",
            ).pack(side="left", padx=8, pady=8)

            file_info = str(_attr(finding, "file"))
            line_info = _attr(finding, "line", 0)
            if file_info:
                ctk.CTkLabel(row,
                    text=f"{file_info}:{line_info}" if line_info else file_info,
                    font=ctk.CTkFont(size=11), text_color=C["text_muted"],
                ).pack(side="right", padx=12, pady=8)

    def _export_pdf(self):
        if not self.state.findings and self.state.health_score == 0.0:
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
            finds    = self.state.findings
            score    = self.state.health_score
            critical = sum(1 for f in finds if _level(f) == "critical")
            warnings = sum(1 for f in finds if _level(f) == "warning")
            profile_description = (
                f"Proyecto: {self.state.project_path}\n"
                f"Total hallazgos: {len(finds)}"
            )
            analysis_data = {
                "score":    score,
                "critical": critical,
                "warnings": warnings,
                "findings": finds,
            }
            output_path = export_report_to_pdf(
                self.state.project_path,
                profile_description,
                analysis_data,
            )
            messagebox.showinfo("✅ Exportado", f"PDF guardado en:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    def _clear(self):
        self._draw_gauge(0)
        self.score_label.configure(text="—")
        self.status_badge.configure(text="  SIN ANALIZAR  ",
            fg_color=self.colors["bg_card"], text_color=self.colors["text_muted"])
        self.counter_critical.configure(text="0")
        self.counter_warning.configure(text="0")
        self.counter_info.configure(text="0")
        for w in self.recent_frame.winfo_children():
            w.destroy()
        self._no_data_label = ctk.CTkLabel(self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"])
        self._no_data_label.pack(pady=40)
