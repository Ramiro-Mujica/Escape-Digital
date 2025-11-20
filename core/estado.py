import time
import json
import os
from core.constants import DEFAULT_LIVES


class EstadoGlobal:
    """Estado global mínimo: nombre y cronómetro."""
    def __init__(self):
        self.nombre = None
        self.cronometro_inicio = None
        self.cronometro_fin = None
        # selected avatar path
        self.avatar = None
        # vidas del jugador (usar DEFAULT_LIVES desde constants)
        self.vidas = DEFAULT_LIVES
        # settings globales: brightness (-1.0 .. 1.0), contrast (0.5 .. 1.5)
        # brightness >0 => overlay blanco (más claro), <0 => overlay negro (más oscuro)
        self.brightness = 0.0
        self.contrast = 1.0
        # master volume (0.0 .. 1.0)
        self.volume = 0.6
        # try loading persisted settings
        try:
            self._settings_path = os.path.join(os.getcwd(), 'settings.json')
            self._load_settings()
        except Exception:
            # ignore persistence errors
            self._settings_path = None
        # last write timestamp for throttling saves
        try:
            self._last_settings_write = 0.0
        except Exception:
            self._last_settings_write = 0.0

    def iniciar_cronometro(self):
        """Start or resume the stopwatch.

        Behavior:
        - If never started, set start=time.time().
        - If stopped (cronometro_fin set), resume by shifting start so elapsed time is preserved.
        - If already running, do nothing.
        """
        now = time.time()
        # never started
        if self.cronometro_inicio is None:
            self.cronometro_inicio = now
            self.cronometro_fin = None
            return
        # was running and not stopped -> keep running
        if self.cronometro_fin is None:
            return
        # was stopped, resume preserving elapsed
        try:
            elapsed = float(self.cronometro_fin - self.cronometro_inicio)
            # set start so that (now - start) == elapsed
            self.cronometro_inicio = now - elapsed
            self.cronometro_fin = None
        except Exception:
            # fallback: restart from now
            self.cronometro_inicio = now
            self.cronometro_fin = None

    def detener_cronometro(self):
        # stop only if it was running; keep last end time
        if self.cronometro_inicio is not None and self.cronometro_fin is None:
            self.cronometro_fin = time.time()

    def tiempo_transcurrido(self):
        if self.cronometro_inicio is None:
            return 0.0
        end = self.cronometro_fin if self.cronometro_fin is not None else time.time()
        return end - self.cronometro_inicio

    # helpers para settings
    def set_brightness(self, value: float):
        # clamp
        self.brightness = max(-1.0, min(1.0, float(value)))

    def set_contrast(self, value: float):
        self.contrast = max(0.5, min(1.5, float(value)))
        try:
            # lightweight debug log to help verify slider changes during testing
            print(f"[Estado] set_contrast -> {self.contrast}")
        except Exception:
            pass

    def set_volume(self, value: float):
        try:
            self.volume = max(0.0, min(1.0, float(value)))
        except Exception:
            return

        # apply immediately to audio manager if available
        try:
            from core.audio import get_audio
            try:
                get_audio().set_volume(self.volume)
            except Exception:
                pass
        except Exception:
            pass
        try:
            # debug log for volume changes
            print(f"[Estado] set_volume -> {self.volume}")
        except Exception:
            pass

    def set_avatar(self, avatar_path: str | None):
        try:
            self.avatar = avatar_path
            self._save_settings()
        except Exception:
            pass

    # vidas management
    def perder_vida(self, n: int = 1):
        try:
            self.vidas = max(0, int(self.vidas) - int(n))
            self._save_settings()
        except Exception:
            pass

    def ganar_vida(self, n: int = 1):
        try:
            self.vidas = int(self.vidas) + int(n)
            self._save_settings()
        except Exception:
            pass

    def set_vidas(self, v: int):
        try:
            self.vidas = max(0, int(v))
            self._save_settings()
        except Exception:
            pass

    def _save_settings(self):
        if not hasattr(self, '_settings_path') or not self._settings_path:
            return
        # throttle frequent saves (e.g., while dragging sliders)
        try:
            now = time.time()
            if now - getattr(self, '_last_settings_write', 0.0) < 0.25:
                return
            self._last_settings_write = now
        except Exception:
            pass
        # Persist minimal settings only (do NOT persist brightness/contrast/volume)
        data = {}
        # include avatar if available
        try:
            data['avatar'] = self.avatar if getattr(self, 'avatar', None) is not None else None
        except Exception:
            pass
        try:
            # include vidas as part of settings persistence
            try:
                data['vidas'] = int(self.vidas)
            except Exception:
                data['vidas'] = None
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            # don't raise on save failure
            pass

    def _load_settings(self):
        if not hasattr(self, '_settings_path') or not self._settings_path:
            return
        if not os.path.exists(self._settings_path):
            return
        try:
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Do not load brightness/contrast/volume from disk to avoid persistent adjustments.
            a = data.get('avatar')
            v = data.get('vidas')
            if a is not None:
                try:
                    self.avatar = str(a)
                except Exception:
                    self.avatar = None
            if v is not None:
                try:
                    self.vidas = int(v)
                except Exception:
                    pass
        except Exception:
            pass
