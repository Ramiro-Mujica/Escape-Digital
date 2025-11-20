"""
Pantalla Juego César (limpia): muestra la palabra cifrada y solicita respuesta.
"""
import pygame
import random


class PantallaJuegoCesar:
    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 30, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 20)
        self.input_text = ''
        self.active = True
        self.alert = ''
        self.alert_until = 0
        # Usar lista de palabras y lógica del otro proyecto (VF-Escape-Room)
        words = [
            "cesar", "clave", "python", "escape", "codigo",
            "logica", "pantalla", "juego"
        ]
        self.original = random.choice(words)

        # Cifrar solo letras ASCII a-z/A-Z (la 'ñ' no cuenta)
        def cifrar(texto, desplazamiento):
            resultado = ""
            for letra in texto:
                if letra.isalpha() and letra.lower() in 'abcdefghijklmnopqrstuvwxyz':
                    base = ord('a') if letra.islower() else ord('A')
                    resultado += chr((ord(letra) - base + desplazamiento) % 26 + base)
                else:
                    resultado += letra
            return resultado

        self.shift = 3
        self.encoded = cifrar(self.original, self.shift)
        self.submit_rect = pygame.Rect(0, 0, 160, 44)
        self.submit_hover = False

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self._try_submit()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if event.unicode and event.unicode.isprintable():
                    self.input_text += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # submit button click
            if self.submit_rect.collidepoint(event.pos):
                return self._try_submit()
            # clicking the invisible (previous) submit target kept for compatibility
            w, h = self.screen.get_size()
            old_center = (w // 2, h - 80)
            if pygame.Rect(0,0,200,48).collidepoint((event.pos[0]-old_center[0]+100, event.pos[1]-old_center[1]+24)):
                return self._try_submit()

        # if completed, only allow continue after auto-advance timer expires
        if getattr(self, 'completed', False):
            now = pygame.time.get_ticks()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                w,h = self.screen.get_size()
                cont = pygame.Rect(0,0,240,56)
                cont.center = (w//2, h-120)
                if cont.collidepoint(event.pos) and now >= getattr(self, 'auto_advance_until', float('inf')):
                    return 'next'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and now >= getattr(self, 'auto_advance_until', float('inf')):
                return 'next'

        return None

    def _try_submit(self):
        guess = self.input_text.strip().lower()
        if guess == self.original:
            # show success alert and only allow continuing after 2s
            now = pygame.time.get_ticks()
            self.alert = '¡Correcto! Terminaste este juego.'
            self.alert_until = now + 2000
            self.input_text = ''
            # mark as completed; continue will be accepted after alert_until
            self.completed = True
            # schedule auto-advance in 5 seconds (show countdown)
            self.auto_advance_until = now + 5000
            try:
                from core.audio import get_audio
                get_audio().play_effect('success')
            except Exception:
                pass
            return None
        else:
            self.alert = 'Incorrecto — inténtalo otra vez.'
            self.alert_until = pygame.time.get_ticks() + 1400
            self.input_text = ''
            # decrement a life on incorrect answer if estado is available
            try:
                if hasattr(self, 'estado') and getattr(self, 'estado') is not None:
                    try:
                        self.estado.perder_vida(1)
                    except Exception:
                        pass
            except Exception:
                pass
            return None

    def update(self):
        if self.alert and pygame.time.get_ticks() > self.alert_until:
            self.alert = ''

    def draw(self):
        w, h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/area.jpg'), (w, h))
            self.screen.blit(bg, (0, 0))
        except Exception:
            try:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
                self.screen.blit(bg, (0, 0))
            except Exception:
                self.screen.fill((18, 20, 24))

        # make panel smaller so HUD doesn't overlap and layout feels lighter
        panel_w = int(w * 0.76)
        panel_h = int(h * 0.72)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # dibujar panel redondeado (fill + border) para que las esquinas sean transparentes
        try:
            pygame.draw.rect(panel_surf, (8, 8, 12, 200), panel_surf.get_rect(), border_radius=18)
            pygame.draw.rect(panel_surf, (200, 200, 200), panel_surf.get_rect(), 3, border_radius=18)
            self.screen.blit(panel_surf, (panel_x, panel_y))
        except Exception:
            # fallback rectangular
            panel_surf.fill((8, 8, 12, 200))
            self.screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 3)

        # centered title with subtle shadow
        title_s = self.font_title.render(self.titulo, True, (240, 240, 240))
        # shadow
        try:
            self.screen.blit(self.font_title.render(self.titulo, True, (12,12,12)), (panel_x + (panel_w - title_s.get_width())//2 + 2, panel_y + 18 + 2))
        except Exception:
            pass
        self.screen.blit(title_s, (panel_x + (panel_w - title_s.get_width())//2, panel_y + 18))

        inst = 'Este juego usa cifrado César (3 letras adelante). Verás la palabra CIFRADA y debes escribir la original. La letra "ñ" no se considera.'
        y = panel_y + 80
        lines = self._wrap_text(inst, self.font_text, panel_w - 60)
        for ln in lines:
            self.screen.blit(self.font_text.render(ln, True, (220, 220, 220)), (panel_x + 30, y))
            y += self.font_text.get_height() + 6

        big_font = pygame.font.SysFont('Verdana', 56, bold=True)
        big = big_font.render(self.encoded.upper(), True, (255, 230, 140))
        # subtle background pill behind code
        code_x = panel_x + (panel_w - big.get_width()) // 2
        code_y = y + 8
        pill_rect = pygame.Rect(code_x - 12, code_y - 8, big.get_width() + 24, big.get_height() + 16)
        pill_surf = pygame.Surface((pill_rect.w, pill_rect.h), pygame.SRCALPHA)
        pill_surf.fill((30, 28, 24, 160))
        try:
            pygame.draw.rect(pill_surf, (255, 230, 140, 24), pill_surf.get_rect(), border_radius=12)
            self.screen.blit(pill_surf, (pill_rect.x, pill_rect.y))
        except Exception:
            self.screen.blit(pill_surf, (pill_rect.x, pill_rect.y))
        self.screen.blit(big, (code_x, code_y))

        # input area: place above bottom to avoid HUD overlap
        inp_y = panel_y + panel_h - 120
        prompt = self.font_text.render('Tu respuesta:', True, (220, 220, 220))
        self.screen.blit(prompt, (panel_x + 30, inp_y))
        box = pygame.Rect(panel_x + 160, inp_y - 6, panel_w - 420, 44)
        # dark rounded input with light text
        pygame.draw.rect(self.screen, (28, 30, 34), box, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 100), box, 2, border_radius=10)
        txt = self.font_text.render(self.input_text or '', True, (230, 230, 230))
        self.screen.blit(txt, (box.x + 12, box.y + (box.h - txt.get_height()) // 2))

        # El botón de envío se mantiene funcional (detección de clicks y Enter),
        # pero lo hacemos invisible para evitar elementos visuales durante la interacción.
        # Si se desea, se puede habilitar mostrando este bloque.

        # submit button to the right of input
        self.submit_rect.topleft = (box.x + box.w + 16, box.y)
        mouse = pygame.mouse.get_pos()
        self.submit_hover = self.submit_rect.collidepoint(mouse)
        btn_color = (245,245,245) if not self.submit_hover else (255, 250, 230)
        border_col = (30,30,30)
        pygame.draw.rect(self.screen, btn_color, self.submit_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_col, self.submit_rect, 2, border_radius=12)
        bf = pygame.font.SysFont('Verdana', 20, bold=True)
        bt = bf.render('Validar', True, (0,0,0))
        self.screen.blit(bt, (self.submit_rect.x + (self.submit_rect.w - bt.get_width())//2, self.submit_rect.y + (self.submit_rect.h - bt.get_height())//2))

        # show transient alerts only when not in the completed auto-advance modal
        if self.alert and not getattr(self, 'completed', False):
            a = self.font_text.render(self.alert, True, (255, 200, 80))
            self.screen.blit(a, (panel_x + 30, self.submit_rect.y - 34))

        # show continue button when completed (but only active after alert period)
        if getattr(self, 'completed', False):
            cont = pygame.Rect(0,0,220,52)
            cont.center = (panel_x + panel_w//2, panel_y + panel_h - 64)
            now = pygame.time.get_ticks()
            if now < getattr(self, 'auto_advance_until', 0):
                # show countdown
                remaining = max(0, int((self.auto_advance_until - now + 999)//1000))
                pygame.draw.rect(self.screen, (200,200,200), cont, border_radius=16)
                pygame.draw.rect(self.screen, (140,140,140), cont, 3, border_radius=16)
                f = pygame.font.SysFont('Verdana', 20, bold=True)
                t = f.render(f'Avanzar en {remaining}', True, (100,100,100))
                self.screen.blit(t, (cont.x + (cont.w - t.get_width())//2, cont.y + (cont.h - t.get_height())//2))
            else:
                pygame.draw.rect(self.screen, (245,245,245), cont, border_radius=16)
                pygame.draw.rect(self.screen, (30,30,30), cont, 3, border_radius=16)
                f = pygame.font.SysFont('Verdana', 22, bold=True)
                t = f.render('Continuar', True, (0,0,0))
                self.screen.blit(t, (cont.x + (cont.w - t.get_width())//2, cont.y + (cont.h - t.get_height())//2))

    def _wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            test = cur + (' ' if cur else '') + w
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines
