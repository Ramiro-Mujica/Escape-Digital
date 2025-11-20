import pygame
import math
from pantallas.pantalla_registro import PantallaRegistro
from pantallas.pantalla_reglas import PantallaReglas
from pantallas.pantalla_juego_cesar import PantallaJuegoCesar
from pantallas.pantalla_juego_placeholder import PantallaJuegoPlaceholder
from pantallas.pantalla_juego_2 import PantallaJuego2
from pantallas.pantalla_juego_parejas import PantallaJuegoParejas
from pantallas.pantalla_juego_simon import PantallaJuegoSimon
from pantallas.pantalla_records import PantallaRecords
from core.gestor_registros import guardar_registro
from core.ui_helpers import draw_persistent_hud, draw_game_over_modal
from core.pointer import load_pointer, draw_pointer
from core.constants import DEFAULT_LIVES, POINTER_PATH


RULES_TEXTS = [
    "Juego 1 - César:\nRegla: cada letra se desplaza 3 posiciones hacia adelante en el alfabeto.\nEjemplo: para la palabra 'hola' la letra 'h' corresponde a 'k' (h -> k).\nEn el juego verás una palabra CIFRADA y deberás escribir la original. La letra 'ñ' no se considera.",
    "Juego 2 - Minidesafío:\nUn pequeño reto adaptado a la pantalla. Selecciona la respuesta correcta para avanzar. (Interfaz simple adaptada al panel central).",
    "Juego 3 - Parejas (Memory):\nEncuentra las parejas iguales dentro del recuadro central (utilizamos imágenes de assets).\nAl fallar se mostrarán las tarjetas unos instantes y luego se ocultarán. Completa todas las parejas para avanzar.",
    "Juego 4 - Patrón (Simon-lite):\nMemoriza la secuencia mostrada. Cada ronda la secuencia crecerá. Hay una espera aproximada de 3 segundos entre rondas al mostrar el siguiente patrón.\nSe requieren 8 rondas correctas para habilitar el botón continuar."
]


class AppController:
    def __init__(self, pantalla, estado, fps=60):
        self.pantalla = pantalla
        self.estado = estado
        self.reloj = pygame.time.Clock()
        self.fps = fps

        # load pointer if available (use constants)
        self.puntero_img = load_pointer(POINTER_PATH)

        # sequence setup
        self.seq = []
        for i in range(1, 5):
            self.seq.append(('rules', i))
            self.seq.append(('game', i))
        self.seq_idx = 0

        # runtime state
        self.pantalla_actual = None
        self.pantalla_records = None
        self.modo = 'inicio'
        self.game_over_active = False
        self.game_over_until = None

        # ensure guard flag
        try:
            self.estado.record_saved = False
        except Exception:
            setattr(self.estado, 'record_saved', False)

    def _instantiate_screen_for(self, kind, idx):
        if kind == 'rules':
            return PantallaReglas(self.pantalla, idx, f'Reglas Juego {idx}', RULES_TEXTS[idx-1])
        else:
            if idx == 1:
                return PantallaJuegoCesar(self.pantalla, idx, 'Juego César')
            elif idx == 2:
                return PantallaJuego2(self.pantalla, idx, 'Juego 2')
            elif idx == 3:
                return PantallaJuegoParejas(self.pantalla, idx, 'Juego Parejas')
            elif idx == 4:
                return PantallaJuegoSimon(self.pantalla, idx, 'Juego Patrón')
            else:
                return PantallaJuegoPlaceholder(self.pantalla, idx, f'Juego {idx}')

    def _draw_persistent_hud_fallback(self):
        try:
            if getattr(self.estado, 'hud_persistent', False) and self.pantalla_actual is not None:
                nombre = self.estado.nombre or '---'
                tiempo = self.estado.tiempo_transcurrido()
                mins = int(tiempo // 60)
                secs = int(tiempo % 60)
                time_s = f"{mins:02d}:{secs:02d}"
                titulo_act = getattr(self.pantalla_actual, 'titulo', '')
                overlay_text = f"{nombre} — {titulo_act} — {time_s}"
                font = pygame.font.SysFont('Verdana', 18, bold=True)
                surf = font.render(overlay_text, True, (240,240,240))
                w_s, h_s = surf.get_size()
                w_win, h_win = self.pantalla.get_size()
                x = w_win - w_s - 20
                y = 18
                self.pantalla.blit(surf, (x, y))
        except Exception:
            pass

    def run(self):
        inicio = PantallaRegistro(self.pantalla, self.estado)
        corriendo = True

        while corriendo:
            ahora = pygame.time.get_ticks()
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    corriendo = False
                    break

                # route events based on mode; if game-over active, ignore per-screen events
                if self.modo == 'inicio':
                    resultado = inicio.handle_events(evento)
                    if resultado == 'siguiente':
                        nombre = inicio.input_text.strip()
                        self.estado.nombre = nombre
                        try:
                            self.estado.set_vidas(DEFAULT_LIVES)
                        except Exception:
                            self.estado.vidas = DEFAULT_LIVES
                        # start the cronómetro; it will be paused when entering rules
                        try:
                            self.estado.iniciar_cronometro()
                        except Exception:
                            pass
                        self.modo = 'flow'
                        self.seq_idx = 0
                        kind, idx = self.seq[self.seq_idx]
                        self.pantalla_actual = self._instantiate_screen_for(kind, idx)
                        if kind == 'rules':
                            try:
                                self.estado.hud_persistent = False
                            except Exception:
                                pass
                        else:
                            try:
                                self.pantalla_actual.estado = self.estado
                                self.estado.hud_persistent = True
                            except Exception:
                                pass
                    elif resultado == 'records':
                        self.estado.detener_cronometro()
                        self.pantalla_records = PantallaRecords(self.pantalla, self.estado)
                        self.modo = 'records'

                elif self.modo == 'flow' and self.pantalla_actual is not None:
                    if self.game_over_active:
                        resultado = None
                    else:
                        resultado = self.pantalla_actual.handle_events(evento)

                    if resultado == 'next':
                        self.seq_idx += 1
                        if self.seq_idx >= len(self.seq):
                            self.estado.detener_cronometro()
                            try:
                                if getattr(self.estado, 'vidas', 0) > 0 and not getattr(self.estado, 'record_saved', False):
                                    guardar_registro(self.estado.nombre or '---', self.estado.tiempo_transcurrido(), getattr(self.estado, 'avatar', None))
                                    self.estado.record_saved = True
                            except Exception:
                                pass
                            self.pantalla_records = PantallaRecords(self.pantalla, self.estado)
                            self.modo = 'records'
                            self.pantalla_actual = None
                        else:
                            kind, idx = self.seq[self.seq_idx]
                            self.pantalla_actual = self._instantiate_screen_for(kind, idx)
                            try:
                                self.pantalla_actual.estado = self.estado
                                self.estado.hud_persistent = (kind != 'rules')
                            except Exception:
                                pass
                            # pause timer for rules, resume for actual game play
                            try:
                                if kind == 'rules':
                                    self.estado.detener_cronometro()
                                else:
                                    self.estado.iniciar_cronometro()
                            except Exception:
                                pass

                elif self.modo == 'records' and self.pantalla_records is not None:
                    resultado = self.pantalla_records.handle_events(evento)
                    if resultado == 'replay':
                        self.pantalla_records = None
                        self.modo = 'inicio'
                        inicio.input_text = ''
                        self.estado.nombre = ''
                        self.estado.avatar = None
                        try:
                            self.estado.set_vidas(DEFAULT_LIVES)
                        except Exception:
                            self.estado.vidas = DEFAULT_LIVES
                        self.estado.record_saved = False
                        # reset cronómetro so it does not show stopped time on registro
                        try:
                            self.estado.cronometro_inicio = None
                            self.estado.cronometro_fin = None
                        except Exception:
                            pass
                        try:
                            self.estado.hud_persistent = False
                        except Exception:
                            pass

            # update/draw
            if self.modo == 'inicio':
                inicio.update()
                inicio.draw()
            elif self.modo == 'flow' and self.pantalla_actual is not None:
                self.pantalla_actual.update()
                self.pantalla_actual.draw()
            elif self.modo == 'records' and self.pantalla_records is not None:
                self.pantalla_records.update()
                self.pantalla_records.draw()
            else:
                self.pantalla.fill((18, 20, 24))

            # HUD persistente
            try:
                if getattr(self.estado, 'hud_persistent', False):
                    draw_persistent_hud(self.pantalla, self.estado, fallback_draw=lambda s, e: self._draw_persistent_hud_fallback())
            except Exception:
                pass

            # brightness overlay only (contrast and volume disabled)
            try:
                b = getattr(self.estado, 'brightness', 0.0)
                w, h = self.pantalla.get_size()
                if abs(b) > 0.001:
                    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                    max_alpha = 110
                    if b > 0:
                        scaled = (abs(b) ** 0.85)
                        alpha = int(min(1.0, b) * max_alpha * scaled)
                        overlay.fill((255, 255, 255, max(0, min(255, alpha))))
                    else:
                        scaled = (abs(b) ** 0.85)
                        alpha = int(min(1.0, -b) * max_alpha * scaled)
                        overlay.fill((0, 0, 0, max(0, min(255, alpha))))
                    self.pantalla.blit(overlay, (0, 0))
            except Exception:
                pass

            # hover/pointer visuals
            try:
                mx, my = pygame.mouse.get_pos()
                hovered_rect = None
                interactive_rects = []
                if self.modo == 'flow' and self.pantalla_actual is not None:
                    if hasattr(self.pantalla_actual, 'get_interactive_rects'):
                        try:
                            interactive_rects = self.pantalla_actual.get_interactive_rects() or []
                        except Exception:
                            interactive_rects = []
                    else:
                        for attr_name in ('back_rect', 'cont_rect', 'submit_rect', 'btn_rects'):
                            if hasattr(self.pantalla_actual, attr_name):
                                a = getattr(self.pantalla_actual, attr_name)
                                if isinstance(a, list):
                                    for r in a:
                                        if isinstance(r, pygame.Rect):
                                            interactive_rects.append(r)
                                elif isinstance(a, pygame.Rect):
                                    interactive_rects.append(a)

                for r in interactive_rects:
                    try:
                        if r.collidepoint((mx, my)):
                            hovered_rect = r
                            break
                    except Exception:
                        continue

                if hovered_rect is not None:
                    pulse = (math.sin(pygame.time.get_ticks() / 220.0) + 1.0) / 2.0
                    alpha = int(80 + pulse * 80)
                    pad = 8
                    ov_w = hovered_rect.w + pad * 2
                    ov_h = hovered_rect.h + pad * 2
                    overlay = pygame.Surface((ov_w, ov_h), pygame.SRCALPHA)
                    try:
                        pygame.draw.rect(overlay, (255, 255, 255, alpha), overlay.get_rect(), border_radius=min(20, ov_h//6))
                        pygame.draw.rect(overlay, (30, 30, 30, int(alpha*0.6)), overlay.get_rect(), 3, border_radius=min(20, ov_h//6))
                    except Exception:
                        overlay.fill((255, 255, 255, alpha))
                    self.pantalla.blit(overlay, (hovered_rect.x - pad, hovered_rect.y - pad))

                # draw custom pointer via helper
                draw_pointer(self.pantalla, self.puntero_img)
            except Exception:
                pass

            # start game-over if lives depleted
            try:
                if self.modo == 'flow' and not self.game_over_active and getattr(self.estado, 'vidas', 0) <= 0:
                    self.game_over_active = True
                    self.game_over_until = pygame.time.get_ticks() + 5000
                    try:
                        self.estado.detener_cronometro()
                    except Exception:
                        pass
            except Exception:
                pass

            # draw game-over modal
            if self.game_over_active:
                try:
                    w, h = self.pantalla.get_size()
                    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                    overlay.fill((6, 6, 8, 220))
                    self.pantalla.blit(overlay, (0, 0))
                    box_w = min(800, int(w * 0.84))
                    box_h = min(360, int(h * 0.44))
                    box_x = (w - box_w) // 2
                    box_y = (h - box_h) // 2
                    box = pygame.Rect(box_x, box_y, box_w, box_h)
                    pygame.draw.rect(self.pantalla, (28, 30, 34), box, border_radius=18)
                    pygame.draw.rect(self.pantalla, (200, 80, 80), box, 4, border_radius=18)
                    title_f = pygame.font.SysFont('Verdana', 36, bold=True)
                    title_s = title_f.render('Has perdido todas las vidas', True, (240, 240, 240))
                    self.pantalla.blit(title_s, (box_x + (box_w - title_s.get_width())//2, box_y + 28))
                    sub_f = pygame.font.SysFont('Verdana', 20)
                    remaining = max(0, int((self.game_over_until - pygame.time.get_ticks() + 999)//1000)) if self.game_over_until else 0
                    sub_s = sub_f.render(f'Redirigiendo al inicio en {remaining} s...', True, (220, 220, 220))
                    self.pantalla.blit(sub_s, (box_x + (box_w - sub_s.get_width())//2, box_y + 28 + title_s.get_height() + 18))
                except Exception:
                    pass

            pygame.display.flip()
            self.reloj.tick(self.fps)

            # auto-advance finalization
            try:
                if self.modo == 'flow' and self.pantalla_actual is not None and getattr(self.pantalla_actual, 'finished', False) and not getattr(self.pantalla_actual, 'saved_final', False):
                    try:
                        self.estado.detener_cronometro()
                        if getattr(self.estado, 'vidas', 0) > 0 and not getattr(self.estado, 'record_saved', False):
                            guardar_registro(self.estado.nombre or '---', self.estado.tiempo_transcurrido(), getattr(self.estado, 'avatar', None))
                            self.estado.record_saved = True
                    except Exception:
                        pass
                    self.pantalla_actual.saved_final = True
                    try:
                        self.pantalla_actual.auto_advance_until = pygame.time.get_ticks() + 5000
                    except Exception:
                        self.pantalla_actual.auto_advance_until = None

                if self.modo == 'flow' and self.pantalla_actual is not None and hasattr(self.pantalla_actual, 'auto_advance_until'):
                    if self.pantalla_actual.auto_advance_until and pygame.time.get_ticks() >= self.pantalla_actual.auto_advance_until:
                        self.seq_idx += 1
                        if self.seq_idx >= len(self.seq):
                            self.estado.detener_cronometro()
                            try:
                                if getattr(self.estado, 'vidas', 0) > 0 and not getattr(self.estado, 'record_saved', False):
                                    guardar_registro(self.estado.nombre or '---', self.estado.tiempo_transcurrido(), getattr(self.estado, 'avatar', None))
                                    self.estado.record_saved = True
                            except Exception:
                                pass
                            self.pantalla_records = PantallaRecords(self.pantalla, self.estado)
                            self.modo = 'records'
                            self.pantalla_actual = None
                        else:
                            kind, idx = self.seq[self.seq_idx]
                            self.pantalla_actual = self._instantiate_screen_for(kind, idx)
                            # ensure cronómetro paused/resumed appropriately
                            try:
                                if kind == 'rules':
                                    self.estado.detener_cronometro()
                                else:
                                    self.estado.iniciar_cronometro()
                            except Exception:
                                pass
            except Exception:
                pass

            # finalize game-over redirect
            try:
                if self.game_over_active and self.game_over_until and pygame.time.get_ticks() >= self.game_over_until:
                    self.game_over_active = False
                    self.game_over_until = None
                    self.pantalla_records = None
                    self.pantalla_actual = None
                    self.modo = 'inicio'
                    inicio.input_text = ''
                    self.estado.nombre = ''
                    self.estado.avatar = None
                    self.estado.record_saved = False
                    try:
                        self.estado.set_vidas(DEFAULT_LIVES)
                    except Exception:
                        self.estado.vidas = DEFAULT_LIVES
                    try:
                        self.estado.cronometro_inicio = None
                        self.estado.cronometro_fin = None
                    except Exception:
                        pass
            except Exception:
                pass

