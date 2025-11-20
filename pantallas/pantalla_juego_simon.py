import pygame
import random


class PantallaJuegoSimon:
    """Juego tipo Simon: reproducir la secuencia usando IMÁGENES (no colores).
    Se basa en la implementación de PatronMemoria del otro proyecto: carga
    imágenes de `assets/` y las muestra/animan durante la reproducción.
    """

    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 28, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 18)
        self.sequence = []
        self.player = []
        # playback state
        self.playing = False
        self.last_step_time = 0
        self.show_idx = 0
        # alert and timing
        self.alert = ''
        self.alert_until = 0
        # start delay before first pattern (ms)
        self.start_delay_ms = 3000
        self.start_at = pygame.time.get_ticks() + self.start_delay_ms
        self.waiting_to_start = True
        # after playback, show 'Tu turno' for 2000ms
        self.show_turn_until = 0
        self.player_allowed = False
        # finished state for final pattern
        self.finished = False
        self.final_alert = ''
        self.final_alert_until = 0
        self.images = []
        self.load_images()
        # start will be triggered after initial delay
        # level display (show 'Nivel N' before playback)
        self.current_level = 0
        self.level_show_until = 0
        # click feedback map: pad_index -> expiry_time (ms)
        self.click_feedback = {}

    def _add_color(self):
        # append new color and prepare to show level text before playback
        self.sequence.append(random.randrange(0, len(self.images) if self.images else 4))
        self.player = []
        # do not start immediate playback: first show level indicator
        self.playing = False
        self.last_step_time = 0
        self.show_idx = 0
        # set current level and show level text for 1.5s before playback
        self.current_level = len(self.sequence)
        self.level_show_until = pygame.time.get_ticks() + 1500

    def load_images(self):
        # try to load 4 images from assets; fallback to colored surfaces
        names = ["img1.png", "img2.png", "img3.png", "img4.png"]
        for n in names:
            try:
                img = pygame.image.load(f"assets/{n}")
                # keep original images; scaling will be done at draw-time preserving aspect
                self.images.append(img)
            except Exception:
                self.images.append(None)

    def handle_events(self, event):
        # accept player input only when allowed and not during playback
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.playing and self.player_allowed and not self.finished:
            w,h = self.screen.get_size()
            panel_w = int(w * 0.9)
            panel_h = int(h * 0.9)
            panel_x = (w - panel_w)//2
            panel_y = (h - panel_h)//2
            # pads in a 2x2 grid centered in panel
            pad_w = int(panel_w * 0.28)
            pad_h = int(panel_h * 0.28)
            start_x = panel_x + (panel_w - (pad_w*2 + 20))//2
            start_y = panel_y + 120
            mx,my = event.pos
            for i in range(4):
                cx = start_x + (i%2)*(pad_w + 20)
                cy = start_y + (i//2)*(pad_h + 20)
                rect = pygame.Rect(cx, cy, pad_w, pad_h)
                if rect.collidepoint((mx,my)):
                    # register short visual feedback for the click
                    try:
                        self.click_feedback[i] = pygame.time.get_ticks() + 220
                    except Exception:
                        pass
                    self.player.append(i)
                    # quick feedback: ensure we have a corresponding sequence element
                    idx = len(self.player) - 1
                    if idx < 0 or idx >= len(self.sequence):
                        # unexpected input (no sequence element) -> treat as error and reset
                        self.alert = 'Entrada inválida. Reiniciando nivel.'
                        self.alert_until = pygame.time.get_ticks() + 1200
                        self.sequence = []
                        self._add_color()
                        return None
                    if self.sequence[idx] != i:
                        # fail: reset sequence to start over
                        self.alert = 'Secuencia incorrecta. Reiniciando nivel.'
                        self.alert_until = pygame.time.get_ticks() + 1200
                        self.sequence = []
                        self._add_color()
                        # decrement a life on mistake if estado available
                        try:
                            if hasattr(self, 'estado') and getattr(self, 'estado') is not None:
                                try:
                                    self.estado.perder_vida(1)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        return None
                    else:
                        # correct so far
                        if len(self.player) == len(self.sequence):
                            # advance: require 8 rounds to finish (match VF behavior)
                            if len(self.sequence) >= 5:
                                # finished full game: show final success then Finalizar
                                self.finished = True
                                self.player_allowed = False
                                now = pygame.time.get_ticks()
                                self.final_alert = '¡Bien! Lo lograste'
                                self.final_alert_until = now + 3000
                            else:
                                # player completed this level (not final)
                                now = pygame.time.get_ticks()
                                # show 'Correcto' for ~3s then schedule next round
                                self.alert = '¡Correcto!'
                                self.alert_until = now + 3000
                                self.player_allowed = False
                                # schedule next round after alert finishes (small buffer)
                                try:
                                    pygame.time.set_timer(pygame.USEREVENT, 3100)
                                except Exception:
                                    pass
                    return None
        # handle scheduled USEREVENT to add next round (used as small delay)
        if event.type == pygame.USEREVENT:
            try:
                pygame.time.set_timer(pygame.USEREVENT, 0)
            except Exception:
                pass
            if not self.finished:
                self._add_color()
            return None
        # if finished, ignore further mouse clicks (auto-advance will handle transition)
        if self.finished and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return None
        return None

    def update(self):
        # play sequence with simple timing
        now = pygame.time.get_ticks()
        # Pause cronómetro during playback and resume when it's player's turn
        try:
            if hasattr(self, 'estado') and getattr(self, 'estado') is not None:
                if getattr(self, 'playing', False):
                    try:
                        self.estado.detener_cronometro()
                    except Exception:
                        pass
                # resume only when player is allowed (i.e., it's the player's turn)
                if getattr(self, 'player_allowed', False) and not getattr(self, 'playing', False):
                    try:
                        self.estado.iniciar_cronometro()
                    except Exception:
                        pass
                # while waiting_to_start or showing level text, ensure paused
                if getattr(self, 'waiting_to_start', False) or (getattr(self, 'level_show_until', 0) and now < getattr(self, 'level_show_until', 0)):
                    try:
                        self.estado.detener_cronometro()
                    except Exception:
                        pass
        except Exception:
            pass
        # handle initial start delay
        if self.waiting_to_start:
            if now >= self.start_at:
                self.waiting_to_start = False
                self._add_color()
            else:
                return
        # if level text is showing and time passed, start playback
        if self.level_show_until and not self.playing:
            if now >= self.level_show_until:
                # start playback
                self.playing = True
                self.last_step_time = now
                self.show_idx = 0
                self.show_phase = 'on'
                self.level_show_until = 0
        if self.playing:
            # playback per-item with explicit ON/OFF phases so repeats are perceptible
            # durations (ms)
            on_dur = 450
            base_off = 200
            # ensure show_phase exists
            if not hasattr(self, 'show_phase') or self.show_phase is None:
                self.show_phase = 'on'
                self.last_step_time = now
            if self.show_idx < len(self.sequence):
                if self.show_phase == 'on':
                    # stay lit for on_dur
                    if now - self.last_step_time >= on_dur:
                        self.show_phase = 'off'
                        self.last_step_time = now
                else:  # off phase
                    # if next element (after current) repeats same pad, increase off duration to make repeats clear
                    off_needed = base_off
                    if self.show_idx + 1 < len(self.sequence) and self.sequence[self.show_idx] == self.sequence[self.show_idx + 1]:
                        off_needed = 300
                    if now - self.last_step_time >= off_needed:
                        # advance to next item
                        self.show_idx += 1
                        # if advanced past last, finish playback
                        if self.show_idx >= len(self.sequence):
                            self.playing = False
                            self.show_idx = 0
                            self.show_phase = None
                            # playback finished; allow player input immediately
                            self.player_allowed = True
                            self.show_turn_until = 0
                        else:
                            # start next item's on-phase
                            self.show_phase = 'on'
                            self.last_step_time = now
            else:
                # safety: no items
                self.playing = False
                self.show_idx = 0
                self.show_phase = None

        if self.alert and now > self.alert_until:
            self.alert = ''
        # clean up expired click feedback entries
        for k, expiry in list(self.click_feedback.items()):
            if now > expiry:
                try:
                    del self.click_feedback[k]
                except Exception:
                    pass
        # enable player input after show_turn timeout
        if self.show_turn_until and now > self.show_turn_until and not self.finished:
            self.player_allowed = True
            self.show_turn_until = 0
        # final alert expiration handled to allow Finalizar button
        if self.final_alert and now > self.final_alert_until:
            self.final_alert = ''

    def draw(self):
        w,h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/area.jpg'), (w, h))
            self.screen.blit(bg, (0,0))
        except Exception:
            try:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
                self.screen.blit(bg, (0,0))
            except Exception:
                self.screen.fill((18,20,24))

        panel_w = int(w * 0.9)
        panel_h = int(h * 0.9)
        panel_x = (w - panel_w)//2
        panel_y = (h - panel_h)//2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # draw a rounded panel so corners are transparent and consistent with other screens
        try:
            pygame.draw.rect(panel_surf, (8,8,12,200), panel_surf.get_rect(), border_radius=18)
            pygame.draw.rect(panel_surf, (200,200,200), panel_surf.get_rect(), 3, border_radius=18)
            self.screen.blit(panel_surf, (panel_x, panel_y))
        except Exception:
            panel_surf.fill((8,8,12,200))
            self.screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3, border_radius=18)

        t = self.font_title.render(self.titulo, True, (240,240,240))
        self.screen.blit(t, (panel_x + 24, panel_y + 18))

        # instructional overlays: show level before playback, playback state, or player's turn
        now = pygame.time.get_ticks()
        instruct_text = None
        # waiting to start (initial countdown)
        if self.waiting_to_start:
            remaining = max(0, (self.start_at - now) // 1000)
            instruct_text = f"Comenzando en {remaining+1}s..."
        # show level label when level_show_until active
        elif self.current_level and self.level_show_until and now < self.level_show_until:
            instruct_text = f"Nivel {self.current_level}"
        elif self.playing:
            instruct_text = "Reproduciendo patrón..."
        elif self.player_allowed:
            instruct_text = "Tu turno: reproduce la secuencia"

        if instruct_text:
            info_font = pygame.font.SysFont('Verdana', 26, bold=True)
            info_s = info_font.render(instruct_text, True, (240,240,220))
            info_bg = pygame.Surface((info_s.get_width()+28, info_s.get_height()+14), pygame.SRCALPHA)
            pygame.draw.rect(info_bg, (30,30,30,220), info_bg.get_rect(), border_radius=12)
            self.screen.blit(info_bg, (panel_x + (panel_w - info_bg.get_width())//2, panel_y + 60))
            self.screen.blit(info_s, (panel_x + (panel_w - info_s.get_width())//2, panel_y + 66))

        # draw pads as images (if available) or fallback colored boxes
        pad_w = int(panel_w * 0.28)
        pad_h = int(panel_h * 0.28)
        start_x = panel_x + (panel_w - (pad_w*2 + 20))//2
        start_y = panel_y + 120
        for i in range(4):
            cx = start_x + (i%2)*(pad_w + 20)
            cy = start_y + (i//2)*(pad_h + 20)
            rect = pygame.Rect(cx, cy, pad_w, pad_h)
            img = None
            if i < len(self.images):
                img = self.images[i]
            # highlight while playing sequence: active when playback is in 'on' phase
            is_highlight = False
            if self.playing and hasattr(self, 'show_phase') and self.show_phase == 'on' and self.show_idx < len(self.sequence):
                try:
                    is_highlight = (i == self.sequence[self.show_idx])
                except Exception:
                    is_highlight = False
            if img:
                try:
                    iw, ih = img.get_size()
                    # target area slightly smaller than pad so images don't feel too wide
                    target_w = int((rect.w - 8) * 0.86)
                    target_h = int((rect.h - 8) * 0.86)
                    # compute scale preserving aspect
                    base_scale = min(target_w / iw, target_h / ih, 1.0)
                    # if highlighted during playback, apply a subtle scale-up for animation
                    if is_highlight:
                        scale = min(base_scale * 1.15, 1.6)
                    else:
                        scale = base_scale
                    new_w = max(1, int(iw * scale))
                    new_h = max(1, int(ih * scale))
                    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                except Exception:
                    try:
                        scaled = pygame.transform.scale(img, (max(1, target_w), max(1, target_h)))
                    except Exception:
                        scaled = None
                if scaled:
                    # center the (possibly scaled) image in the pad
                    img_x = rect.x + (rect.w - scaled.get_width()) // 2
                    img_y = rect.y + (rect.h - scaled.get_height()) // 2
                    # draw base pad background
                    pygame.draw.rect(self.screen, (30,30,30), rect, border_radius=16)
                    # if highlighted, add a subtle glow behind the image
                    if is_highlight:
                        glow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                        try:
                            pygame.draw.rect(glow, (255,255,200,50), glow.get_rect(), border_radius=16)
                        except Exception:
                            glow.fill((255,255,200,50))
                        self.screen.blit(glow, (rect.x, rect.y))
                    self.screen.blit(scaled, (img_x, img_y))
                    # click feedback overlay (short) - stronger than playback highlight
                    is_clicked = i in self.click_feedback and now < self.click_feedback.get(i, 0)
                    if is_highlight or is_clicked:
                        # overlay + brighter border (rounded)
                        overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                        try:
                            if is_clicked:
                                pygame.draw.rect(overlay, (255,255,255,140), overlay.get_rect(), border_radius=16)
                            else:
                                pygame.draw.rect(overlay, (255,255,255,80), overlay.get_rect(), border_radius=16)
                        except Exception:
                            if is_clicked:
                                overlay.fill((255,255,255,140))
                            else:
                                overlay.fill((255,255,255,80))
                        self.screen.blit(overlay, (rect.x, rect.y))
                        try:
                            border_col = (255, 215, 120) if not is_clicked else (255, 190, 80)
                            pygame.draw.rect(self.screen, border_col, rect, 6, border_radius=16)
                        except Exception:
                            pass
            else:
                # fallback colored boxes
                color = (200,50,50) if i==0 else (50,200,80) if i==1 else (50,120,220) if i==2 else (240,200,50)
                is_clicked = i in self.click_feedback and now < self.click_feedback.get(i, 0)
                if is_clicked:
                    bright = tuple(min(255, int(c*1.25)) for c in color)
                    pygame.draw.rect(self.screen, bright, rect, border_radius=16)
                    # overlay to indicate click
                    ov = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    ov.fill((255,255,255,100))
                    self.screen.blit(ov, (rect.x, rect.y))
                elif is_highlight:
                    bright = tuple(min(255, int(c*1.3)) for c in color)
                    pygame.draw.rect(self.screen, bright, rect, border_radius=16)
                else:
                    pygame.draw.rect(self.screen, color, rect, border_radius=16)

        # transient alert while playing/advancing; suppress when finished modal is shown
        if self.alert and not getattr(self, 'finished', False):
            a = self.font_text.render(self.alert, True, (255,200,80))
            self.screen.blit(a, (panel_x + 30, panel_y + panel_h - 100))

        # When the required rounds are finished and player has completed them, show a big modal
        # with a clear 'Juego completado' message and a visible countdown using auto_advance_until.
        if getattr(self, 'finished', False):
            now = pygame.time.get_ticks()
            # modal background
            overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            overlay.fill((8,8,12,200))
            self.screen.blit(overlay, (panel_x, panel_y))
            # centered box
            box_w = int(panel_w * 0.7)
            box_h = int(panel_h * 0.4)
            box_x = panel_x + (panel_w - box_w)//2
            box_y = panel_y + (panel_h - box_h)//2
            box = pygame.Rect(box_x, box_y, box_w, box_h)
            pygame.draw.rect(self.screen, (30,30,36), box, border_radius=18)
            pygame.draw.rect(self.screen, (240,200,80), box, 4, border_radius=18)
            # big title
            bigf = pygame.font.SysFont('Verdana', 36, bold=True)
            title = bigf.render('¡Juego completado!', True, (240,240,240))
            self.screen.blit(title, (box_x + (box_w - title.get_width())//2, box_y + 28))
            # subtitle / final alert (if any)
            subf = pygame.font.SysFont('Verdana', 22)
            sub = self.final_alert or '¡Lo lograste!' 
            sub_s = subf.render(sub, True, (220,220,200))
            self.screen.blit(sub_s, (box_x + (box_w - sub_s.get_width())//2, box_y + 28 + title.get_height() + 12))
            # countdown (use auto_advance_until if set)
            adv_until = getattr(self, 'auto_advance_until', 0)
            if adv_until and adv_until > now:
                remaining = max(0, int((adv_until - now + 999)//1000))
                cntf = pygame.font.SysFont('Verdana', 28, bold=True)
                cnts = cntf.render(f'Redirigiendo a records en {remaining}', True, (200,200,200))
                self.screen.blit(cnts, (box_x + (box_w - cnts.get_width())//2, box_y + box_h - 68))
            else:
                cntf = pygame.font.SysFont('Verdana', 22)
                cnts = cntf.render('Preparando registros...', True, (180,180,180))
                self.screen.blit(cnts, (box_x + (box_w - cnts.get_width())//2, box_y + box_h - 68))
