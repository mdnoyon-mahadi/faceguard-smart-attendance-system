# ============================================================
# transitions.py — Page Transition Manager  (v4 — Instant Feel)
# ============================================================
#
# THE CORE PROBLEM THIS VERSION SOLVES
# ──────────────────────────────────────
# CTkToplevel window creation on Windows takes ~300–800 ms
# (OS window handle + widget build). In v3, the home page sat
# frozen during this time → user felt a 2-second lag.
#
# THE FIX: "Instant Feedback + Background Build" pattern
# ──────────────────────────────────────────────────────
#   1. navigate() dims the CURRENT page instantly (1 frame,
#      alpha 1.0 → 0.42) so the user gets immediate response.
#   2. The new window builds while the current page is dimmed.
#   3. Once ready, both windows cross-fade simultaneously.
#
# NEW in v4
# ──────────────────────────────────────────────────────
#   • navigate()      — the recommended single method for all page changes
#   • instant_dim()   — one-liner instant feedback on button press
#   • _parallel_fade()— outgoing + incoming animate on same timer
#   • Faster defaults — 80 ms total (steps=8, ms=10)
#   • Quartic ease-out — snappier than cubic, still buttery smooth
#   • after(1) kick   — no initial dead-frame delay
#
# BACKWARD COMPATIBLE — all v2/v3 call sites work unchanged.
#
# ── Recommended usage ────────────────────────────────────
#
#   # Home page button:
#   def _open_admin(self):
#       PageTransition.navigate(
#           self,
#           lambda: AdminLogin(on_close=self._restore)
#       )
#
#   # Every Toplevel __init__ (unchanged from v3):
#   super().__init__()
#   PageTransition.prepare_window(self)
#   self._build_ui()
#   PageTransition.fade_in(self)
# ============================================================


# ── Timing ────────────────────────────────────────────────────────────────────
FADE_STEPS  = 8      # 8 frames × 10 ms = 80 ms total fade
FADE_MS     = 10     # ms between frames  (~100 fps feel)
SLIDE_STEPS = 10     # slide frames
SLIDE_MS    = 10     # ms between slide frames
SLIDE_PX    = 18     # max pixel offset (subtle)
DIM_ALPHA   = 0.42   # instant-dim target for click feedback


# ── Easing curves ─────────────────────────────────────────────────────────────

def _ease_out(t):
    """Quartic ease-out — snappier than cubic."""
    return 1.0 - (1.0 - t) ** 4

def _ease_in(t):
    """Quartic ease-in."""
    return t ** 4

def _ease_in_out(t):
    """Smooth-step — gentle at both ends, good for cross-fade."""
    return t * t * (3.0 - 2.0 * t)

def _ease_out_back(t):
    """Ease-out with tiny overshoot — snap-into-place feel for slide."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


# ── Navigation Lock ───────────────────────────────────────────────────────────

class NavigationLock:
    """Prevents double-click from firing two concurrent transitions."""
    _locked = False

    @classmethod
    def acquire(cls) -> bool:
        if cls._locked:
            return False
        cls._locked = True
        return True

    @classmethod
    def release(cls):
        cls._locked = False

    @classmethod
    def force_release(cls):
        """Emergency reset if UI ever gets permanently stuck."""
        cls._locked = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _exists(win) -> bool:
    try:
        return bool(win.winfo_exists())
    except Exception:
        return False

def _alpha(win, value: float) -> bool:
    try:
        win.attributes("-alpha", max(0.0, min(1.0, value)))
        return True
    except Exception:
        return False

def _safe_call(fn):
    try:
        fn()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
class PageTransition:
    """
    v4 — Instant-feel page transition engine.
    All methods are @staticmethod. Drop-in for v2/v3.
    """

    # ── navigate() ────────────────────────────────────────────────────────────
    @staticmethod
    def navigate(outgoing, builder, on_done=None):
        """
        THE recommended way to open a new page. Eliminates perceived lag.

        Steps:
          1. Dims outgoing instantly (1 paint cycle) → instant feedback
          2. Calls builder() to create the new window.
             New window MUST call prepare_window() as first line.
          3. Cross-fades outgoing → 0  and  incoming → 1 simultaneously.

        Args:
            outgoing : the currently visible window/toplevel
            builder  : callable() → new window (or None to abort)
            on_done  : optional callback when animation finishes

        Example:
            def _go_to_admin(self):
                PageTransition.navigate(
                    self,
                    lambda: AdminLogin(on_close=self._show)
                )
        """
        if not NavigationLock.acquire():
            return

        if not _exists(outgoing):
            NavigationLock.release()
            return

        # ── 1. Instant dim — user sees response NOW ────────────────────────
        _alpha(outgoing, DIM_ALPHA)

        # ── 2. Build new window (invisible via prepare_window) ─────────────
        try:
            incoming = builder()
        except Exception:
            _alpha(outgoing, 1.0)
            NavigationLock.release()
            return

        if incoming is None or not _exists(incoming):
            _alpha(outgoing, 1.0)
            NavigationLock.release()
            return

        # ── 3. Parallel cross-fade ─────────────────────────────────────────
        PageTransition._parallel_fade(
            outgoing, incoming,
            start_out=DIM_ALPHA,
            on_done=on_done,
        )

    # ── instant_dim() ─────────────────────────────────────────────────────────
    @staticmethod
    def instant_dim(window):
        """
        Dim a window in a single call — use on button press for
        immediate click feedback before any heavy work begins.

            def _on_click(self):
                PageTransition.instant_dim(self)
                self.after(0, self._do_heavy_work)
        """
        _alpha(window, DIM_ALPHA)

    # ── prepare_window() ──────────────────────────────────────────────────────
    @staticmethod
    def prepare_window(window):
        """
        Call as the VERY FIRST line after super().__init__().
        Hides at OS level (withdraw) so widget build is invisible.

            class MyPage(ctk.CTkToplevel):
                def __init__(self):
                    super().__init__()
                    PageTransition.prepare_window(self)  # ← here
                    self._build_ui()
                    PageTransition.fade_in(self)
        """
        try:
            window.withdraw()
        except Exception:
            pass
        _alpha(window, 0.0)

    # ── fade_in() ─────────────────────────────────────────────────────────────
    @staticmethod
    def fade_in(window, target_alpha: float = 1.0,
                steps: int = FADE_STEPS, ms: int = FADE_MS,
                on_done=None):
        """Ease-out fade 0 → target_alpha. Calls deiconify() first."""
        if not _exists(window):
            if on_done:
                _safe_call(on_done)
            return

        _safe_call(window.deiconify)
        _alpha(window, 0.0)
        frame = [0]

        def _step():
            if not _exists(window):
                if on_done:
                    _safe_call(on_done)
                return
            frame[0] += 1
            t = frame[0] / steps
            _alpha(window, target_alpha * _ease_out(min(t, 1.0)))
            if frame[0] >= steps:
                _alpha(window, target_alpha)
                if on_done:
                    _safe_call(on_done)
                return
            try:
                window.after(ms, _step)
            except Exception:
                _alpha(window, target_alpha)
                if on_done:
                    _safe_call(on_done)

        try:
            window.after(1, _step)   # after(1) — no dead-frame delay
        except Exception:
            _alpha(window, target_alpha)
            if on_done:
                _safe_call(on_done)

    # ── fade_out() ────────────────────────────────────────────────────────────
    @staticmethod
    def fade_out(window, on_done=None,
                 steps: int = FADE_STEPS, ms: int = FADE_MS,
                 withdraw_after: bool = False):
        """Ease-in fade current alpha → 0, then call on_done()."""
        if not _exists(window):
            NavigationLock.release()
            if on_done:
                _safe_call(on_done)
            return

        try:
            start = float(window.attributes("-alpha"))
        except Exception:
            start = 1.0

        if start <= 0.02:
            NavigationLock.release()
            if withdraw_after:
                _safe_call(window.withdraw)
            if on_done:
                _safe_call(on_done)
            return

        frame = [0]

        def _step():
            if not _exists(window):
                NavigationLock.release()
                if on_done:
                    _safe_call(on_done)
                return
            frame[0] += 1
            t = frame[0] / steps
            _alpha(window, start * (1.0 - _ease_in(min(t, 1.0))))
            if frame[0] >= steps:
                _alpha(window, 0.0)
                NavigationLock.release()
                if withdraw_after:
                    _safe_call(window.withdraw)
                if on_done:
                    _safe_call(on_done)
                return
            try:
                window.after(ms, _step)
            except Exception:
                NavigationLock.release()
                if on_done:
                    _safe_call(on_done)

        try:
            window.after(1, _step)
        except Exception:
            NavigationLock.release()
            _alpha(window, 0.0)
            if on_done:
                _safe_call(on_done)

    # ── slide_in() ────────────────────────────────────────────────────────────
    @staticmethod
    def slide_in(window, direction: str = "right",
                 steps: int = SLIDE_STEPS, ms: int = SLIDE_MS):
        """
        Slide + fade with ease-out-back (subtle snap on arrival).
        direction="right" → forward  |  direction="left" → back
        Geometry is snapped to exact origin after animation (no drift).
        """
        if not _exists(window):
            return

        _safe_call(window.deiconify)
        try:
            window.update_idletasks()
            x0 = window.winfo_x()
            y0 = window.winfo_y()
        except Exception:
            PageTransition.fade_in(window, steps=steps, ms=ms)
            return

        offset = SLIDE_PX if direction == "right" else -SLIDE_PX

        try:
            window.geometry(f"+{x0 + offset}+{y0}")
            _alpha(window, 0.0)
        except Exception:
            PageTransition.fade_in(window, steps=steps, ms=ms)
            return

        frame = [0]

        def _step():
            if not _exists(window):
                return
            frame[0] += 1
            t  = frame[0] / steps
            et = _ease_out_back(min(t, 1.0))
            a  = max(0.0, min(1.0, et))
            cur_x = x0 + int(offset * (1.0 - min(et, 1.0)))
            _alpha(window, a)
            try:
                window.geometry(f"+{cur_x}+{y0}")
            except Exception:
                return
            if frame[0] >= steps:
                try:
                    window.geometry(f"+{x0}+{y0}")
                    _alpha(window, 1.0)
                except Exception:
                    pass
                return
            try:
                window.after(ms, _step)
            except Exception:
                pass

        try:
            window.after(1, _step)
        except Exception:
            try:
                window.geometry(f"+{x0}+{y0}")
            except Exception:
                pass
            _alpha(window, 1.0)

    # ── appear() ──────────────────────────────────────────────────────────────
    @staticmethod
    def appear(window):
        """Quick fade-in alias."""
        PageTransition.fade_in(window)

    # ── switch() — legacy ─────────────────────────────────────────────────────
    @staticmethod
    def switch(outgoing, on_hide, incoming=None, direction: str = "right"):
        """v2/v3 compatible. Prefer navigate() for new code."""
        if not NavigationLock.acquire():
            return

        def _after_fade():
            _safe_call(on_hide)
            if incoming is not None and _exists(incoming):
                PageTransition.slide_in(incoming, direction=direction)

        PageTransition.fade_out(outgoing, on_done=_after_fade)

    # ── cross_fade() ──────────────────────────────────────────────────────────
    @staticmethod
    def cross_fade(outgoing, incoming, on_hide=None,
                   steps: int = FADE_STEPS, ms: int = FADE_MS):
        """Fade out + fade in simultaneously. navigate() uses this internally."""
        if not NavigationLock.acquire():
            return
        PageTransition._parallel_fade(
            outgoing, incoming,
            start_out=None,
            steps=steps, ms=ms,
            on_done=on_hide,
        )

    # ── _parallel_fade() — internal ───────────────────────────────────────────
    @staticmethod
    def _parallel_fade(outgoing, incoming,
                       start_out=None,
                       steps: int = FADE_STEPS,
                       ms: int = FADE_MS,
                       on_done=None):
        """
        Runs both fades on a single shared timer — perfectly in sync.
        Uses ease-in-out for a cinematic blend.
        Releases NavigationLock on completion.
        """
        if start_out is None:
            try:
                start_out = float(outgoing.attributes("-alpha"))
            except Exception:
                start_out = 1.0

        if _exists(incoming):
            _safe_call(incoming.deiconify)
            _alpha(incoming, 0.0)

        frame = [0]

        def _step():
            frame[0] += 1
            t  = frame[0] / steps
            et = _ease_in_out(min(t, 1.0))

            out_ok = _exists(outgoing)
            inc_ok = _exists(incoming)

            if out_ok:
                _alpha(outgoing, start_out * (1.0 - et))
            if inc_ok:
                _alpha(incoming, et)

            if frame[0] >= steps:
                if out_ok:
                    _alpha(outgoing, 0.0)
                if inc_ok:
                    _alpha(incoming, 1.0)
                NavigationLock.release()
                if on_done:
                    _safe_call(on_done)
                return

            host = incoming if inc_ok else (outgoing if out_ok else None)
            if host:
                try:
                    host.after(ms, _step)
                except Exception:
                    NavigationLock.release()
                    if on_done:
                        _safe_call(on_done)
            else:
                NavigationLock.release()
                if on_done:
                    _safe_call(on_done)

        host = incoming if _exists(incoming) else (
               outgoing if _exists(outgoing) else None)
        if host:
            try:
                host.after(1, _step)
            except Exception:
                NavigationLock.release()
        else:
            NavigationLock.release()