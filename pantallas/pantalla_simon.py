"""
Deprecated helper module.
This file remained from an older Simon implementation. Use `pantalla_juego_simon.py` instead.
The module keeps a small compatibility alias so older imports don't break.
"""
try:
    from .pantalla_juego_simon import PantallaJuegoSimon as PantallaSimon
except Exception:
    class PantallaSimon:
        def __init__(self, *args, **kwargs):
            raise RuntimeError('pantalla_simon is deprecated; use pantalla_juego_simon')
