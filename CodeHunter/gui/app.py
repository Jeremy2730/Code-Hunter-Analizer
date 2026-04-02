"""
CodeHunter GUI - Ventana Principal

🎯 Propósito:
Contenedor principal de la aplicación.

🧠 Responsabilidades:
- Manejar layout general
- Controlar navegación entre vistas
- Sincronizar estado global
"""

import os
import customtkinter as ctk
from .sidebar import Sidebar 
from .views.dashboard_view import DashboardView
from .views.findings_view import FindingsView
from .views.tree_view import TreeView
from .views.search_view import SearchView
from .state import AppState


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


COLORS = {
    "bg_dark": "#0D1117",
    "bg_panel": "#161B22",
    "bg_card": "#21262D",
    "bg_hover": "#2D333B",
    "accent": "#58A6FF",
    "accent_green": "#3FB950",
    "accent_yellow": "#D29922",
    "accent_red": "#F85149",
    "text_primary": "#E6EDF3",
    "text_muted": "#7D8590",
    "border": "#30363D",
}


class CodeHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.app_state = AppState()

        self.title("CodeHunter • Analizador Python")
        self.geometry("1280x800")
        self.configure(fg_color=COLORS["bg_dark"])

        # Layout base
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, self.app_state, self._navigate, COLORS)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Panel derecho
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"])
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        # 🔥 IMPORTANTE (después de crear)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

        # Barra título
        self.title_bar = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLORS["bg_panel"],
            height=50
        )
        self.title_bar.grid(row=0, column=0, sticky="ew")

        self.project_title = ctk.CTkLabel(
            self.title_bar,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.project_title.pack(pady=10)

        # 🔥 AHORA SÍ CREAR views_container (ANTES NO EXISTÍA)
        self.views_container = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLORS["bg_dark"]
        )
        self.views_container.grid(row=1, column=0, sticky="nsew")

        # 🔥 CONFIGURAR EXPANSIÓN
        self.views_container.grid_columnconfigure(0, weight=1)
        self.views_container.grid_rowconfigure(0, weight=1)

        # Vistas
        self.views = {}
        self._init_views()

        # Estado
        self.app_state.subscribe(self._on_state_change)

        # Vista inicial
        self._navigate("dashboard")

    def _init_views(self):
        """Inicializa todas las vistas y las monta en el contenedor"""

        view_classes = {
            "dashboard": DashboardView,
            "findings": FindingsView,
            "tree": TreeView,
            "search": SearchView,
        }

        for name, View in view_classes.items():
            v = View(self.views_container, self.app_state, COLORS)
            v.grid(row=0, column=0, sticky="nsew")  # 🔥 CLAVE PARA QUE EXPANDA
            self.views[name] = v

    def _navigate(self, view_name):
        """Cambia entre vistas"""
        for name, view in self.views.items():
            if name == view_name:
                view.tkraise()

        # Sincronizar sidebar
        if hasattr(self.sidebar, "set_active"):
            self.sidebar.set_active(view_name)

    def _on_state_change(self, event, data):
        """Escucha cambios del estado global"""
        if event in ("folder_selected", "analysis_done"):
            self._update_title()

    def _update_title(self):
        """Actualiza el nombre del proyecto en la UI"""
        path = self.app_state.project_path
        if not path:
            self.project_title.configure(text="")
            return

        name = os.path.basename(path)
        self.project_title.configure(text=f"📂 {name}")