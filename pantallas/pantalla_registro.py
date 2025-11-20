import pygame
from core.audio import get_audio
import os
from pantallas.ui_controls import Slider


class AvatarGrid:
    def __init__(self, rect, avatars):
        self.rect = pygame.Rect(rect)
        self.avatars = avatars
        self.selected = None
        self.selected_time = 0
        self.hover_index = None

    def draw(self, screen):
        cols = 4
        pad = 8
        w = (self.rect.w - pad * (cols + 1)) // cols
        h = w
        x0, y0 = self.rect.x + pad, self.rect.y + pad
        # detect mouse for hover
        try:
            mx, my = pygame.mouse.get_pos()
        except Exception:
            mx, my = (-1, -1)
        self.hover_index = None
        for i in range(min(len(self.avatars), 4)):
            x = x0 + (i % cols) * (w + pad)
            y = y0 + (i // cols) * (h + pad)
            cell_rect = pygame.Rect(x, y, w, h)
            bg_rect = cell_rect.inflate(-6, -6)
            # background + border
            pygame.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=12)
            border_col = (70, 70, 74)
            # hover effect
            if mx >= x and mx <= x + w and my >= y and my <= y + h:
                self.hover_index = i
                border_col = (100, 100, 106)
            pygame.draw.rect(screen, border_col, bg_rect, 2, border_radius=12)
            img_rect = bg_rect.inflate(-8, -8)
            path = self.avatars[i]
            if path:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (img_rect.w, img_rect.h))
                    screen.blit(img, (img_rect.x, img_rect.y))
                except Exception:
                    pygame.draw.rect(screen, (220, 220, 220), img_rect, border_radius=8)
            else:
                pygame.draw.rect(screen, (220, 220, 220), img_rect, border_radius=8)

            # selection animation
            if self.selected == i:
                t = pygame.time.get_ticks() - getattr(self, 'selected_time', 0)
                import math
                pulse = 1.0 + 0.15 * math.sin(t / 120.0)
                border_w = max(2, int(3 * pulse))
                glow_rect = bg_rect.inflate(border_w * 2, border_w * 2)
                try:
                    s = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
                    alpha = max(30, min(120, int(80 * pulse)))
                    col = (255, 200, 200, alpha)
                    pygame.draw.rect(s, col, s.get_rect(), border_radius=12)
                    screen.blit(s, (glow_rect.x, glow_rect.y))
                except Exception:
                    pass
                pygame.draw.rect(screen, (255, 200, 200), bg_rect, border_w, border_radius=12)

    def handle_click(self, pos):
        cols = 4
        pad = 8
        w = (self.rect.w - pad * (cols + 1)) // cols
        h = w
        x0, y0 = self.rect.x + pad, self.rect.y + pad
        for i in range(min(len(self.avatars), 4)):
            x = x0 + (i % cols) * (w + pad)
            y = y0 + (i // cols) * (h + pad)
            r = pygame.Rect(x, y, w, h)
            if r.collidepoint(pos):
                self.selected = i
                try:
                    self.selected_time = pygame.time.get_ticks()
                except Exception:
                    self.selected_time = 0
                return i
        return None


class PantallaRegistro:
    """Pantalla de registro que muestra un input de nombre y selección de avatar.
    API compatible con `PantallaInicio`: tiene `input_text`, `handle_events`, `update`, `draw`.
    """
    def __init__(self, screen, estado):
        self.screen = screen
        self.estado = estado
        self.input_text = ''
        self.active = True
        self.max_len = 20

        self.titulo_font = pygame.font.SysFont('Verdana', 40, bold=True)
        self.text_font = pygame.font.SysFont('Verdana', 28)

        self.accept_width = 180
        self.accept_height = 48
        self.accept_rect = pygame.Rect(0, 0, self.accept_width, self.accept_height)

        self.gear_rect = pygame.Rect(0, 0, 34, 34)

        # load avatars from assets/avatares
        base = os.path.join(os.path.dirname(__file__), '..', 'assets', 'avatares')
        base = os.path.normpath(base)
        # allow relative path from project cwd as well
        if not os.path.isdir(base):
            base = os.path.join(os.getcwd(), 'assets', 'avatares')
        avatars = []
        for i in range(1, 5):
            p = os.path.join(base, f'avatar{i}.png')
            avatars.append(p)
        self.avatars = avatars
        self.grid = AvatarGrid((0, 0, 520, 120), self.avatars)

        self.menu_open = False
        self.menu_items = ['Pantalla', 'Records', 'Nosotros', 'Atras']
        self.menu_view = 'options'  # 'options' | 'pantalla' | 'nosotros'
        self.menu_dragging_slider = None  # 'brightness' | 'contrast' | None
        self.menu_dragging = False
        self.menu_hover = -1
        self.menu_pressed = -1
        self.menu_item_height = 54

        self.audio = get_audio()
        # do NOT start menu music now; play it after intro finishes
        self.audio = get_audio()

        # --- intro animation (doors + escape) ---
        self.intro_active = True
        self.intro_state = 'wait'  # wait -> escape_fading -> doors_opening -> done
        self.escape_alpha = 255
        # timings matched to the other project for better sync
        self.escape_fade_duration = 2000
        self.escape_fade_start = None
        self.doors_start = None
        self.doors_duration = 3000
        self.left_door_img = None
        self.right_door_img = None
        self.escape_img = None
        self.left_pos = None
        self.right_pos = None
        # try load images from assets
        try:
            cand_left = [os.path.join('assets', 'puertas.jpg'), os.path.join('assets', 'puertas.jpg')]
            cand_right = [os.path.join('assets', 'puertas2.jpg'), os.path.join('assets', 'puertas2.jpg')]
            cand_escape = [os.path.join('assets', 'escape.png'), os.path.join('assets', 'escape copy.png')]
            for p in cand_left:
                if os.path.exists(p):
                    try:
                        self.left_door_img = pygame.image.load(p).convert_alpha()
                    except Exception:
                        self.left_door_img = None
                    break
            for p in cand_right:
                if os.path.exists(p):
                    try:
                        self.right_door_img = pygame.image.load(p).convert_alpha()
                    except Exception:
                        self.right_door_img = None
                    break
            for p in cand_escape:
                if os.path.exists(p):
                    try:
                        self.escape_img = pygame.image.load(p).convert_alpha()
                    except Exception:
                        self.escape_img = None
                    break
        except Exception:
            pass

        # visual tuning
        self.bg_color = (20, 24, 30)
        self.input_bg = (34, 36, 42)
        self.input_border = (0, 0, 0)
        # unified greyscale palette; use black for borders
        self.accent = (20, 20, 20)
        self.panel_light = (245, 245, 245)
        self.panel_mid = (230, 230, 230)
        self.menu_border = (0, 0, 0)
        self.menu_bg = (230, 230, 230)
        # alerts
        self.alert = ''
        self.alert_until = 0
        # sliders (only brightness — contrast and volume removed)
        self.brightness_slider = Slider('Brillo', -1.0, 1.0, lambda: getattr(self.estado, 'brightness', 0.0), lambda v: self.estado.set_brightness(v), fmt=lambda v: f"{int((v+1.0)/2.0*100)}%")

    def handle_events(self, event):
        # during intro we only accept the initial click to start the animation
        if getattr(self, 'intro_active', False):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.intro_state == 'wait':
                self.escape_fade_start = pygame.time.get_ticks()
                self.intro_state = 'escape_fading'
            return None
        # handle menu interactions (mouse move, click, drag) when menu is open
        if self.menu_open and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            w, h = self.screen.get_size()
            menu_w = min(520, max(280, w - 40))
            menu_h = 420
            menu_x = (w - menu_w) // 2
            menu_y = (h - menu_h) // 2
            btn_h = 44
            # geometry helpers
            def item_rect(i):
                return pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), menu_w - 40, btn_h)

            # tracks for 'pantalla' view will be computed in drawing code
            b_track = None
            c_track = None
            back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, menu_w - 40, btn_h)

            if self.menu_view == 'pantalla':
                label_y = menu_y + 86
                label_h = self.text_font.get_height()
                track_x = menu_x + 160
                track_w = max(160, menu_w - 340)
                b_track_y = label_y + label_h + 8
                b_track = pygame.Rect(track_x, b_track_y, track_w, 12)
                c_track_y = b_track_y + 12 + 18
                c_track = pygame.Rect(track_x, c_track_y, track_w, 12)
                # volume track position (used for dragging in MOUSEMOTION)
                v_label_y = c_track_y + label_h + 8
                v_track_y = v_label_y + label_h + 8
                v_track = pygame.Rect(track_x, v_track_y, track_w, 12)

            # handle mouse wheel (not used here)
            if event.type == pygame.MOUSEWHEEL:
                return None

            # mouse move: update hover and dragging
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                # hover index for options list
                new_hover = -1
                if self.menu_view == 'options':
                    for i in range(len(self.menu_items)):
                        if item_rect(i).collidepoint((mx, my)):
                            new_hover = i
                            break
                self.menu_hover = new_hover
                # if in pantalla subview, forward motion to sliders (they handle dragging state)
                if self.menu_view == 'pantalla':
                    try:
                        # compute layout values for slider mapping
                        w, h = self.screen.get_size()
                        menu_w = min(520, max(280, w - 40))
                        track_x = menu_x + 160
                        track_w = max(160, menu_w - 340)
                        label_y = menu_y + 86
                        # forward motion only to brightness slider
                        self.brightness_slider.handle_event(event, menu_x, menu_y, track_x, track_w, label_y, 0, self.text_font)
                    except Exception:
                        pass
                return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # check gear menu option clicks (only when viewing the options list)
                if self.menu_view == 'options':
                    for i in range(len(self.menu_items)):
                        r = item_rect(i)
                        if r.collidepoint((mx, my)):
                            lab = self.menu_items[i]
                            if lab == 'Records':
                                self.menu_open = False
                                return 'records'
                            elif lab == 'Atras':
                                self.menu_open = False
                                return None
                            else:
                                # switch subview
                                if lab == 'Pantalla':
                                    self.menu_view = 'pantalla'
                                elif lab == 'Nosotros':
                                    self.menu_view = 'nosotros'
                                else:
                                    self.menu_view = 'options'
                                return None

                # if in pantalla subview, forward mouse-down to sliders
                if self.menu_view == 'pantalla':
                    try:
                        w, h = self.screen.get_size()
                        menu_w = min(520, max(280, w - 40))
                        track_x = menu_x + 160
                        track_w = max(160, menu_w - 340)
                        label_y = menu_y + 86
                        if self.brightness_slider.handle_event(event, menu_x, menu_y, track_x, track_w, label_y, 0, self.text_font):
                            return None
                    except Exception:
                        pass

                # back button
                if back_rect.collidepoint((mx, my)):
                    if self.menu_view != 'options':
                        self.menu_view = 'options'
                    else:
                        self.menu_open = False
                    return None

                return None

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # forward mouse-up to sliders so they can clear dragging
                if self.menu_view == 'pantalla':
                    try:
                        w, h = self.screen.get_size()
                        menu_w = min(520, max(280, w - 40))
                        track_x = menu_x + 160
                        track_w = max(160, menu_w - 340)
                        label_y = menu_y + 86
                        # call handler for brightness so it can clear dragging state
                        self.brightness_slider.handle_event(event, menu_x, menu_y, track_x, track_w, label_y, 0, self.text_font)
                    except Exception:
                        pass
                # handle click release for options list (only when showing options)
                mx, my = event.pos
                if self.menu_view == 'options':
                    for i in range(len(self.menu_items)):
                        r = item_rect(i)
                        if r.collidepoint((mx, my)):
                            if self.menu_items[i] == 'Records':
                                self.menu_open = False
                                return 'records'
                            elif self.menu_items[i] == 'Atras':
                                self.menu_open = False
                                return None
                            else:
                                lab = self.menu_items[i]
                                if lab == 'Pantalla':
                                    self.menu_view = 'pantalla'
                                elif lab == 'Nosotros':
                                    self.menu_view = 'nosotros'
                                else:
                                    self.menu_view = 'options'
                                return None
                return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            w, h = self.screen.get_size()
            self.gear_rect.topright = (w - 18, 18)
            if self.gear_rect.collidepoint(event.pos):
                self.menu_open = not self.menu_open
                return None

            if self.accept_rect.collidepoint(event.pos):
                nombre = self.input_text.strip()
                # require both name and avatar
                if not nombre:
                    try:
                        self.alert = 'Ingresá tu nombre'
                        self.alert_until = pygame.time.get_ticks() + 1500
                    except Exception:
                        pass
                    return None
                if self.grid.selected is None:
                    try:
                        self.alert = 'Seleccioná un avatar'
                        self.alert_until = pygame.time.get_ticks() + 1500
                    except Exception:
                        pass
                    return None
                # save avatar choice to estado
                try:
                    self.estado.set_avatar(self.avatars[self.grid.selected])
                except Exception:
                    try:
                        self.estado.avatar = self.avatars[self.grid.selected]
                    except Exception:
                        self.estado.avatar = None
                return 'siguiente'

            sel = self.grid.handle_click(event.pos)
            if sel is not None:
                try:
                    self.estado.set_avatar(self.avatars[sel])
                except Exception:
                    self.estado.avatar = None
                return None

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

    def _render_outlined(self, text, font, fg=(255,255,255), outline=(0,0,0)):
        # Render text with a simple 1px outline by blitting offsets
        try:
            base = font.render(text, True, fg)
            outline_surf = font.render(text, True, outline)
            w = max(base.get_width(), outline_surf.get_width()) + 2
            h = max(base.get_height(), outline_surf.get_height()) + 2
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            # draw outline in 8 directions
            for ox, oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                surf.blit(outline_surf, (ox+1, oy+1))
            surf.blit(base, (1,1))
            return surf
        except Exception:
            try:
                return font.render(text, True, fg)
            except Exception:
                return pygame.Surface((0,0))

    def _wrap_text(self, text, font, max_width):
        """Simple word-wrapping: returns list of lines that fit within max_width using the provided font."""
        if not text:
            return []
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip() if cur else w
            try:
                wdt = font.size(test)[0]
            except Exception:
                try:
                    wdt = font.render(test, True, (0,0,0)).get_width()
                except Exception:
                    wdt = len(test) * 8
            if wdt <= max_width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def update(self):
        # manage intro animation
        if getattr(self, 'intro_active', False):
            now = pygame.time.get_ticks()
            w, h = self.screen.get_size()
            # prepare door positions if images loaded
            if self.left_pos is None and self.left_door_img is not None and self.right_door_img is not None:
                half_w = w // 2
                try:
                    self.left_door_img = pygame.transform.smoothscale(self.left_door_img, (half_w, h))
                except Exception:
                    pass
                try:
                    self.right_door_img = pygame.transform.smoothscale(self.right_door_img, (half_w, h))
                except Exception:
                    pass
                self.left_pos = [0, 0]
                self.right_pos = [half_w, 0]

            if self.intro_state == 'escape_fading' and self.escape_fade_start:
                elapsed = now - self.escape_fade_start
                t = min(1.0, elapsed / float(self.escape_fade_duration))
                self.escape_alpha = int(255 * (1.0 - t))
                if t >= 1.0:
                    self.doors_start = pygame.time.get_ticks()
                    self.intro_state = 'doors_opening'
                    # play door sound if available
                    try:
                        # try several common locations and play with reasonable volume
                        candidates = [
                            os.path.join('assets', 'puertas.mp3'),
                            os.path.join('assets', 'audio', 'puertas.mp3'),
                            os.path.join('recursos', 'audio', 'sfx', 'puertas.mp3'),
                            os.path.join('recursos', 'audio', 'puertas.mp3')
                        ]
                        sfile = None
                        for c in candidates:
                            if os.path.exists(c):
                                sfile = c
                                break
                        if sfile:
                            try:
                                pygame.mixer.init()
                                snd = pygame.mixer.Sound(sfile)
                                try:
                                    snd.set_volume(0.9)
                                except Exception:
                                    pass
                                snd.play()
                            except Exception:
                                pass
                    except Exception:
                        pass

            if self.intro_state == 'doors_opening' and self.doors_start and self.left_pos is not None:
                elapsed = now - self.doors_start
                t = min(1.0, elapsed / float(self.doors_duration))
                half_w = w // 2
                import math
                mod = 1.0 + 0.03 * math.sin(t * math.pi * 8)
                dx = int((half_w + 20) * t * mod)
                self.left_pos[0] = 0 - dx
                self.right_pos[0] = half_w + dx
                if t >= 1.0:
                    self.intro_state = 'done'
                    self.intro_active = False
                    # start menu music now that intro finished
                    try:
                        self.audio.play_music(loop=True)
                    except Exception:
                        pass
            return None
        return None

    def draw(self):
        w, h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'bg_start.jpg')), (w, h))
            self.screen.blit(bg, (0, 0))
        except Exception:
            self.screen.fill(self.bg_color)

        # if intro is active, draw doors/escape overlay and don't show registration UI yet
        if getattr(self, 'intro_active', False):
            try:
                # draw base background darkened
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 120))
                self.screen.blit(overlay, (0, 0))
                if self.left_door_img is not None and self.right_door_img is not None and self.left_pos is not None:
                    lh = self.left_door_img.get_height()
                    lw = self.left_door_img.get_width()
                    rh = self.right_door_img.get_height()
                    rw = self.right_door_img.get_width()
                    if lh != h:
                        left_img = pygame.transform.smoothscale(self.left_door_img, (lw, h))
                    else:
                        left_img = self.left_door_img
                    if rh != h:
                        right_img = pygame.transform.smoothscale(self.right_door_img, (rw, h))
                    else:
                        right_img = self.right_door_img
                    lx, ly = int(self.left_pos[0]), int(self.left_pos[1])
                    rx, ry = int(self.right_pos[0]), int(self.right_pos[1])
                    try:
                        self.screen.blit(left_img, (lx, ly))
                        self.screen.blit(right_img, (rx, ry))
                    except Exception:
                        pass
                if self.escape_img is not None:
                    # render a smaller escape logo centered, preserving aspect ratio
                    try:
                        iw, ih = self.escape_img.get_size()
                        # desired width: clamp to 38% of screen or 380px max
                        desired_w = min(380, max(160, int(w * 0.38)))
                        scale = desired_w / float(max(1, iw))
                        new_w = max(1, int(iw * scale))
                        new_h = max(1, int(ih * scale))
                        esc = pygame.transform.smoothscale(self.escape_img, (new_w, new_h)).copy()
                        try:
                            esc.set_alpha(self.escape_alpha)
                        except Exception:
                            pass
                        ex = (w - esc.get_width())//2
                        ey = (h - esc.get_height())//2 - 40
                        self.screen.blit(esc, (ex, ey))
                    except Exception:
                        try:
                            esc = self.escape_img.copy()
                            try:
                                esc.set_alpha(self.escape_alpha)
                            except Exception:
                                pass
                            ex = (w - esc.get_width())//2
                            ey = (h - esc.get_height())//2 - 40
                            self.screen.blit(esc, (ex, ey))
                        except Exception:
                            pass
            except Exception:
                pass
            return
        # Title with outline (white text, black outline)
        title_surf = self._render_outlined('Registro de jugador', self.titulo_font, fg=(255,255,255), outline=(0,0,0))
        self.screen.blit(title_surf, ((w - title_surf.get_width()) // 2, 48))

        # draw alert if present
        try:
            if getattr(self, 'alert', '') and pygame.time.get_ticks() < getattr(self, 'alert_until', 0):
                af = pygame.font.SysFont('Verdana', 18, bold=True)
                a_s = af.render(self.alert, True, (240,200,80))
                self.screen.blit(a_s, ((w - a_s.get_width())//2, title_surf.get_height() + 60))
        except Exception:
            pass

        # Vertical layout: input -> avatar grid -> label -> accept button
        center_x = w // 2
        y_cursor = 140

        # Input box: dark background, black border, white outlined text
        padding_x = 20
        padding_y = 12
        txt_display = self.input_text if self.input_text else 'Escribí tu nombre...'
        is_placeholder = (not self.input_text)
        txt_color = (180,180,180) if is_placeholder else (255,255,255)
        # measure
        txt_surf_measure = self.text_font.render(txt_display, True, txt_color)
        box_width = max(420, txt_surf_measure.get_width() + padding_x * 2)
        box_height = txt_surf_measure.get_height() + padding_y * 2
        box_x = center_x - box_width // 2
        box_y = y_cursor

        # draw input background and border
        caja_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        # panel claro with subtle black border to match greyscale style
        pygame.draw.rect(self.screen, self.panel_light, caja_rect, border_radius=14)
        pygame.draw.rect(self.screen, (0,0,0), caja_rect, 2, border_radius=14)

        # render text with outline
        if is_placeholder:
            # placeholder smaller contrast, render plain gray
            txt_surf = self.text_font.render(txt_display, True, (120,120,120))
            self.screen.blit(txt_surf, (box_x + padding_x, box_y + padding_y))
        else:
            # filled text: black on light panel, with subtle outline
            txt_surf = self._render_outlined(self.input_text, self.text_font, fg=(20,20,20), outline=(240,240,240))
            self.screen.blit(txt_surf, (box_x + padding_x, box_y + padding_y - 2))

        y_cursor = box_y + box_height + 18

        # (Removed duplicated input box with red border)

        # avatar grid position under the box
        grid_w = min(520, w - 160)
        grid_x = (w - grid_w) // 2
        grid_y = y_cursor
        # use a taller grid like the original project for better visual balance
        self.grid.rect = pygame.Rect(grid_x, grid_y, grid_w, 200)
        self.grid.draw(self.screen)
        # label below grid: outlined white text
        try:
            grid_rect = self.grid.rect
            choose_font = pygame.font.SysFont('Verdana', 22, bold=True)
            label_surf = self._render_outlined('Elija su avatar', choose_font, fg=(255,255,255), outline=(0,0,0))
            lx = grid_rect.x + (grid_rect.w - label_surf.get_width()) // 2
            ly = grid_rect.y + grid_rect.h + 8
            self.screen.blit(label_surf, (lx, ly))
        except Exception:
            pass

        y_cursor = grid_y + self.grid.rect.h + 36

        # accept button
        self.accept_rect.centerx = center_x
        self.accept_rect.y = y_cursor
        # Accept button: light panel with black border when active
        if self.input_text.strip():
            pygame.draw.rect(self.screen, self.panel_light, self.accept_rect, border_radius=14)
            pygame.draw.rect(self.screen, (0,0,0), self.accept_rect, 2, border_radius=14)
            txt_s = self._render_outlined('Aceptar', self.text_font, fg=(20,20,20), outline=(240,240,240))
        else:
            pygame.draw.rect(self.screen, self.panel_mid, self.accept_rect, border_radius=14)
            pygame.draw.rect(self.screen, (120,120,120), self.accept_rect, 2, border_radius=14)
            txt_s = self._render_outlined('Aceptar', self.text_font, fg=(140,140,140), outline=(200,200,200))
        self.screen.blit(txt_s, (self.accept_rect.x + (self.accept_rect.w - txt_s.get_width()) // 2,
                                   self.accept_rect.y + (self.accept_rect.h - txt_s.get_height()) // 2))

        # gear icon (light background + red border like escape_room)
        self.gear_rect.topright = (w - 18, 18)
        pygame.draw.rect(self.screen, (245,245,245), self.gear_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0,0,0), self.gear_rect, 2, border_radius=8)
        try:
            gear_font = pygame.font.SysFont('Segoe UI Symbol', 20)
            gear_s = gear_font.render('⚙', True, (0,0,0))
        except Exception:
            gear_s = self.text_font.render('CFG', True, (0,0,0))
        self.screen.blit(gear_s, (self.gear_rect.x + (self.gear_rect.width - gear_s.get_width()) // 2,
                                  self.gear_rect.y + (self.gear_rect.height - gear_s.get_height()) // 2))

        # if menu open, draw menu overlay and subviews (options / pantalla / nosotros)
        if self.menu_open:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            menu_w = min(520, max(280, w - 40))
            menu_h = 420
            menu_x = (w - menu_w) // 2
            menu_y = (h - menu_h) // 2
            panel = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
            pygame.draw.rect(self.screen, self.menu_bg, panel, border_radius=12)
            pygame.draw.rect(self.screen, self.menu_border, panel, 3, border_radius=12)
            # show the current subview as title for clarity
            view_title = 'Opciones'
            if self.menu_view == 'pantalla':
                view_title = 'Pantalla'
            elif self.menu_view == 'nosotros':
                view_title = 'Nosotros'
            title_s = self._render_outlined(view_title, self.titulo_font, fg=(20,20,20), outline=(0,0,0))
            self.screen.blit(title_s, (menu_x + 20, menu_y + 12))
            btn_w = menu_w - 40
            btn_h = 44
            if self.menu_view == 'options':
                for i, lab in enumerate(self.menu_items):
                    r = pygame.Rect(menu_x + 20, menu_y + 120 + i * (btn_h + 12), btn_w, btn_h)
                    pygame.draw.rect(self.screen, (245, 245, 245), r, border_radius=8)
                    pygame.draw.rect(self.screen, (120, 120, 120), r, 2, border_radius=8)
                    txt = self.text_font.render(lab, True, (20, 20, 20))
                    self.screen.blit(txt, (r.x + 12, r.y + (r.h - txt.get_height()) // 2))
            elif self.menu_view == 'pantalla':
                # Use centralized Slider draw helper for brightness only
                label_y = menu_y + 86
                track_x = menu_x + 160
                track_w = max(160, menu_w - 340)
                try:
                    self.brightness_slider.draw(self.screen, menu_x, menu_y, track_x, track_w, label_y, 0, self.text_font)
                except Exception:
                    pass
                # back button
                back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, btn_w, btn_h)
                pygame.draw.rect(self.screen, (240,240,240), back_rect, border_radius=8)
                pygame.draw.rect(self.screen, (160,160,160), back_rect, 2, border_radius=8)
                back_txt = self.text_font.render('Volver a opciones', True, (20,20,20))
                self.screen.blit(back_txt, (back_rect.x + 12, back_rect.y + 8))
            else:  # nosotros
                # use a smaller font for the 'Nosotros' body so it fits and is readable
                lines = [
                    'Somos Tejo Imaginar, un equipo pequeño de desarrolladores y diseñadores.',
                    'Diseñamos experiencias de escape room digitales y minijuegos educativos y entretenidos.',
                    'Combinamos narrativa, puzzles y pequeñas lecciones para todas las edades.',
                    'Gracias por jugar y por apoyar proyectos independientes.'
                ]
                full = ' '.join(lines)
                small_font = pygame.font.SysFont('Verdana', 16)
                wrapped = self._wrap_text(full, small_font, btn_w - 24)
                y0 = menu_y + 86
                lh = small_font.get_height() + 6
                max_h = menu_h - 140
                for i, ln in enumerate(wrapped):
                    if i * lh > max_h:
                        break
                    t = small_font.render(ln, True, (20,20,20))
                    self.screen.blit(t, (menu_x + 24, y0 + i * lh))
                back_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 64, btn_w, btn_h)
                pygame.draw.rect(self.screen, (240,240,240), back_rect, border_radius=8)
                pygame.draw.rect(self.screen, (160,160,160), back_rect, 2, border_radius=8)
                back_txt = self.text_font.render('Volver a opciones', True, (20,20,20))
                self.screen.blit(back_txt, (back_rect.x + 12, back_rect.y + 8))
