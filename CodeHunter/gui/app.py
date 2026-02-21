"""
CodeHunter GUI - Ventana Principal
Layout: Sidebar izquierdo + Barra de título + Área de contenido
"""

import os
import customtkinter as ctk
from gui.sidebar import Sidebar
from gui.views.dashboard_view import DashboardView
from gui.views.findings_view import FindingsView
from gui.views.tree_view import TreeView
from gui.views.search_view import SearchView
from gui.state import AppState


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg_dark":       "#0D1117",
    "bg_panel":      "#161B22",
    "bg_card":       "#21262D",
    "bg_hover":      "#2D333B",
    "accent":        "#58A6FF",
    "accent_green":  "#3FB950",
    "accent_yellow": "#D29922",
    "accent_red":    "#F85149",
    "text_primary":  "#E6EDF3",
    "text_muted":    "#7D8590",
    "border":        "#30363D",
}


class CodeHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.app_state = AppState()

        self.title("CodeHunter  •  Analizador de Proyectos Python")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        # ── Layout: sidebar | (titulo + contenido) ────────────────────────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, self.app_state, self._navigate, COLORS)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Columna derecha: título arriba + contenido abajo
        right_col = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.grid_columnconfigure(0, weight=1)
        right_col.grid_rowconfigure(1, weight=1)

        # ── Barra de título del proyecto ──────────────────────────────────────
        self.title_bar = ctk.CTkFrame(
            right_col,
            fg_color=COLORS["bg_panel"],
            corner_radius=0,
            height=48,
        )
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.grid_propagate(False)
        self.title_bar.grid_columnconfigure(0, weight=1)

        self.project_title_label = ctk.CTkLabel(
            self.title_bar,
            text="Ningún proyecto seleccionado",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS["text_muted"],
            anchor="center",
        )
        self.project_title_label.grid(row=0, column=0, sticky="nsew", padx=20)

        # ── Área de contenido ─────────────────────────────────────────────────
        self.content_frame = ctk.CTkFrame(
            right_col, fg_color=COLORS["bg_dark"], corner_radius=0
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # ── Vistas ────────────────────────────────────────────────────────────
        self._views: dict[str, ctk.CTkFrame] = {}
        self._active_view: str | None = None
        self._init_views()

        # Suscribirse a cambios de estado para actualizar el título
        self.app_state.subscribe(self._on_state_change)

        self._navigate("dashboard")

    def _init_views(self):
        view_classes = {
            "dashboard": DashboardView,
            "findings":  FindingsView,
            "tree":      TreeView,
            "search":    SearchView,
        }
        for name, ViewClass in view_classes.items():
            view = ViewClass(self.content_frame, self.app_state, COLORS)
            view.grid(row=0, column=0, sticky="nsew")
            self._views[name] = view

    def _navigate(self, view_name: str):
        for name, view in self._views.items():
            if name == view_name:
                view.tkraise()
            else:
                view.lower()
        self._active_view = view_name
        self.sidebar.set_active(view_name)

    def _on_state_change(self, event, data):
        if event in ("folder_selected", "analysis_done", "analysis_started", "reset"):
            self.after(0, self._update_title_bar)

    def _update_title_bar(self):
        path = self.app_state.project_path
        if not path:
            self.project_title_label.configure(
                text="Ningún proyecto seleccionado",
                text_color=COLORS["text_muted"],
            )
            return

        name = os.path.basename(path)
        self.project_title_label.configure(
            text=f"📂  {name}",
            text_color=COLORS["text_primary"],
        )