"""
CodeHunter GUI - Vista Dashboard
Gauge circular de salud + contadores + estado general.
"""

import math
import customtkinter as ctk


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.state  = state
        self.colors = colors

        self._build()

        # Suscribirse a cambios de estado
        self.state.subscribe(self._on_state_change)

    # ──────────────────────────────────────────────────────────────────────────
    def _build(self):
        C = self.colors

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="w")

        ctk.CTkLabel(
            header, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=C["text_primary"],
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            header, text="  SIN ANALIZAR  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C["bg_card"],
            text_color=C["text_muted"],
            corner_radius=6,
        )
        self.status_badge.pack(side="left", padx=16)

        # ── Fila superior: gauge + contadores ─────────────────────────────────
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=1, column=0, padx=30, pady=20, sticky="ew")
        top_row.grid_columnconfigure(1, weight=1)

        # Gauge
        gauge_card = card(top_row, C)
        gauge_card.grid(row=0, column=0, padx=(0, 16), pady=0, sticky="ns")

        ctk.CTkLabel(
            gauge_card, text="Health Score",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["text_muted"],
        ).pack(pady=(16, 4))

        self.gauge_canvas = ctk.CTkCanvas(
            gauge_card, width=200, height=200,
            bg=C["bg_card"], highlightthickness=0,
        )
        self.gauge_canvas.pack(padx=20, pady=4)

        self.score_label = ctk.CTkLabel(
            gauge_card, text="—",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=C["text_primary"],
        )
        self.score_label.pack(pady=(0, 16))

        self._draw_gauge(0)

        # Contadores
        counters_col = ctk.CTkFrame(top_row, fg_color="transparent")
        counters_col.grid(row=0, column=1, sticky="nsew")
        counters_col.grid_rowconfigure((0, 1, 2), weight=1)

        self.counter_critical = self._counter_card(
            counters_col, "CRÍTICOS", "0", C["accent_red"], row=0
        )
        self.counter_warning = self._counter_card(
            counters_col, "WARNINGS", "0", C["accent_yellow"], row=1
        )
        self.counter_info = self._counter_card(
            counters_col, "INFO", "0", C["accent"], row=2
        )

        # ── Fila inferior: hallazgos recientes ────────────────────────────────
        ctk.CTkLabel(
            self, text="Hallazgos recientes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C["text_primary"],
        ).grid(row=2, column=0, padx=30, pady=(0, 8), sticky="w")

        self.recent_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["bg_dark"], corner_radius=0,
        )
        self.recent_frame.grid(row=3, column=0, padx=30, pady=(0, 24), sticky="nsew")
        self.grid_rowconfigure(3, weight=1)

        self._no_data_label = ctk.CTkLabel(
            self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"],
        )
        self._no_data_label.pack(pady=40)

    # ──────────────────────────────────────────────────────────────────────────
    def _counter_card(self, parent, label, value, color, row):
        c = card(parent, self.colors)
        c.grid(row=row, column=0, pady=6, sticky="ew")
        parent.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        indicator = ctk.CTkFrame(inner, width=4, height=40, fg_color=color, corner_radius=2)
        indicator.pack(side="left", padx=(0, 14))
        indicator.pack_propagate(False)

        val_lbl = ctk.CTkLabel(
            inner, text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color,
        )
        val_lbl.pack(side="left")

        ctk.CTkLabel(
            inner, text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_muted"],
        ).pack(side="left", padx=12, anchor="s", pady=(0, 4))

        return val_lbl   # Retorna referencia para actualizar

    def _draw_gauge(self, score: float):
        """Dibuja el gauge circular con el score (0-100)."""
        canvas = self.gauge_canvas
        canvas.delete("all")
        C = self.colors

        cx, cy, r = 100, 100, 75
        thickness = 14

        # Fondo del arco
        self._arc(canvas, cx, cy, r, thickness, 135, 270, C["bg_hover"])

        # Color según score
        if score >= 80:   color = C["accent_green"]
        elif score >= 50: color = C["accent_yellow"]
        else:             color = C["accent_red"]

        # Arco de progreso
        extent = (score / 100) * 270
        if extent > 0:
            self._arc(canvas, cx, cy, r, thickness, 135, extent, color)

        # Punto final
        if score > 0:
            angle_rad = math.radians(135 + extent)
            px = cx + r * math.cos(angle_rad)
            py = cy + r * math.sin(angle_rad)
            canvas.create_oval(
                px - 6, py - 6, px + 6, py + 6,
                fill=color, outline="", tags="dot"
            )

    def _arc(self, canvas, cx, cy, r, thickness, start, extent, color):
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r
        canvas.create_arc(
            x0, y0, x1, y1,
            start=-start, extent=-extent,
            outline=color, width=thickness,
            style="arc",
        )

    # ──────────────────────────────────────────────────────────────────────────
    def _on_state_change(self, event, data):
        if event == "analysis_started":
            self.after(0, self._show_loading)
        elif event == "analysis_done":
            self.after(0, self._refresh)
        elif event == "reset":
            self.after(0, self._clear)

    def _show_loading(self):
        self.status_badge.configure(
            text="  ANALIZANDO...  ",
            fg_color=self.colors["accent"],
            text_color="#FFFFFF",
        )

    def _refresh(self):
        C      = self.colors
        score  = self.state.health_score
        finds  = self.state.findings

        # Score
        self._draw_gauge(score)
        self.score_label.configure(text=f"{score:.0f}")

        # Status badge
        if score >= 80:
            badge_color, badge_text = C["accent_green"], "  HEALTHY  "
        elif score >= 50:
            badge_color, badge_text = C["accent_yellow"], "  WARNING  "
        else:
            badge_color, badge_text = C["accent_red"], "  CRITICAL  "

        self.status_badge.configure(
            text=badge_text, fg_color=badge_color, text_color="#0D1117"
        )

        # Contadores
        def count(level): return sum(1 for f in finds if f.get("level") == level)
        self.counter_critical.configure(text=str(count("critical")))
        self.counter_warning.configure(text=str(count("warning")))
        self.counter_info.configure(text=str(count("info")))

        # Hallazgos recientes
        self._no_data_label.pack_forget()
        for w in self.recent_frame.winfo_children():
            w.destroy()

        level_colors = {
            "critical": C["accent_red"],
            "warning":  C["accent_yellow"],
            "info":     C["accent"],
        }

        for finding in finds[:10]:  # Máximo 10 en dashboard
            row = ctk.CTkFrame(self.recent_frame, fg_color=C["bg_card"], corner_radius=8)
            row.pack(fill="x", pady=4)

            level = finding.get("level", "info")
            color = level_colors.get(level, C["text_muted"])

            ctk.CTkLabel(
                row,
                text=f"  {level.upper():8}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color,
                width=90,
                anchor="w",
            ).pack(side="left", padx=(12, 0), pady=10)

            ctk.CTkLabel(
                row,
                text=finding.get("message", ""),
                font=ctk.CTkFont(size=12),
                text_color=C["text_primary"],
                anchor="w",
            ).pack(side="left", padx=8, pady=10)

            file_info = finding.get("file", "")
            line_info = finding.get("line", 0)
            if file_info:
                ctk.CTkLabel(
                    row,
                    text=f"{file_info}:{line_info}" if line_info else file_info,
                    font=ctk.CTkFont(size=11),
                    text_color=C["text_muted"],
                    anchor="e",
                ).pack(side="right", padx=16, pady=10)

    def _clear(self):
        self._draw_gauge(0)
        self.score_label.configure(text="—")
        self.status_badge.configure(
            text="  SIN ANALIZAR  ", fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"]
        )
        self.counter_critical.configure(text="0")
        self.counter_warning.configure(text="0")
        self.counter_info.configure(text="0")
        for w in self.recent_frame.winfo_children():
            w.destroy()
        self._no_data_label = ctk.CTkLabel(
            self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"],
        )
        self._no_data_label.pack(pady=40)


# ── Helper ─────────────────────────────────────────────────────────────────────
def card(parent, colors):
    return ctk.CTkFrame(parent, fg_color=colors["bg_card"], corner_radius=12)
