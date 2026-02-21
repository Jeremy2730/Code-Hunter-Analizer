"""
CodeHunter GUI - Sidebar
Panel lateral con: logo, selector de carpeta, navegación, botón de análisis.
"""

import os
import threading
import traceback
import customtkinter as ctk
from tkinter import filedialog
from CodeHunter.analyzers.system_doctor import run_code_doctor


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, state, navigate_fn, colors):
        super().__init__(
            parent,
            width=220,
            fg_color=colors["bg_panel"],
            corner_radius=0,
        )
        self.grid_propagate(False)
        self.grid_rowconfigure(5, weight=1)

        self.state     = state
        self.navigate  = navigate_fn
        self.colors    = colors
        self._nav_btns = {}

        self._build_sidebar()

    # ──────────────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        """Director: construye el sidebar llamando a sub-funciones."""
        self._build_logo()
        self._build_folder_selector()
        self._build_run_button()
        self._build_navigation()
        self._build_footer()

    def _build_logo(self):
        C = self.colors
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")

        ctk.CTkLabel(
            logo_frame,
            text="⟨/⟩",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=C["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="CodeHunter",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=C["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            self,
            text="v1.0  •  Python Analyzer",
            font=ctk.CTkFont(size=10),
            text_color=C["text_muted"],
        ).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

    def _build_folder_selector(self):
        C = self.colors
        section_label(self, "PROYECTO", C).grid(
            row=2, column=0, padx=20, pady=(0, 6), sticky="w"
        )

        folder_frame = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=8)
        folder_frame.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")
        folder_frame.grid_columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(
            folder_frame,
            font=ctk.CTkFont(size=11),
            text_color=C["text_muted"],
            wraplength=150,
            anchor="w",
        )
        self.path_label.grid(row=0, column=0, padx=10, pady=6, sticky="w")

        self.project_name_label = ctk.CTkLabel(
            folder_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=C["text_primary"],
            anchor="center",
        )
        self.project_name_label.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            folder_frame,
            font=ctk.CTkFont(size=12),
            height=32,
            fg_color=C["bg_hover"],
            hover_color=C["border"],
            text_color=C["text_primary"],
            corner_radius=6,
            command=self._pick_folder,
        ).grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")

    def _build_run_button(self):
        C = self.colors
        self.run_btn = ctk.CTkButton(
            self,
            text="▶  Ejecutar diagnóstico",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            fg_color=C["accent"],
            hover_color="#1F6FEB",
            text_color="#FFFFFF",
            corner_radius=8,
            command=self._run_analysis,
        )
        self.run_btn.grid(row=4, column=0, padx=12, pady=(0, 24), sticky="ew")

    def _build_navigation(self):
        C = self.colors
        section_label(self, "NAVEGACIÓN", C).grid(
            row=5, column=0, padx=20, pady=(0, 6), sticky="nw"
        )

        nav_items = [
            ("dashboard", "◈  Dashboard"),
            ("findings",  "⚠  Hallazgos"),
            ("tree",      "🌲  Árbol"),
            ("search",    "🔍  Buscar"),
        ]

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=5, column=0, padx=12, pady=(20, 0), sticky="new")

        for view_id, label in nav_items:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                font=ctk.CTkFont(size=13),
                height=38,
                anchor="w",
                fg_color="transparent",
                hover_color=C["bg_hover"],
                text_color=C["text_muted"],
                corner_radius=7,
                command=lambda v=view_id: self.navigate(v),
            )
            btn.pack(fill="x", pady=2)
            self._nav_btns[view_id] = btn

    def _build_footer(self):
        C = self.colors
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=6, column=0, padx=12, pady=16, sticky="sew")

        self.theme_var = ctk.StringVar(value="dark")
        ctk.CTkSwitch(
            footer,
            text="Tema claro",
            font=ctk.CTkFont(size=11),
            text_color=C["text_muted"],
            variable=self.theme_var,
            onvalue="light",
            offvalue="dark",
            command=self._toggle_theme,
            progress_color=C["accent"],
        ).pack(anchor="w")

    # ──────────────────────────────────────────────────────────────────────────
    def set_active(self, view_name: str):
        """Resalta el botón de navegación activo."""
        C = self.colors
        for vid, btn in self._nav_btns.items():
            if vid == view_name:
                btn.configure(fg_color=C["bg_hover"], text_color=C["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=C["text_muted"])

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Selecciona el proyecto Python")
        if path:
            self.state.project_path = path
            short = os.path.basename(path) or path
            self.path_label.configure(
                text=f"📂  {short}", text_color=self.colors["text_primary"]
            )
            self.state.reset()
            self.state.notify("folder_selected", path)

    def _run_analysis(self):
        if not self.state.project_path:
            self.path_label.configure(
                text="⚠ Selecciona una carpeta",
                text_color=self.colors["accent_yellow"]
            )
            return

        self.run_btn.configure(text="⏳  Analizando...", state="disabled")
        self.state.status = "RUNNING"
        self.state.notify("analysis_started")
        threading.Thread(target=self._do_analysis, daemon=True).start()

    def _do_analysis(self):
        print("Iniciando análisis de:", self.state.project_path)
        try:
            print("Importando backend...")
            result = run_code_doctor(self.state.project_path)
            print("Resultado:", result)
            self.state.diagnosis_data = result
            self.state.findings       = result.get("findings", [])
            self.state.health_score   = result.get("score", 0.0)
            self.state.status         = "DONE"
            self.state.notify("analysis_done", result)
        except Exception as e:
            traceback.print_exc()
            self.state.status = "ERROR"
            self.state.notify("analysis_error", str(e))
        finally:
            self.after(0, self._restore_run_btn)

    def _restore_run_btn(self):
        self.run_btn.configure(text="▶  Ejecutar diagnóstico", state="normal")

    def _toggle_theme(self):
        ctk.set_appearance_mode(self.theme_var.get())


# ── Helper ─────────────────────────────────────────────────────────────────────
def section_label(parent, text, colors):
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=colors["text_muted"],
    )