"""
CodeHunter GUI - Ventana Principal
Layout: Sidebar izquierdo + Área de contenido principal
"""

import customtkinter as ctk
from gui.sidebar import Sidebar
from gui.views.dashboard_view import DashboardView
from gui.views.findings_view import FindingsView
from gui.views.tree_view import TreeView
from gui.views.search_view import SearchView
from gui.state import AppState


# ── Tema global ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta de colores CodeHunter
COLORS = {
    "bg_dark":      "#0D1117",   # Fondo principal (GitHub dark)
    "bg_panel":     "#161B22",   # Paneles / sidebar
    "bg_card":      "#21262D",   # Tarjetas / cards
    "bg_hover":     "#2D333B",   # Hover states
    "accent":       "#58A6FF",   # Azul acento (GitHub blue)
    "accent_green": "#3FB950",   # Healthy
    "accent_yellow":"#D29922",   # Warning
    "accent_red":   "#F85149",   # Critical
    "text_primary": "#E6EDF3",   # Texto principal
    "text_muted":   "#7D8590",   # Texto secundario
    "border":       "#30363D",   # Bordes
}


class CodeHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Estado compartido de la app ────────────────────────────────────────
        self.state = AppState()

        # ── Configuración de ventana ───────────────────────────────────────────
        self.title("CodeHunter  •  Analizador de Proyectos Python")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(fg_color=COLORS["bg_dark"])

        # Icono (si existe)
        # self.iconbitmap("assets/icon.ico")

        # ── Layout principal: sidebar (fijo) + contenido (expansible) ─────────
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, self.state, self._navigate, COLORS)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Área de contenido
        self.content_frame = ctk.CTkFrame(
            self, fg_color=COLORS["bg_dark"], corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # ── Vistas registradas ─────────────────────────────────────────────────
        self._views: dict[str, ctk.CTkFrame] = {}
        self._active_view: str | None = None

        self._init_views()

        # ── Vista inicial ──────────────────────────────────────────────────────
        self._navigate("dashboard")

    # ──────────────────────────────────────────────────────────────────────────
    def _init_views(self):
        """Crea todas las vistas y las apila en el mismo slot de la grilla."""
        view_classes = {
            "dashboard": DashboardView,
            "findings":  FindingsView,
            "tree":      TreeView,
            "search":    SearchView,
        }
        for name, ViewClass in view_classes.items():
            view = ViewClass(self.content_frame, self.state, COLORS)
            view.grid(row=0, column=0, sticky="nsew")
            self._views[name] = view

    def _navigate(self, view_name: str):
        """Muestra la vista solicitada y oculta las demás."""
        for name, view in self._views.items():
            if name == view_name:
                view.tkraise()
            else:
                view.lower()

        self._active_view = view_name
        self.sidebar.set_active(view_name)
