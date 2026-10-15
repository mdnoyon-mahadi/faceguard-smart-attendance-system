# ============================================================
# theme.py — Centralized Theme Manager
# ============================================================
# Usage:
#   from theme import ThemeManager
#   ThemeManager.get_color("bg")       → returns current bg color
#   ThemeManager.toggle()              → switches dark ↔ light
#   ThemeManager.apply_ctk()          → updates CTk appearance mode
# ============================================================

import customtkinter as ctk

# ── Theme Definitions ─────────────────────────────────────────

THEMES = {
    "dark": {
        "bg":            "#0d1117",   # Darker background
        "bg2":           "#161b22",   # Navbar background
        "sidebar":       "#0a0e1a",   # Sidebar background
        "card":          "#0d121f",   # Card
        "card_border":   "#1e293b",   # Subtle border
        "text":          "#f8fafc",   # Near white text
        "text_dim":      "#94a3b8",   # Muted text
        "accent":        "#00d2ff",   # Vibrant cyan
        "accent2":       "#7c3aed",   # Purple
        "accent3":       "#0ea5e9",   # Sky blue
        "btn_active":    "#1e293b",
        "hover":         "#1e293b",
        "sep":           "#1e293b",
        "danger":        "#f87171",
        "success":       "#4ade80",
        "ctk_mode":      "dark",
    },
    "light": {
        "bg":            "#f1f5f9",   # Soft gray
        "bg2":           "#e2e8f0",   # Slightly darker bg
        "sidebar":       "#f1f5f9",   # Sidebar
        "card":          "#ffffff",   # Pure white
        "card_border":   "#cbd5e1",   # Visible light border
        "text":          "#1e293b",   # Dark navy text
        "text_dim":      "#64748b",   # Muted text
        "accent":        "#3b82f6",   # Soft blue
        "accent2":       "#6366f1",   # Indigo
        "accent3":       "#2563eb",   # Deep blue
        "btn_active":    "#e2e8f0",   # Active button
        "hover":         "#f1f5f9",   # Hover
        "sep":           "#cbd5e1",   # Separator
        "danger":        "#ef4444",   # Red
        "success":       "#22c55e",   # Green
        "ctk_mode":      "light",
    },
}


# ── ThemeManager Singleton ────────────────────────────────────

class _ThemeManager:
    """
    Singleton theme manager. Stores current mode and provides
    color lookups and theme toggle functionality.
    """

    def __init__(self):
        self._mode = "dark"                # Default mode
        self._callbacks = []               # List of refresh callbacks

    # ── Public API ───────────────────────────────────────────

    @property
    def current_mode(self) -> str:
        return self._mode

    @current_mode.setter
    def current_mode(self, mode: str):
        if mode in THEMES:
            self._mode = mode

    def get_color(self, key: str) -> str:
        """Return a color value for the current theme."""
        return THEMES[self._mode].get(key, "#ffffff")

    def toggle(self):
        """Toggle between dark and light mode."""
        self._mode = "light" if self._mode == "dark" else "dark"
        self.apply_ctk()
        self._notify_callbacks()

    def apply_ctk(self):
        """Sync CustomTkinter's global appearance mode with current theme."""
        ctk.set_appearance_mode(THEMES[self._mode]["ctk_mode"])

    def register(self, callback):
        """
        Register a refresh callback. Called whenever theme toggles.
        The callback must accept no arguments.
        Example:
            ThemeManager.register(self.refresh_ui)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister(self, callback):
        """Remove a previously registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self):
        """Invoke all registered refresh callbacks safely."""
        dead = []
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                dead.append(cb)
        # Clean up dead callbacks
        for cb in dead:
            self._callbacks.remove(cb)


# ── Singleton Instance ────────────────────────────────────────
# Import and use this across the project:
#   from theme import ThemeManager
ThemeManager = _ThemeManager()