"""Audio manager simple para la demo: play/pause de música y mute/unmute.
Carga archivos desde la carpeta `assets/` del proyecto.
"""
import pygame
from pathlib import Path


class AudioManager:
    def __init__(self):
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.muted = False
        # volume scalar (0.0 .. 1.0)
        self.volume = 0.6
        self.music_channel = None
        # Preferir game_music.mp3 si existe, si no usar musica.mp3
        self.bg_path = Path('assets') / 'game_music.mp3'
        if not self.bg_path.exists():
            self.bg_path = Path('assets') / 'musica.mp3'

    def play_music(self, loop=True, path=None):
        try:
            p = Path(path) if path is not None else self.bg_path
            if p and p.exists():
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                pygame.mixer.music.load(str(p))
                pygame.mixer.music.set_volume(self.volume if not self.muted else 0)
                pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            pass

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def toggle_mute(self):
        self.muted = not self.muted
        try:
            if self.muted:
                pygame.mixer.music.set_volume(0)
            else:
                pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def set_volume(self, vol: float):
        try:
            self.volume = max(0.0, min(1.0, float(vol)))
            if not self.muted:
                pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass


_audio = None


def get_audio():
    global _audio
    if _audio is None:
        _audio = AudioManager()
    return _audio
