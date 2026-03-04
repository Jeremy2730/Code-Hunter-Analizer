"""
CodeHunter GUI - Vista Dashboard
Gauge circular de salud + contadores + descripción del proyecto + exportar PDF.
"""

import os
import json
import math
import urllib.request
import threading
import customtkinter as ctk
import time
from tkinter import filedialog, messagebox
from ..utils import get_level as _level, get_attr as _attr
from CodeHunter.infrastructure.pdf_exporter import export_report_to_pdf


def _scan_project(path):
    """Lee el proyecto y retorna estadísticas + muestra de código."""
    stats = {"files": 0, "lines": 0, "functions": 0, "classes": 0, "modules": set()}
    code_sample = []

    IGNORE = {"__pycache__", ".venv", "venv", ".git", "node_modules"}

    for dirpath, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            stats["files"] += 1
            rel = os.path.relpath(dirpath, path)
            top = rel.split(os.sep)[0]
            if top != ".":
                stats["modules"].add(top)

            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                stats["lines"] += len(lines)
                for line in lines:
                    s = line.strip()
                    if s.startswith("def "):
                        stats["functions"] += 1
                    if s.startswith("class "):
                        stats["classes"] += 1
                if len(code_sample) < 3 and len(lines) > 5:
                    code_sample.append({
                        "file": os.path.relpath(fpath, path),
                        "code": "".join(lines[:40])
                    })
            except Exception:
                pass

    stats["modules"] = len(stats["modules"])
    return stats, code_sample


def _generate_readme(project_name, stats, code_sample):
    """Llama a la API de Claude para generar descripción del proyecto."""
    try:
        sample_text = ""
        for s in code_sample:
            sample_text += f"\n--- {s['file']} ---\n{s['code'][:500]}\n"

        prompt = f"""Analiza este proyecto Python llamado "{project_name}" y escribe una descripción técnica breve en español.

Estadísticas:
- Archivos Python: {stats['files']}
- Líneas de código: {stats['lines']}
- Funciones: {stats['functions']}
- Clases: {stats['classes']}
- Módulos: {stats['modules']}

Muestra de código:
{sample_text}

Escribe en español:
1. Una descripción de 2-3 oraciones de qué hace el proyecto
2. Las tecnologías o patrones principales que detectas
3. El propósito principal del sistema

Sé conciso y técnico. Máximo 150 palabras."""

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except Exception:
        return None


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, state, colors):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.state  = state
        self.colors = colors
        self._build_dashboard()
        self.state.subscribe(self._on_analysis_update)

    # ──────────────────────────────────────────────────────────────────────────
    # BUILD — orquestador principal (ahora solo llama a sub-constructores)
    # ──────────────────────────────────────────────────────────────────────────

    def _build_dashboard(self):
        """Orquesta la construcción de la vista delegando en métodos específicos."""
        self._scroll = self._build_scroll_container()
        self._build_header(self._scroll)
        self._build_gauge_and_counters(self._scroll)
        self._build_readme_section(self._scroll)
        self._build_recent_findings(self._scroll)

    # ──────────────────────────────────────────────────────────────────────────
    # SUB-CONSTRUCTORES
    # ──────────────────────────────────────────────────────────────────────────

    def _build_scroll_container(self):
        """Crea y retorna el frame scrolleable raíz de la vista."""
        C = self.colors
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg_dark"], corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        return scroll

    def _build_header(self, parent):
        """Construye la fila de título, badge de estado y botón exportar PDF."""
        C = self.colors

        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(28, 0), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(side="left")

        ctk.CTkLabel(
            title_row, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=C["text_primary"],
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            title_row, text="  SIN ANALIZAR  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C["bg_card"], text_color=C["text_muted"], corner_radius=6,
        )
        self.status_badge.pack(side="left", padx=16)

        self.export_btn = ctk.CTkButton(
            header,
            text="📄  Exportar PDF",
            font=ctk.CTkFont(size=12, weight="bold"), height=36,
            fg_color=C["bg_card"], hover_color=C["bg_hover"],
            text_color=C["accent"], corner_radius=8,
            border_width=1, border_color=C["border"],
            command=self._export_pdf,
        )
        self.export_btn.pack(side="right")

    def _build_gauge_and_counters(self, parent):
        """Construye la tarjeta del gauge circular y las tarjetas de contadores."""
        C = self.colors

        top_row = ctk.CTkFrame(parent, fg_color="transparent")
        top_row.grid(row=1, column=0, padx=30, pady=20, sticky="ew")
        top_row.grid_columnconfigure(1, weight=1)

        self._build_gauge_card(top_row)
        self._build_counter_cards(top_row)

    def _build_gauge_card(self, parent):
        """Construye la tarjeta con el canvas del gauge y la etiqueta de score."""
        C = self.colors

        gauge_card = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=12)
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

    def _build_counter_cards(self, parent):
        """Construye las tres tarjetas de contadores (críticos, warnings, info)."""
        counters_col = ctk.CTkFrame(parent, fg_color="transparent")
        counters_col.grid(row=0, column=1, sticky="nsew")
        counters_col.grid_rowconfigure((0, 1, 2), weight=1)

        C = self.colors
        self.counter_critical = self._counter_card(counters_col, "CRÍTICOS", "0", C["accent_red"],    row=0)
        self.counter_warning  = self._counter_card(counters_col, "WARNINGS", "0", C["accent_yellow"], row=1)
        self.counter_info     = self._counter_card(counters_col, "INFO",     "0", C["accent"],        row=2)

    def _build_readme_section(self, parent):
        """Construye la sección de descripción del proyecto con chips y texto IA."""
        C = self.colors

        ctk.CTkLabel(
            parent, text="📋  Descripción del Proyecto",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C["text_primary"],
        ).grid(row=2, column=0, padx=30, pady=(0, 8), sticky="w")

        self.readme_frame = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=12)
        self.readme_frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="ew")
        self.readme_frame.grid_columnconfigure(0, weight=1)

        self._build_stats_chips(self.readme_frame)

        ctk.CTkFrame(self.readme_frame, height=1, fg_color=C["border"]
        ).grid(row=1, column=0, padx=20, pady=4, sticky="ew")

        self.readme_label = ctk.CTkLabel(
            self.readme_frame,
            text="Ejecuta el diagnóstico para generar la descripción del proyecto.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"],
            anchor="w", justify="left", wraplength=800,
        )
        self.readme_label.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="ew")

    def _build_stats_chips(self, parent):
        """Construye la fila de chips de estadísticas del proyecto."""
        self.stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        self.stats_row.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        self.stat_files   = self._stat_chip(self.stats_row, "📁", "—", "Archivos")
        self.stat_lines   = self._stat_chip(self.stats_row, "📝", "—", "Líneas")
        self.stat_funcs   = self._stat_chip(self.stats_row, "⚙",  "—", "Funciones")
        self.stat_classes = self._stat_chip(self.stats_row, "🧩", "—", "Clases")
        self.stat_modules = self._stat_chip(self.stats_row, "📦", "—", "Módulos")

    def _build_recent_findings(self, parent):
        """Construye la sección de hallazgos recientes con su mensaje vacío inicial."""
        C = self.colors

        ctk.CTkLabel(
            parent, text="Hallazgos recientes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C["text_primary"],
        ).grid(row=4, column=0, padx=30, pady=(0, 8), sticky="w")

        self.recent_frame = ctk.CTkFrame(parent, fg_color=C["bg_dark"], corner_radius=0)
        self.recent_frame.grid(row=5, column=0, padx=30, pady=(0, 24), sticky="ew")
        self.recent_frame.grid_columnconfigure(0, weight=1)

        self._no_data_label = ctk.CTkLabel(
            self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13), text_color=C["text_muted"],
        )
        self._no_data_label.pack(pady=40)

    # ──────────────────────────────────────────────────────────────────────────
    # WIDGETS REUTILIZABLES
    # ──────────────────────────────────────────────────────────────────────────

    def _stat_chip(self, parent, icon, value, label):
        """Crea un chip de estadística: ícono + número + etiqueta."""
        C = self.colors
        chip = ctk.CTkFrame(parent, fg_color=C["bg_hover"], corner_radius=8)
        chip.pack(side="left", padx=6)

        ctk.CTkLabel(chip, text=icon,
            font=ctk.CTkFont(size=16), text_color=C["accent"],
        ).pack(side="left", padx=(10, 4), pady=10)

        val_lbl = ctk.CTkLabel(chip, text=value,
            font=ctk.CTkFont(size=16, weight="bold"), text_color=C["text_primary"],
        )
        val_lbl.pack(side="left", pady=10)

        ctk.CTkLabel(chip, text=f"  {label}",
            font=ctk.CTkFont(size=11), text_color=C["text_muted"],
        ).pack(side="left", padx=(2, 12), pady=10)

        return val_lbl

    def _counter_card(self, parent, label, value, color, row):
        """Crea una tarjeta de contador con indicador de color lateral."""
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

    # ──────────────────────────────────────────────────────────────────────────
    # GAUGE — dibujo y animación
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_gauge(self, score: float):
        canvas = self.gauge_canvas
        canvas.delete("all")
        C = self.colors

        score = max(0, min(score, 100))
        cx, cy, r, thickness = 100, 100, 75, 16

        self._arc(canvas, cx, cy, r, thickness, 135, 270, C["bg_hover"])

        extent = (score / 100) * 270
        color  = self._interpolate_color(score / 100)

        if extent > 0:
            self._arc(canvas, cx, cy, r, thickness, 135, extent, color)

        angle_rad    = math.radians(135 + extent)
        needle_length = r - 12
        px = cx + needle_length * math.cos(angle_rad)
        py = cy + needle_length * math.sin(angle_rad)

        canvas.create_line(cx, cy, px, py, fill=color, width=4)
        canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="#1a1a1a", outline="")

    def animate_gauge(self, target_score, duration=800):
        self._gauge_target     = max(0, min(target_score, 100))
        self._gauge_start      = getattr(self, "_current_score", 0)
        self._gauge_start_time = time.time()
        self._gauge_duration   = duration / 1000
        self._animate_step()

    def _animate_step(self):
        elapsed = time.time() - self._gauge_start_time
        t       = min(elapsed / self._gauge_duration, 1)
        eased   = 1 - (1 - t) ** 3

        current_score        = self._gauge_start + (self._gauge_target - self._gauge_start) * eased
        self._current_score  = current_score

        self._draw_gauge(current_score)
        self.score_label.configure(text=f"{current_score:.0f}")

        if t < 1:
            self.after(16, self._animate_step)

    def _arc(self, canvas, cx, cy, r, thickness, start, extent, color):
        canvas.create_arc(
            cx-r, cy-r, cx+r, cy+r,
            start=-start, extent=-extent,
            outline=color, width=thickness, style="arc",
        )

    def _interpolate_color(self, t):
        """Interpola rojo → amarillo → verde según t (0..1)."""
        if t < 0.5:
            r, g, b = 255, int(255 * (t / 0.5)), 0
        else:
            r, g, b = int(255 * (1 - (t - 0.5) / 0.5)), 255, 0
        return f"#{r:02x}{g:02x}{b:02x}"

    # ──────────────────────────────────────────────────────────────────────────
    # EVENTOS DEL STATE
    # ──────────────────────────────────────────────────────────────────────────

    def _on_analysis_update(self, event, data):
        if event == "analysis_started":
            self.after(0, self._show_loading)
        elif event == "analysis_done":
            self.after(0, self._refresh)
        elif event == "reset":
            self.after(0, self._clear)

    def _show_loading(self):
        self.status_badge.configure(
            text="  ANALIZANDO...  ",
            fg_color=self.colors["accent"], text_color="#FFFFFF",
        )
        self.readme_label.configure(
            text="⏳  Generando descripción del proyecto...",
            text_color=self.colors["text_muted"],
        )

    def _refresh(self):
        C     = self.colors
        score = self.state.health_score
        finds = self.state.findings
        path  = self.state.project_path

        self.after(50, lambda: self.animate_gauge(score))
        self._update_status_badge(score)
        self._update_counters(finds)

        if path:
            threading.Thread(
                target=self._generate_project_info, args=(path,), daemon=True
            ).start()

        self._render_recent_findings(finds)

    def _update_status_badge(self, score):
        """Actualiza el badge de estado según el health score."""
        C = self.colors
        if score >= 80:
            badge_color, badge_text = C["accent_green"],  "  HEALTHY  "
        elif score >= 50:
            badge_color, badge_text = C["accent_yellow"], "  WARNING  "
        else:
            badge_color, badge_text = C["accent_red"],    "  CRITICAL  "
        self.status_badge.configure(
            text=badge_text, fg_color=badge_color, text_color="#0D1117"
        )

    def _update_counters(self, finds):
        """Actualiza los tres contadores de severidad."""
        def count(level):
            return sum(1 for f in finds if _level(f) == level)
        self.counter_critical.configure(text=str(count("critical")))
        self.counter_warning.configure(text=str(count("warning")))
        self.counter_info.configure(text=str(count("info")))

    def _render_recent_findings(self, finds):
        """Renderiza las filas de hallazgos recientes (máximo 10)."""
        C = self.colors
        for w in self.recent_frame.winfo_children():
            w.destroy()

        if not finds:
            ctk.CTkLabel(
                self.recent_frame,
                text="✅  No se detectaron problemas en el proyecto.",
                font=ctk.CTkFont(size=13), text_color=C["accent_green"],
            ).pack(pady=40)
            return

        level_colors = {
            "critical": C["accent_red"],
            "warning":  C["accent_yellow"],
            "info":     C["accent"],
        }

        for finding in finds[:10]:
            level = _level(finding)
            color = level_colors.get(level, C["text_muted"])
            self._render_finding_row(finding, level, color)

    def _render_finding_row(self, finding, level, color):
        """Renderiza una fila individual de hallazgo."""
        C   = self.colors
        row = ctk.CTkFrame(self.recent_frame, fg_color=C["bg_card"], corner_radius=8)
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row, text=f"  {level.upper():8}",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=color,
            width=90, anchor="w",
        ).pack(side="left", padx=(12, 0), pady=8)

        ctk.CTkLabel(
            row, text=str(_attr(finding, "message")),
            font=ctk.CTkFont(size=12), text_color=C["text_primary"], anchor="w",
        ).pack(side="left", padx=8, pady=8)

        file_info = str(_attr(finding, "file"))
        line_info = _attr(finding, "line", 0)
        if file_info:
            ctk.CTkLabel(
                row,
                text=f"{file_info}:{line_info}" if line_info else file_info,
                font=ctk.CTkFont(size=11), text_color=C["text_muted"],
            ).pack(side="right", padx=12, pady=8)

    # ──────────────────────────────────────────────────────────────────────────
    # GENERACIÓN DE INFO DEL PROYECTO (hilo secundario)
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_project_info(self, path):
        """Corre en hilo: escanea stats y llama a IA para descripción."""
        project_name = os.path.basename(path)
        stats, code_sample = _scan_project(path)

        self.after(0, lambda: self._update_stats(stats))
        self.after(0, lambda: self.readme_label.configure(
            text="🤖  Analizando código con IA...",
            text_color=self.colors["text_muted"],
        ))

        description = _generate_readme(project_name, stats, code_sample)

        if description:
            self.after(0, lambda: self.readme_label.configure(
                text=description, text_color=self.colors["text_primary"]
            ))
        else:
            basic = (
                f"Proyecto Python con {stats['files']} archivos, "
                f"{stats['lines']:,} líneas de código, "
                f"{stats['functions']} funciones y {stats['classes']} clases "
                f"distribuidas en {stats['modules']} módulos."
            )
            self.after(0, lambda: self.readme_label.configure(
                text=basic, text_color=self.colors["text_primary"]
            ))

    def _update_stats(self, stats):
        """Actualiza los chips de estadísticas en el hilo principal."""
        self.stat_files.configure(text=str(stats["files"]))
        self.stat_lines.configure(text=f"{stats['lines']:,}")
        self.stat_funcs.configure(text=str(stats["functions"]))
        self.stat_classes.configure(text=str(stats["classes"]))
        self.stat_modules.configure(text=str(stats["modules"]))

    # ──────────────────────────────────────────────────────────────────────────
    # EXPORTAR PDF
    # ──────────────────────────────────────────────────────────────────────────

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

            analysis_data = {
                "score":    score,
                "critical": critical,
                "warnings": warnings,
                "findings": finds,
            }
            output_path = export_report_to_pdf(
                self.state.project_path,
                f"Proyecto: {self.state.project_path}\nTotal hallazgos: {len(finds)}",
                analysis_data,
            )
            messagebox.showinfo("✅ Exportado", f"PDF guardado en:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    # ──────────────────────────────────────────────────────────────────────────
    # RESET / CLEAR
    # ──────────────────────────────────────────────────────────────────────────

    def _clear(self):
        self._draw_gauge(0)
        self.score_label.configure(text="—")
        self.status_badge.configure(
            text="  SIN ANALIZAR  ",
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_muted"],
        )
        self.counter_critical.configure(text="0")
        self.counter_warning.configure(text="0")
        self.counter_info.configure(text="0")
        self.stat_files.configure(text="—")
        self.stat_lines.configure(text="—")
        self.stat_funcs.configure(text="—")
        self.stat_classes.configure(text="—")
        self.stat_modules.configure(text="—")
        self.readme_label.configure(
            text="Ejecuta el diagnóstico para generar la descripción del proyecto.",
            text_color=self.colors["text_muted"],
        )
        for w in self.recent_frame.winfo_children():
            w.destroy()
        self._no_data_label = ctk.CTkLabel(
            self.recent_frame,
            text="Abre una carpeta y ejecuta el diagnóstico para ver resultados.",
            font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"],
        )
        self._no_data_label.pack(pady=40)