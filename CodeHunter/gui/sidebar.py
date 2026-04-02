"""
CodeHunter GUI - Sidebar (Panel lateral principal)

🎯 Propósito:
Control central de interacción del usuario dentro de la aplicación.

🧠 Qué hace:
- Selecciona proyecto
- Permite elegir perfil de análisis
- Ejecuta análisis en segundo plano
- Controla navegación entre vistas

⚙️ Perfiles:
- fast → rápido
- full → completo
- security → seguridad

🔥 NO analiza código directamente
"""

import threading
import customtkinter as ctk
from tkinter import filedialog
from CodeHunter.analyzers.advanced_diagnostics import run_advanced_analysis


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, state, navigate_fn, colors):
        super().__init__(parent, width=220, fg_color=colors["bg_panel"], corner_radius=0)

        self.grid_propagate(False)
        self.grid_rowconfigure(6, weight=1)

        self.state = state
        self.navigate = navigate_fn
        self.colors = colors
        self._nav_btns = {}

        self.profile = ctk.StringVar(value="full")

        self._build_sidebar()

    def _build_sidebar(self):
        self._build_logo()
        self._build_folder_selector()
        self._build_profile_selector()
        self._build_run_button()
        self._build_navigation()
        self._build_footer()

    def _build_logo(self):
        C = self.colors

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")

        ctk.CTkLabel(frame, text="⟨/⟩",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=C["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(frame, text="CodeHunter",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=C["text_primary"],
        ).pack(side="left")

    def _build_folder_selector(self):
        C = self.colors

        section_label(self, "PROYECTO", C).grid(row=1, column=0, padx=20, pady=(10, 6), sticky="w")

        frame = ctk.CTkFrame(self, fg_color=C["bg_card"])
        frame.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkButton(frame, text="📂 Abrir carpeta",
            command=self._pick_folder
        ).pack(fill="x", padx=8, pady=8)

    def _build_profile_selector(self):
        C = self.colors

        section_label(self, "MODO DE ANÁLISIS", C).grid(row=3, column=0, padx=20, pady=(0, 6), sticky="w")

        option = ctk.CTkOptionMenu(
            self,
            values=["fast", "full", "security"],
            variable=self.profile
        )
        option.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="ew")

    def _build_run_button(self):
        self.run_btn = ctk.CTkButton(self,
            text="▶ Ejecutar diagnóstico",
            command=self._run_analysis
        )
        self.run_btn.grid(row=5, column=0, padx=12, pady=(0, 20), sticky="ew")

    def _build_navigation(self):
        C = self.colors

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=6, column=0, padx=12, sticky="n")

        for vid, label in [
            ("tree", "🌲 Árbol"),
            ("search", "🔍 Buscar"),
            ("findings", "⚠ Hallazgos"),
            ("dashboard", "📊 Dashboard"),
        ]:
            btn = ctk.CTkButton(nav_frame, text=label,
                fg_color="transparent",
                hover_color=C["bg_hover"],
                text_color=C["text_muted"],
                anchor="w",
                command=lambda v=vid: self._on_nav(v)
            )
            btn.pack(fill="x", pady=2)
            self._nav_btns[vid] = btn

    def _build_footer(self):
        self.theme_var = ctk.StringVar(value="dark")

        ctk.CTkSwitch(self,
            text="Tema claro",
            variable=self.theme_var,
            onvalue="light",
            offvalue="dark",
            command=self._toggle_theme
        ).grid(row=7, column=0, padx=12, pady=10)

    # 🔥 NUEVO CONTROL CENTRAL DE NAV
    def _on_nav(self, view_name):
        self.navigate(view_name)
        self.set_active(view_name)

    def set_active(self, view_name: str):
        """Resalta botón activo"""
        C = self.colors

        for vid, btn in self._nav_btns.items():
            if vid == view_name:
                btn.configure(
                    fg_color=C["bg_hover"],
                    text_color=C["accent"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=C["text_muted"]
                )

    def _pick_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.state.project_path = path
            self.state.reset()
            self.state.notify("folder_selected", path)

    def _run_analysis(self):
        if not self.state.project_path:
            return

        self.run_btn.configure(text="⏳ Analizando...", state="disabled")
        self.state.status = "RUNNING"

        threading.Thread(target=self._do_analysis, daemon=True).start()

    def _do_analysis(self):
        try:
            result = run_advanced_analysis(
                self.state.project_path,
                profile=self.profile.get()
            )

            self.state.findings = result.get("findings", [])
            self.state.health_score = result.get("score", 0.0)
            self.state.status = "DONE"
            self.state.notify("analysis_done", result)

        except Exception as e:
            self.state.status = "ERROR"
            self.state.notify("analysis_error", str(e))

        finally:
            self.after(0, self._restore_btn)

    def _restore_btn(self):
        self.run_btn.configure(text="▶ Ejecutar diagnóstico", state="normal")

    def _toggle_theme(self):
        ctk.set_appearance_mode(self.theme_var.get())


def section_label(parent, text, colors):
    return ctk.CTkLabel(parent, text=text)