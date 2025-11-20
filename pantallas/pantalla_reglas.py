import pygame
import os


def draw_persistent_hud(screen, estado):
    """Draw a compact bottom-right HUD showing avatar, name, timer and lives.

    Uses a greyscale panel with black outlines and `assets/vida.png` as life icon.
    """
    try:
        w, h = screen.get_size()
        panel_w, panel_h = 260, 88
        px = w - panel_w - 16
        py = h - panel_h - 16

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # grey-black palette
        panel.fill((28, 30, 34, 220))
        pygame.draw.rect(panel, (0, 0, 0), panel.get_rect(), 2, border_radius=14)

        # Avatar
        avatar_surf = None
        avatar_path = getattr(estado, 'avatar', None)
        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar_surf = pygame.image.load(avatar_path).convert_alpha()
            except Exception:
                avatar_surf = None
        if avatar_surf is not None:
            try:
                av = pygame.transform.smoothscale(avatar_surf, (56, 56))
                panel.blit(av, (12, (panel_h - 56)//2))
            except Exception:
                pass

        # Name and timer
        try:
            font = pygame.font.Font(None, 22)
        except Exception:
            font = pygame.font.SysFont('Arial', 20)
        name = getattr(estado, 'nombre', None) or getattr(estado, 'name', '') or ''
        tiempo = None
        try:
            tiempo = estado.tiempo_transcurrido()
        except Exception:
            try:
                tiempo = getattr(estado, 'cronometro', None)
            except Exception:
                tiempo = None
        try:
            tiempo_display = f"{int(tiempo)}s" if tiempo is not None else ''
        except Exception:
            tiempo_display = str(tiempo) if tiempo is not None else ''

        txt_name = font.render(name, True, (230, 230, 230))
        txt_time = font.render(tiempo_display, True, (190, 190, 190))
        panel.blit(txt_name, (84, 16))
        panel.blit(txt_time, (84, 40))

        # Lives: display up to 10 small life icons in a row (one icon per life)
        vidas = getattr(estado, 'vidas', None)
        if vidas is None:
            vidas = 0
        try:
            vida_icon_path = os.path.join('assets', 'vida.png')
            if os.path.exists(vida_icon_path):
                vida_img_raw = pygame.image.load(vida_icon_path).convert_alpha()
            else:
                vida_img_raw = None
        except Exception:
            vida_img_raw = None

        max_lives = 10
        # layout: small icons aligned to the right area of the panel under name/time
        vida_w = 14
        vida_h = 14
        spacing = 6
        total_w = max_lives * vida_w + (max_lives - 1) * spacing
        start_x = panel_w - 12 - total_w
        y_icon = 62
        for i in range(max_lives):
            x = start_x + i * (vida_w + spacing)
            if i < int(vidas):
                # draw filled life
                if vida_img_raw:
                    try:
                        vida_img = pygame.transform.smoothscale(vida_img_raw, (vida_w, vida_h))
                        panel.blit(vida_img, (x, y_icon))
                    except Exception:
                        pygame.draw.circle(panel, (240, 180, 80), (x + vida_w//2, y_icon + vida_h//2), vida_w//2)
                else:
                    pygame.draw.circle(panel, (240, 180, 80), (x + vida_w//2, y_icon + vida_h//2), vida_w//2)
            else:
                # empty/consumed life (draw dim outline)
                try:
                    s = pygame.Surface((vida_w, vida_h), pygame.SRCALPHA)
                    pygame.draw.circle(s, (80, 80, 80, 90), (vida_w//2, vida_h//2), vida_w//2)
                    panel.blit(s, (x, y_icon))
                except Exception:
                    pygame.draw.circle(panel, (80, 80, 80), (x + vida_w//2, y_icon + vida_h//2), vida_w//2)

        screen.blit(panel, (px, py))
    except Exception:
        pass


class PantallaReglas:
    """Pantalla de reglas para un minijuego.

    Muestra a la izquierda una imagen `assets/reglas{index}.png` si existe
    (si no, un recuadro de color). A la derecha muestra el texto de reglas
    con efecto máquina de escribir. Tiene botón 'Continuar' para avanzar.
    """
    def __init__(self, screen, index, titulo, texto):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.texto = texto
        self.font_title = pygame.font.SysFont('Verdana', 34, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 20)

        # typewriter state
        self.full_text = texto
        self.shown_len = 0
        self.last_tick = pygame.time.get_ticks()
        # default speed; slow down slightly for the last game's rules
        if index == 4:
            self.char_interval = 80  # ms per character (más lento)
        else:
            self.char_interval = 30  # ms per character

        
        # boton continuar
        self.cont_rect = pygame.Rect(0, 0, 220, 56)

        # try load image (keep raw surface; scale later to preserve aspect)
        # choose a rule image: prefer specific themed images where available
        yamato = os.path.join('assets', 'yamato.png')
        default_tai = os.path.join('assets', 'tai.png')
        izumi = os.path.join('assets', 'izumi.png')
        sora = os.path.join('assets', 'sora.png')
        # prefer izumi for Juego 3, yamato for Juego 2, sora for Juego 4, then tai fallback
        if index == 4 and os.path.exists(sora):
            self.image_path = sora
        elif index == 3 and os.path.exists(izumi):
            self.image_path = izumi
        elif index == 2 and os.path.exists(yamato):
            self.image_path = yamato
        elif os.path.exists(default_tai):
            self.image_path = default_tai
        else:
            self.image_path = os.path.join('assets', f'reglas{index}.png')
        try:
            if os.path.exists(self.image_path):
                img = pygame.image.load(self.image_path)
                try:
                    self.image_raw = img.convert_alpha()
                except Exception:
                    self.image_raw = img.convert()
            else:
                self.image_raw = None
        except Exception:
            self.image_raw = None

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            w, h = self.screen.get_size()
            self.cont_rect.center = (w//2, h - 80)
            if self.cont_rect.collidepoint(event.pos):
                return 'next'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return 'next'
        return None

    def update(self):
        now = pygame.time.get_ticks()
        if self.shown_len < len(self.full_text) and now - self.last_tick >= self.char_interval:
            self.shown_len += 1
            self.last_tick = now

    def draw(self):
        w, h = self.screen.get_size()
        # background
        try:
            # use area.jpg as background for all rules screens if available
            area_path = os.path.join('assets', 'area.jpg')
            if os.path.exists(area_path):
                bg = pygame.transform.scale(pygame.image.load(area_path), (w, h))
            else:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
            self.screen.blit(bg, (0, 0))
        except Exception:
            self.screen.fill((18, 20, 24))

        # central panel occupying ~90% of the window
        panel_w = int(w * 0.9)
        panel_h = int(h * 0.9)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # translucent rounded panel and border (darker for better contrast)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            # draw filled rounded rect into the surface so the panel itself has rounded corners
            pygame.draw.rect(panel_surf, (18, 20, 24, 220), panel_surf.get_rect(), border_radius=18)
            pygame.draw.rect(panel_surf, (200,200,200), panel_surf.get_rect(), 3, border_radius=18)
            self.screen.blit(panel_surf, (panel_x, panel_y))
        except Exception:
            # fallback: solid blit + rectangular border
            panel_surf.fill((18, 20, 24, 220))
            self.screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3)

        # title inside panel (more contrast)
        t_surf = self.font_title.render(self.titulo, True, (255, 255, 255))
        self.screen.blit(t_surf, (panel_x + 24, panel_y + 18))

        # image (if present) centered near the top of the panel
        img_area_h = int(panel_h * 0.35)
        if getattr(self, 'image_raw', None):
            iw, ih = self.image_raw.get_size()
            if ih > 0 and iw > 0:
                aspect = iw / ih
                target_w = int(panel_w * 0.6)
                target_h = int(target_w / aspect)
                max_h = int(img_area_h * 0.95)
                if target_h > max_h:
                    target_h = max_h
                    target_w = int(target_h * aspect)
                try:
                    scaled = pygame.transform.smoothscale(self.image_raw, (max(1, target_w), max(1, target_h)))
                except Exception:
                    try:
                        scaled = pygame.transform.scale(self.image_raw, (max(1, target_w), max(1, target_h)))
                    except Exception:
                        scaled = None
                if scaled:
                    # draw the image inside a rounded panel so small images don't look like naked squares
                    img_rect = scaled.get_rect()
                    center_x = panel_x + panel_w//2
                    center_y = panel_y + 24 + img_area_h//2
                    img_rect.center = (center_x, center_y)
                    # background box slightly larger than image, rounded and with thin black border
                    pad = 12
                    box_w = img_rect.w + pad * 2
                    box_h = img_rect.h + pad * 2
                    box_x = center_x - box_w // 2
                    box_y = center_y - box_h // 2
                    box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
                    # Blit the image directly without an extra background box or border
                    # (images should be provided with transparent backgrounds if needed)
                    try:
                        self.screen.blit(scaled, img_rect)
                    except Exception:
                        pass

        # textual rules area below the image
        dialog_rect = pygame.Rect(panel_x + 24, panel_y + int(panel_h*0.35) + 36, panel_w - 48, panel_h - int(panel_h*0.35) - 120)
        # draw text progressively; sanitize newlines so unsupported glyphs don't render
        text_to_show = self.full_text[:self.shown_len]
        # replace newline characters with spaces to avoid unknown-glyph boxes
        try:
            text_to_show = text_to_show.replace('\n', ' ').replace('\r', ' ')
        except Exception:
            pass
        # wrap text manually
        lines = []
        words = text_to_show.split(' ')
        cur = ''
        for word in words:
            test = (cur + ' ' + word).strip()
            if self.font_text.size(test)[0] > dialog_rect.width - 24:
                lines.append(cur)
                cur = word
            else:
                cur = test
        if cur:
            lines.append(cur)

        y = dialog_rect.y + 8
        for ln in lines:
            # brighter white text for legibility
            surf = self.font_text.render(ln, True, (255,255,255))
            self.screen.blit(surf, (dialog_rect.x + 6, y))
            y += self.font_text.get_height() + 6

        # boton continuar (greyscale style, no red borders)
        self.cont_rect.center = (w//2, h - 80)
        pygame.draw.rect(self.screen, (245,245,245), self.cont_rect, border_radius=14)
        pygame.draw.rect(self.screen, (0,0,0), self.cont_rect, 2, border_radius=14)
        f = pygame.font.SysFont('Verdana', 22, bold=True)
        txt = f.render('Continuar', True, (0,0,0))
        self.screen.blit(txt, (self.cont_rect.x + (self.cont_rect.width - txt.get_width())//2,
                       self.cont_rect.y + (self.cont_rect.height - txt.get_height())//2))
        
        # Nota: no dibujamos aquí el HUD persistente (vidas/nombre/cronómetro)
        # Las pantallas de reglas deben mostrarse sin HUD; el HUD se dibuja
        # globalmente desde `main.py` cuando `estado.hud_persistent` es True.
