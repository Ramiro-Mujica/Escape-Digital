import pygame
from core.audio import get_audio

# Toggle this to True to print debug info about menu hit-testing and events
# During normal gameplay keep this False to avoid terminal output.
DEBUG_MENU = False


class PantallaInicio:
    """Pantalla de inicio minimal: input de nombre, boton Aceptar y control de musica (play/pause).
    Incluye un botón de configuración (engranaje) que abre un menú con opciones.
    """
    def __init__(self, screen, estado):
        self.screen = screen
        self.estado = estado
        self.input_text = ""
        self.active = True
        self.max_len = 20
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500

        self.negro = (0, 0, 0)
        self.blanco = (255, 255, 255)
        self.rojo = (200, 30, 30)
        self.gris_claro = (230, 230, 230)

        self.titulo_font = pygame.font.SysFont("Verdana", 40, bold=True)
        self.text_font = pygame.font.SysFont("Verdana", 28)
        # botones
        self.btn_size = 36
        # botón play/pause (izquierda)
        self.btn_rect = pygame.Rect(20, 20, self.btn_size, self.btn_size)
        # botón engranaje (config) arriba-derecha
        self.gear_rect = pygame.Rect(0, 0, 34, 34)
        self.accept_width = 180
        self.accept_height = 48
        self.accept_rect = pygame.Rect(0, 0, self.accept_width, self.accept_height)

        # audio manager
        self.audio = get_audio()
        try:
            # iniciar la música de menú automáticamente
            self.audio.play_music(loop=True)
        except Exception:
            pass
        # menu de configuración cerrado por defecto
        self.menu_open = False
        self.menu_view = 'options'  # 'options' | 'pantalla' | 'nosotros'
        # interactive menu state
        self.menu_scroll = 0
        # simplified menu: Pantalla -> opens sliders; Records -> navigates out; Nosotros -> info; Atras -> close menu
        self.menu_items = ['Pantalla', 'Records', 'Nosotros', 'Atras']
        self.menu_item_height = 54
        self.menu_dragging_slider = None  # 'brightness' | 'contrast' | None
        self.menu_dragging = False
        self.menu_hover = -1
        self.menu_pressed = -1
        # small animation timers per menu item (frames)
        self._button_anims = [0 for _ in self.menu_items]

    def handle_events(self, event):
        # route ongoing mouse events to the menu handler when the menu is open
        if self.menu_open and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
            handled = self._menu_handle_event(event)
            if handled:
                return handled

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # click en boton play/pause
            if self.btn_rect.collidepoint(event.pos):
                # Toggle play / pause of background music
                try:
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        self.audio.stop_music()
                    else:
                        self.audio.play_music(loop=True)
                except Exception:
                    pass
                return None
            # click en engranaje (abrir/cerrar menu)
            # posicionar gear rect en la esquina superior derecha antes de check
            w, h = self.screen.get_size()
            self.gear_rect.topright = (w - 18, 18)
            if self.gear_rect.collidepoint(event.pos):
                self.menu_open = not self.menu_open
                # reset view
                self.menu_view = 'options'
                if DEBUG_MENU:
                    print(f"[MENU] gear clicked -> menu_open={self.menu_open}")
                return None
            # si el menu está abierto, dejar que su propio handler lo consuma
            if self.menu_open:
                # route full event object to menu handler for richer interactions
                handled = self._menu_handle_event(event)
                if handled:
                    return handled
                return None
            if self.accept_rect.collidepoint(event.pos):
                nombre = self.input_text.strip()
                if nombre:
                    return 'siguiente'

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                nombre = self.input_text.strip()
                if nombre:
                    return 'siguiente'
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if len(self.input_text) < self.max_len and event.unicode.isprintable():
                    self.input_text += event.unicode
        return None

    def _handle_menu_click(self, pos):
        return None

    def _menu_handle_event(self, event):
        """Maneja eventos más ricos del menú: scroll, hover, click, drag sliders.
        Devuelve 'records' si la acción solicita navegar fuera, o None.
        """
        w, h = self.screen.get_size()
        menu_w = 520
        menu_h = 420
        menu_x = (w - menu_w) // 2
        menu_y = (h - menu_h) // 2

    # geometry for items (different layouts depending on subview)
        btn_h = 44
        # options list layout
        opts_y_base = menu_y + 120
        opts_spacing = btn_h + 12

        def item_rect(i):
            if self.menu_view == 'options':
                y = opts_y_base + i * opts_spacing
                return pygame.Rect(menu_x + 20, y, menu_w - 40, btn_h)
            else:
                # fallback (not used for now)
                y = menu_y + 160 + i * (btn_h + 10) - self.menu_scroll
                return pygame.Rect(menu_x + 20, y, menu_w - 40, btn_h)

    # compute exact hit-rects matching what _draw_menu paints for current view
        if self.menu_view == 'options':
            menu_rects = [pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), menu_w - 40, btn_h) for i in range(len(self.menu_items))]
            b_track = None
            c_track = None
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, menu_w - 40, btn_h)
        elif self.menu_view == 'pantalla':
            menu_rects = [pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), menu_w - 40, btn_h) for i in range(len(self.menu_items))]
            # compute same geometry as _draw_menu: label positions and track sizes
            label_y = menu_y + 86
            label_h = self.text_font.get_height()
            track_x = menu_x + 160
            track_w = max(160, menu_w - 340)
            b_track_y = label_y + label_h + 8
            b_track = pygame.Rect(track_x, b_track_y, track_w, 12)
            c_track_y = b_track_y + 12 + 18
            c_track = pygame.Rect(track_x, c_track_y, track_w, 12)
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, menu_w - 40, btn_h)
        else:  # 'nosotros' and fallback
            menu_rects = [pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), menu_w - 40, btn_h) for i in range(len(self.menu_items))]
            b_track = None
            c_track = None
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, menu_w - 40, btn_h)

        # clamp helper for scroll (not used in simplified options, keep zero)
        total_items_h = len(self.menu_items) * (btn_h + 10)
        max_scroll = 0

        # debug logging removed: no terminal output during gameplay

        if event.type == pygame.MOUSEWHEEL:
            return None
        # older wheel support
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if event.button == 4:
                self.menu_scroll = max(0, self.menu_scroll - 40)
            else:
                self.menu_scroll = min(max_scroll, self.menu_scroll + 40)
            return None

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            # update hover index (only for options list)
            new_hover = -1
            for i, r in enumerate(menu_rects):
                if r.collidepoint((mx, my)):
                    new_hover = i
                    break
            self.menu_hover = new_hover
            # if dragging a slider, update value
            if self.menu_dragging_slider is not None and self.menu_dragging:
                if self.menu_dragging_slider == 'brightness':
                    rel = (mx - b_track.x) / b_track.w
                    val = -1.0 + rel * 2.0
                    self.estado.set_brightness(max(-1.0, min(1.0, val)))
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] drag brightness -> {self.estado.brightness:.2f}")
                        except Exception:
                            print("[MENU] drag brightness")
                elif self.menu_dragging_slider == 'contrast':
                    rel = (mx - c_track.x) / c_track.w
                    val = 0.5 + rel * 1.0
                    self.estado.set_contrast(max(0.5, min(1.5, val)))
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] drag contrast -> {self.estado.contrast:.2f}")
                        except Exception:
                            print("[MENU] drag contrast")
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # prefer using last-drawn geometry when available (more accurate hit-testing)
            if hasattr(self, '_last_b_track') and self._last_b_track is not None:
                b_track = self._last_b_track
            if hasattr(self, '_last_c_track') and self._last_c_track is not None:
                c_track = self._last_c_track
            if hasattr(self, '_last_back_rect') and self._last_back_rect is not None:
                back_rect = self._last_back_rect
            # check minus/plus rectangles (only relevant in pantalla view)
            if b_track is not None:
                # match draw() geometry: minus/plus are slightly wider and shorter
                minus_rect = pygame.Rect(b_track.x - 44, b_track.y - 6, 36, 28)
                plus_rect = pygame.Rect(b_track.x + b_track.w + 8, b_track.y - 6, 36, 28)
                # create slightly larger hitboxes for more tolerant clicks
                minus_hit = minus_rect.inflate(12, 12)
                plus_hit = plus_rect.inflate(12, 12)
            else:
                minus_rect = pygame.Rect(0, 0, 0, 0)
                plus_rect = pygame.Rect(0, 0, 0, 0)
            if c_track is not None:
                c_minus = pygame.Rect(c_track.x - 44, c_track.y - 6, 36, 28)
                c_plus = pygame.Rect(c_track.x + c_track.w + 8, c_track.y - 6, 36, 28)
                c_minus_hit = c_minus.inflate(12, 12)
                c_plus_hit = c_plus.inflate(12, 12)
            else:
                c_minus = pygame.Rect(0, 0, 0, 0)
                c_plus = pygame.Rect(0, 0, 0, 0)
            if self.menu_view == 'pantalla':
                # use expanded hitboxes for better UX
                if 'minus_hit' in locals() and minus_hit.collidepoint((mx, my)):
                    self.estado.set_brightness(self.estado.brightness - 0.1)
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] brightness dec -> {self.estado.brightness:.2f}")
                        except Exception:
                            print("[MENU] brightness dec")
                    return None
                if 'plus_hit' in locals() and plus_hit.collidepoint((mx, my)):
                    self.estado.set_brightness(self.estado.brightness + 0.1)
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] brightness inc -> {self.estado.brightness:.2f}")
                        except Exception:
                            print("[MENU] brightness inc")
                    return None
                if 'c_minus_hit' in locals() and c_minus_hit.collidepoint((mx, my)):
                    self.estado.set_contrast(self.estado.contrast - 0.05)
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] contrast dec -> {self.estado.contrast:.2f}")
                        except Exception:
                            print("[MENU] contrast dec")
                    return None
                if 'c_plus_hit' in locals() and c_plus_hit.collidepoint((mx, my)):
                    self.estado.set_contrast(self.estado.contrast + 0.05)
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] contrast inc -> {self.estado.contrast:.2f}")
                        except Exception:
                            print("[MENU] contrast inc")
                    return None

            # check if clicked on slider knob area (start dragging) - only for pantalla view
            if self.menu_view == 'pantalla':
                # compute knob rects matching draw() geometry
                # if we stored the last knob rects while drawing, prefer those
                b_knob_rect = getattr(self, '_last_b_knob', None)
                c_knob_rect = getattr(self, '_last_c_knob', None)
                if b_knob_rect is None:
                    try:
                        bv = max(-1.0, min(1.0, self.estado.brightness))
                        b_bx = int(b_track.x + ((bv + 1.0) / 2.0) * b_track.w)
                        b_knob_rect = pygame.Rect(b_bx - 12, b_track.y + b_track.h//2 - 12, 24, 24)
                    except Exception:
                        b_knob_rect = None
                if c_knob_rect is None:
                    try:
                        cv = max(0.5, min(1.5, self.estado.contrast))
                        c_cx = int(c_track.x + ((cv - 0.5) / 1.0) * c_track.w)
                        c_knob_rect = pygame.Rect(c_cx - 12, c_track.y + c_track.h//2 - 12, 24, 24)
                    except Exception:
                        c_knob_rect = None

                if (b_knob_rect and b_knob_rect.collidepoint((mx, my))) or (b_track and b_track.collidepoint((mx, my))):
                    self.menu_dragging_slider = 'brightness'
                    self.menu_dragging = True
                    # defensive: clear any previously stored press state so a
                    # leftover menu press doesn't fire when we release after dragging
                    try:
                        self.menu_pressed = -1
                        self._menu_press_rect = None
                    except Exception:
                        pass
                    rel = (mx - b_track.x) / b_track.w
                    val = -1.0 + rel * 2.0
                    self.estado.set_brightness(max(-1.0, min(1.0, val)))
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] start drag brightness -> {self.estado.brightness:.2f}")
                        except Exception:
                            print("[MENU] start drag brightness")
                    return None

                if (c_knob_rect and c_knob_rect.collidepoint((mx, my))) or (c_track and c_track.collidepoint((mx, my))):
                    self.menu_dragging_slider = 'contrast'
                    self.menu_dragging = True
                    # defensive: clear any previously stored press state so a
                    # leftover menu press doesn't fire when we release after dragging
                    try:
                        self.menu_pressed = -1
                        self._menu_press_rect = None
                    except Exception:
                        pass
                    rel = (mx - c_track.x) / c_track.w
                    val = 0.5 + rel * 1.0
                    self.estado.set_contrast(max(0.5, min(1.5, val)))
                    if DEBUG_MENU:
                        try:
                            print(f"[MENU] start drag contrast -> {self.estado.contrast:.2f}")
                        except Exception:
                            print("[MENU] start drag contrast")
                    return None

            # check clicks on items (options list) - only when viewing options
            if self.menu_view == 'options':
                for i, r in enumerate(menu_rects):
                    if r.collidepoint((mx, my)):
                        self.menu_pressed = i
                        # store the exact rect instance we pressed so we can test the same
                        # geometry on mouse-up (avoids mismatches between draw and
                        # recomputed geometry). Use a copy to avoid later mutation.
                        try:
                            self._menu_press_rect = pygame.Rect(r)
                        except Exception:
                            self._menu_press_rect = None
                        if DEBUG_MENU:
                            try:
                                lab = self.menu_items[i] if i < len(self.menu_items) else str(i)
                                print(f"[MENU] pressed idx={i} lab={lab} rect={self._menu_press_rect}")
                            except Exception:
                                print(f"[MENU] pressed idx={i}")
                        return None

            # back button
            if back_rect.collidepoint((mx, my)):
                # In any subview, this returns to options; if already on options, close menu
                if self.menu_view != 'options':
                    self.menu_view = 'options'
                else:
                    self.menu_open = False
                return None

            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos
            # stop any dragging
            if self.menu_dragging:
                self.menu_dragging = False
                self.menu_dragging_slider = None
                if DEBUG_MENU:
                    print(f"[MENU] stop dragging")
                return None

            # if we had a pressed index, check if release inside same item => activate
            if self.menu_pressed != -1:
                idx = self.menu_pressed
                # clear pressed state now (we will activate based on stored rect)
                self.menu_pressed = -1
                r = None
                # prefer the exact rect we recorded on mouse-down, fall back to recomputed
                if hasattr(self, '_menu_press_rect') and self._menu_press_rect is not None:
                    r = self._menu_press_rect
                else:
                    try:
                        r = item_rect(idx)
                    except Exception:
                        r = None
                # clear stored press rect
                self._menu_press_rect = None
                if r is not None and r.collidepoint((mx, my)):
                    lab = self.menu_items[idx]
                    # start a short click animation for feedback
                    try:
                        self._button_anims[idx] = 12
                    except Exception:
                        pass
                    if lab == 'Records':
                        self.menu_open = False
                        if DEBUG_MENU:
                            print(f"[MENU] activate Records -> navigate out")
                        return 'records'
                    elif lab == 'Pantalla':
                        self.menu_view = 'pantalla'
                        if DEBUG_MENU:
                            print(f"[MENU] activate Pantalla -> submenu")
                        return None
                    elif lab == 'Nosotros':
                        self.menu_view = 'nosotros'
                        if DEBUG_MENU:
                            print(f"[MENU] activate Nosotros -> submenu")
                        return None
                    elif lab == 'Atras':
                        # exit config menu back to registration
                        self.menu_open = False
                        if DEBUG_MENU:
                            print(f"[MENU] activate Atras -> menu_closed")
                        return None
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_scroll = max(0, self.menu_scroll - 40)
                return None
            elif event.key == pygame.K_DOWN:
                self.menu_scroll = min(max_scroll, self.menu_scroll + 40)
                return None
        return None

    def _wrap_text(self, text, font, max_width):
        """Simple word-wrap that returns a list of lines fitting within max_width."""
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            test = cur + (' ' if cur else '') + w
            try:
                tw = font.size(test)[0]
            except Exception:
                tw = len(test) * 8
            if tw <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _draw_menu(self):
        w, h = self.screen.get_size()
        menu_w = min(520, max(280, w - 40))
        menu_h = 420
        menu_x = (w - menu_w) // 2
        menu_y = (h - menu_h) // 2

        # background overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # panel
        panel = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
        pygame.draw.rect(self.screen, (250,250,250), panel, border_radius=12)
        pygame.draw.rect(self.screen, self.rojo, panel, 3, border_radius=12)

        title = self.titulo_font.render('Opciones', True, (0,0,0))
        self.screen.blit(title, (menu_x + 20, menu_y + 12))

        # draw according to current subview
        btn_w = menu_w - 40
        btn_h = 44
        if self.menu_view == 'options':
            # Draw options list with gradient-styled buttons and hover/click feedback
            menu_rects = []
            for i, lab in enumerate(self.menu_items):
                r = pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), btn_w, btn_h)
                menu_rects.append(r)
                # gradient background for button
                grad = pygame.Surface((r.w, r.h))
                for yy in range(r.h):
                    t = yy / r.h
                    color = (int(245 - 60 * t), int(245 - 80 * t), int(245 - 100 * t))
                    pygame.draw.line(grad, color, (0, yy), (r.w, yy))
                grad.set_alpha(255)
                self.screen.blit(grad, (r.x, r.y))
                # border with hover/anim feedback
                border_color = (160, 30, 30)
                border_w = 2
                if self.menu_hover == i:
                    border_color = (200, 50, 50)
                    border_w = 3
                if hasattr(self, '_button_anims') and self._button_anims and self._button_anims[i] > 0:
                    border_color = (255, 100, 100)
                    border_w = 4
                pygame.draw.rect(self.screen, border_color, r, border_w, border_radius=8)
                txt = self.text_font.render(lab, True, (20,20,20))
                self.screen.blit(txt, (r.x + 16, r.y + (r.h - txt.get_height())//2))
            # store last-drawn rects for event handling
            self._last_menu_rects = menu_rects
            self._last_b_track = None
            self._last_c_track = None
            self._last_back_rect = None
            # no per-frame debug output here
        elif self.menu_view == 'pantalla':
            # Draw sliders and a back button to options
            # We'll draw a visible track (bar) with a filled portion and a knob,
            # plus clear +/- buttons to the sides. Spacing improved so they don't overlap.
            label = self.text_font.render('Brillo:', True, (20,20,20))
            # compute dynamic vertical positions to avoid overlap
            label_y = menu_y + 86
            label_h = self.text_font.get_height()
            self.screen.blit(label, (menu_x + 40, label_y))

            # compute track geometry responsive to menu width
            track_x = menu_x + 160
            track_w = max(160, menu_w - 340)
            b_track_y = label_y + label_h + 8
            b_track = pygame.Rect(track_x, b_track_y, track_w, 12)

            # draw track background
            pygame.draw.rect(self.screen, (220,220,220), b_track, border_radius=6)
            # draw filled portion for current brightness
            bv = max(-1.0, min(1.0, self.estado.brightness))
            rel_b = (bv + 1.0) / 2.0
            filled_w = int(rel_b * b_track.w)
            if filled_w > 0:
                pygame.draw.rect(self.screen, (200,50,50), (b_track.x, b_track.y, filled_w, b_track.h), border_radius=6)
            # draw knob
            bx = b_track.x + filled_w
            # knob rect (slightly larger hit area / visual)
            knob_r = 12
            knob_rect = pygame.Rect(int(bx - knob_r), int(b_track.y + b_track.h//2 - knob_r), knob_r*2, knob_r*2)
            # hover/pressed visuals
            mx,my = pygame.mouse.get_pos()
            outer_color = (255,255,255)
            inner_color = (150,30,30)
            if hasattr(self, 'menu_dragging_slider') and self.menu_dragging_slider == 'brightness' and self.menu_dragging:
                outer_color = (255,240,240)
                inner_color = (220,60,60)
            elif knob_rect.collidepoint((mx,my)):
                outer_color = (250,250,250)
            pygame.draw.circle(self.screen, outer_color, (bx, b_track.y + b_track.h//2), knob_r)
            pygame.draw.circle(self.screen, inner_color, (bx, b_track.y + b_track.h//2), 6)
            # plus/minus buttons
            minus_rect = pygame.Rect(b_track.x - 44, b_track.y - 6, 36, 28)
            plus_rect = pygame.Rect(b_track.x + b_track.w + 8, b_track.y - 6, 36, 28)
            pygame.draw.rect(self.screen, (245,245,245), minus_rect, border_radius=6)
            pygame.draw.rect(self.screen, (245,245,245), plus_rect, border_radius=6)
            pygame.draw.rect(self.screen, (160,160,160), minus_rect, 2, border_radius=6)
            pygame.draw.rect(self.screen, (160,160,160), plus_rect, 2, border_radius=6)
            # center the +/- signs
            minus_s = self.text_font.render('-', True, (20,20,20))
            plus_s = self.text_font.render('+', True, (20,20,20))
            # hover visual
            mx,my = pygame.mouse.get_pos()
            if minus_rect.collidepoint((mx,my)):
                pygame.draw.rect(self.screen, (230,230,230), minus_rect, border_radius=6)
            if plus_rect.collidepoint((mx,my)):
                pygame.draw.rect(self.screen, (230,230,230), plus_rect, border_radius=6)
            self.screen.blit(minus_s, (minus_rect.x + (minus_rect.w - minus_s.get_width())//2, minus_rect.y + (minus_rect.h - minus_s.get_height())//2))
            self.screen.blit(plus_s, (plus_rect.x + (plus_rect.w - plus_s.get_width())//2, plus_rect.y + (plus_rect.h - plus_s.get_height())//2))
            # store knob rect for event handling
            self._last_b_knob = knob_rect
            # show brightness percent
            # vertical center for percent/value
            pct_y = b_track.y + (b_track.h - self.text_font.get_height()) // 2
            self.screen.blit(self.text_font.render(f"{int(rel_b*100)}%", True, (20,20,20)), (b_track.x + b_track.w + 56, pct_y))

            # Contraste (separado verticalmente)
            label2 = self.text_font.render('Contraste:', True, (20,20,20))
            # place contrast below brightness with spacing
            c_label_y = b_track.y + b_track.h + 18
            self.screen.blit(label2, (menu_x + 40, c_label_y))
            c_track_y = c_label_y + label_h + 8
            c_track = pygame.Rect(track_x, c_track_y, track_w, 12)
            pygame.draw.rect(self.screen, (220,220,220), c_track, border_radius=6)
            cv = max(0.5, min(1.5, self.estado.contrast))
            rel_c = (cv - 0.5) / 1.0
            filled_c = int(rel_c * c_track.w)
            if filled_c > 0:
                pygame.draw.rect(self.screen, (200,50,50), (c_track.x, c_track.y, filled_c, c_track.h), border_radius=6)
            cx = c_track.x + filled_c
            c_knob_r = 12
            c_knob_rect = pygame.Rect(int(cx - c_knob_r), int(c_track.y + c_track.h//2 - c_knob_r), c_knob_r*2, c_knob_r*2)
            outer_c = (255,255,255)
            inner_c = (150,30,30)
            if hasattr(self, 'menu_dragging_slider') and self.menu_dragging_slider == 'contrast' and self.menu_dragging:
                outer_c = (255,240,240)
                inner_c = (220,60,60)
            elif c_knob_rect.collidepoint((mx,my)):
                outer_c = (250,250,250)
            pygame.draw.circle(self.screen, outer_c, (cx, c_track.y + c_track.h//2), c_knob_r)
            pygame.draw.circle(self.screen, inner_c, (cx, c_track.y + c_track.h//2), 6)
            c_minus = pygame.Rect(c_track.x - 44, c_track.y - 6, 36, 28)
            c_plus = pygame.Rect(c_track.x + c_track.w + 8, c_track.y - 6, 36, 28)
            pygame.draw.rect(self.screen, (245,245,245), c_minus, border_radius=6)
            pygame.draw.rect(self.screen, (245,245,245), c_plus, border_radius=6)
            pygame.draw.rect(self.screen, (160,160,160), c_minus, 2, border_radius=6)
            pygame.draw.rect(self.screen, (160,160,160), c_plus, 2, border_radius=6)
            c_minus_s = self.text_font.render('-', True, (20,20,20))
            c_plus_s = self.text_font.render('+', True, (20,20,20))
            # hover visual
            if c_minus.collidepoint((mx,my)):
                pygame.draw.rect(self.screen, (230,230,230), c_minus, border_radius=6)
            if c_plus.collidepoint((mx,my)):
                pygame.draw.rect(self.screen, (230,230,230), c_plus, border_radius=6)
            self.screen.blit(c_minus_s, (c_minus.x + (c_minus.w - c_minus_s.get_width())//2, c_minus.y + (c_minus.h - c_minus_s.get_height())//2))
            self.screen.blit(c_plus_s, (c_plus.x + (c_plus.w - c_plus_s.get_width())//2, c_plus.y + (c_plus.h - c_plus_s.get_height())//2))
            # store knob rect
            self._last_c_knob = c_knob_rect
            pct_c_y = c_track.y + (c_track.h - self.text_font.get_height()) // 2
            self.screen.blit(self.text_font.render(f"{cv:.2f}", True, (20,20,20)), (c_track.x + c_track.w + 56, pct_c_y))

            # back to options
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, btn_w, btn_h)
            pygame.draw.rect(self.screen, (240,240,240), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, (160,160,160), back_rect, 2, border_radius=8)
            back_txt = self.text_font.render('Volver a opciones', True, (20,20,20))
            self.screen.blit(back_txt, (back_rect.x + 12, back_rect.y + 8))
            # store last-drawn rects for event handling
            self._last_b_track = b_track
            self._last_c_track = c_track
            # also store +/- rects so clicks map correctly in event handler logic expectations
            self._last_b_minus = minus_rect
            self._last_b_plus = plus_rect
            self._last_c_minus = c_minus
            self._last_c_plus = c_plus
            self._last_back_rect = back_rect
            self._last_menu_rects = [pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), btn_w, btn_h) for i in range(len(self.menu_items))]
            # (debug drawing info removed to avoid per-frame console spam)
        elif self.menu_view == 'nosotros':
            # company/about text - wrap to fit panel
            lines = [
                'Somos Tejo Imaginar - desarrolladores de juegos.',
                'Creamos experiencias de escape room y minijuegos educativos.'
            ]
            full = ' '.join(lines)
            wrapped = self._wrap_text(full, self.text_font, btn_w - 24)
            y0 = menu_y + 90
            lh = self.text_font.get_height() + 6
            max_h = menu_h - 140
            for i, ln in enumerate(wrapped):
                if i * lh > max_h:
                    break
                t = self.text_font.render(ln, True, (20,20,20))
                self.screen.blit(t, (menu_x + 24, y0 + i * lh))
            # volver a opciones
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, btn_w, btn_h)
            pygame.draw.rect(self.screen, (240,240,240), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, (160,160,160), back_rect, 2, border_radius=8)
            back_txt = self.text_font.render('Volver a opciones', True, (20,20,20))
            self.screen.blit(back_txt, (back_rect.x + 12, back_rect.y + 8))
            # store last-drawn rects for event handling
            self._last_b_track = None
            self._last_c_track = None
            self._last_back_rect = back_rect
            self._last_menu_rects = [pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), btn_w, btn_h) for i in range(len(self.menu_items))]
            # (debug drawing info removed to avoid per-frame console spam)

    def update(self):
        ahora = pygame.time.get_ticks()
        if ahora - self.cursor_timer > self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = ahora
        # decrement any active button animations
        if hasattr(self, '_button_anims') and self._button_anims:
            for i in range(len(self._button_anims)):
                if self._button_anims[i] > 0:
                    self._button_anims[i] -= 1

    def draw(self):
        w, h = self.screen.get_size()
        # dibujar fondo desde assets si existe
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
            self.screen.blit(bg, (0, 0))
        except Exception:
            self.screen.fill((20, 24, 30))

        # Título
        sombra = self.titulo_font.render('Registro de jugador', True, (0,0,0))
        texto = self.titulo_font.render('Registro de jugador', True, self.blanco)
        self.screen.blit(sombra, ((w - sombra.get_width())//2 + 2, 60 + 2))
        self.screen.blit(texto, ((w - texto.get_width())//2, 60))

        # Caja de entrada
        padding_x = 24
        padding_y = 14
        texto_surface = self.text_font.render(self.input_text if self.input_text else 'Escribí tu nombre...', True, self.negro if self.input_text else (120,120,120))
        box_width = max(400, texto_surface.get_width() + padding_x * 2)
        box_height = texto_surface.get_height() + padding_y * 2
        box_x = (w - box_width) // 2
        box_y = (h - box_height) // 2

        caja_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(caja_surf, self.gris_claro, caja_surf.get_rect(), border_radius=18)
        pygame.draw.rect(caja_surf, self.rojo, caja_surf.get_rect(), 3, border_radius=18)
        self.screen.blit(caja_surf, (box_x, box_y))

        text_x = box_x + padding_x
        text_y = box_y + padding_y
        if self.input_text:
            rojo_text = self.text_font.render(self.input_text, True, self.rojo)
            offsets = [(-1,0),(1,0),(0,-1),(0,1)]
            for dx, dy in offsets:
                self.screen.blit(rojo_text, (text_x + dx, text_y + dy))
            negro_text = self.text_font.render(self.input_text, True, self.negro)
            self.screen.blit(negro_text, (text_x, text_y))
        else:
            placeholder = self.text_font.render('Escribí tu nombre...', True, (120,120,120))
            self.screen.blit(placeholder, (text_x, text_y))

        # cursor
        if self.cursor_visible and self.active:
            if self.input_text:
                last_w = self.text_font.render(self.input_text, True, self.negro).get_width()
            else:
                last_w = 0
            cursor_x = text_x + last_w + 4
            cursor_y = text_y
            cursor_h = self.text_font.get_height()
            pygame.draw.rect(self.screen, self.negro, (cursor_x, cursor_y, 3, cursor_h))

        # boton mute
        pygame.draw.rect(self.screen, (245,245,245), self.btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.rojo, self.btn_rect, 2, border_radius=10)
        cx = self.btn_rect.centerx
        cy = self.btn_rect.centery
        # Dibujar icono play/pause segun si la musica esta reproduciendo
        try:
            playing = pygame.mixer.get_init() and pygame.mixer.music.get_busy()
        except Exception:
            playing = False
        icon_color = self.rojo if playing else (120,120,120)
        if playing:
            # dibujar icono 'pause' (dos rectangulos)
            pygame.draw.rect(self.screen, icon_color, (cx-6, cy-10, 6, 20))
            pygame.draw.rect(self.screen, icon_color, (cx+2, cy-10, 6, 20))
        else:
            pts = [(cx-6, cy-8), (cx-6, cy+8), (cx+6, cy)]
            pygame.draw.polygon(self.screen, icon_color, pts)

        # boton aceptar
        self.accept_rect.centerx = box_x + box_width // 2
        self.accept_rect.y = box_y + box_height + 24
        if self.input_text.strip():
            pygame.draw.rect(self.screen, (245,245,245), self.accept_rect, border_radius=14)
            pygame.draw.rect(self.screen, self.rojo, self.accept_rect, 3, border_radius=14)
            txt = self.text_font.render('Aceptar', True, self.negro)
            rojo_txt = self.text_font.render('Aceptar', True, self.rojo)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                self.screen.blit(rojo_txt, (self.accept_rect.x + (self.accept_rect.width - rojo_txt.get_width())//2 + dx,
                                            self.accept_rect.y + (self.accept_rect.height - rojo_txt.get_height())//2 + dy))
            self.screen.blit(txt, (self.accept_rect.x + (self.accept_rect.width - txt.get_width())//2,
                                   self.accept_rect.y + (self.accept_rect.height - txt.get_height())//2))
        else:
            pygame.draw.rect(self.screen, (200,200,200), self.accept_rect, border_radius=14)
            pygame.draw.rect(self.screen, (160,160,160), self.accept_rect, 2, border_radius=14)
            txt = self.text_font.render('Aceptar', True, (120,120,120))
            self.screen.blit(txt, (self.accept_rect.x + (self.accept_rect.width - txt.get_width())//2,
                                   self.accept_rect.y + (self.accept_rect.height - txt.get_height())//2))

        # dibujar icono de engranaje arriba-derecha
        try:
            cx = self.gear_rect.centerx
        except Exception:
            cx = 0
        w, h = self.screen.get_size()
        self.gear_rect.topright = (w - 18, 18)
        gx, gy = self.gear_rect.topleft
        # panel circular
        pygame.draw.rect(self.screen, (245,245,245), self.gear_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.rojo, self.gear_rect, 2, border_radius=8)
        gear_font = pygame.font.SysFont('Segoe UI Symbol', 20)
        try:
            gear_s = gear_font.render('⚙', True, self.rojo)
        except Exception:
            gear_s = self.text_font.render('CFG', True, self.rojo)
        self.screen.blit(gear_s, (self.gear_rect.x + (self.gear_rect.width - gear_s.get_width())//2,
                                  self.gear_rect.y + (self.gear_rect.height - gear_s.get_height())//2))

        # si el menu está abierto, dibujar overlay
        if self.menu_open:
            self._draw_menu()
