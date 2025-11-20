import pygame
import random
import os


class PantallaJuegoParejas:
    """Memory pairs game using images in assets/img1..img5.png (will use up to 4 pairs).
    Grid 4x2 (8 cards). Click to reveal; matches stay revealed. When all matched, return 'next'."""
    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 30, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 20)
        self.images = []
        for i in range(1,6):
            p = os.path.join('assets', f'img{i}.png')
            try:
                img = pygame.image.load(p).convert_alpha()
                self.images.append(img)
            except Exception:
                pass
        if len(self.images) < 4:
            # fallback to simple colored squares if not enough images
            self.images = [None]*4

        # pick 4 images to use
        choices = random.sample(self.images, 4)
        deck = choices + choices
        random.shuffle(deck)
        self.deck = deck
        self.revealed = [False]*8
        self.locked = [False]*8
        self.first = None
        self.wait_timer = 0
        self.message = ''
        self.completed = False
        self.cont_rect = pygame.Rect(0,0,240,56)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.wait_timer > 0:
                return None
            # if completed, only allow manual continue after auto-advance timeout
            if self.completed:
                mx,my = event.pos
                self.cont_rect.center = (self.screen.get_width()//2, self.screen.get_height() - 80)
                now = pygame.time.get_ticks()
                # if auto_advance is set and not yet expired, ignore clicks
                if hasattr(self, 'auto_advance_until') and self.auto_advance_until and now < self.auto_advance_until:
                    return None
                if self.cont_rect.collidepoint((mx,my)):
                    return 'next'
                return None
            mx,my = event.pos
            w,h = self.screen.get_size()
            panel_w = int(w*0.9)
            panel_h = int(h*0.9)
            panel_x = (w - panel_w)//2
            panel_y = (h - panel_h)//2
            margin = 28
            inner_w = panel_w - margin*2
            inner_h = panel_h - margin*2 - 80
            grid_x = panel_x + margin
            grid_y = panel_y + margin + 40
            cols = 4
            rows = 2
            card_w = int((inner_w - (cols-1)*12) / cols)
            card_h = int((inner_h - (rows-1)*12) / rows)
            for idx in range(8):
                rcol = idx % cols
                rrow = idx // cols
                rx = grid_x + rcol * (card_w + 12)
                ry = grid_y + rrow * (card_h + 12)
                rect = pygame.Rect(rx, ry, card_w, card_h)
                if rect.collidepoint((mx,my)) and not self.locked[idx]:
                    # reveal
                    self.revealed[idx] = True
                    if self.first is None:
                        self.first = idx
                    else:
                        # check match
                        if self._same_image(self.deck[self.first], self.deck[idx]):
                            self.locked[self.first] = True
                            self.locked[idx] = True
                            self.first = None
                            # check win
                            if all(self.locked):
                                # mark completed and show message
                                self.completed = True
                                self.message = '¡Correcto! Preparando siguiente...'
                                # ensure any pending timers are cleared
                                self.wait_timer = 0
                                # start auto-advance countdown (5 seconds)
                                try:
                                    self.auto_advance_until = pygame.time.get_ticks() + 5000
                                except Exception:
                                    self.auto_advance_until = None
                        else:
                            # start hide timer
                            self.wait_timer = pygame.time.get_ticks() + 800
                            # player made a mistake: decrement a life if estado is available
                            try:
                                if hasattr(self, 'estado') and getattr(self, 'estado') is not None:
                                    try:
                                        self.estado.perder_vida(1)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    break
        return None

    def _same_image(self, a, b):
        # since images may be None placeholders, compare by id or None
        return (a is None and b is None) or (a is not None and b is not None and a.get_rect().size == b.get_rect().size and a.get_bitsize() == b.get_bitsize())

    def update(self):
        if self.wait_timer and pygame.time.get_ticks() >= self.wait_timer:
            # hide the last two revealed that are not locked
            for i in range(8):
                if not self.locked[i] and self.revealed[i]:
                    self.revealed[i] = False
            self.first = None
            self.wait_timer = 0

    def draw(self):
        w,h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/area.jpg'), (w, h))
            self.screen.blit(bg, (0,0))
        except Exception:
            self.screen.fill((18,20,24))

        # panel
        panel_w = int(w*0.9)
        panel_h = int(h*0.9)
        panel_x = (w - panel_w)//2
        panel_y = (h - panel_h)//2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # mismo look apagado que el juego Simon
        panel_surf.fill((8,8,12,200))
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3, border_radius=18)

        title = self.font_title.render(self.titulo, True, (255,255,255))
        self.screen.blit(title, (panel_x + 24, panel_y + 18))

        # draw grid
        margin = 28
        inner_w = panel_w - margin*2
        inner_h = panel_h - margin*2 - 80
        grid_x = panel_x + margin
        grid_y = panel_y + margin + 40
        cols = 4
        rows = 2
        card_w = int((inner_w - (cols-1)*12) / cols)
        card_h = int((inner_h - (rows-1)*12) / rows)
        for idx in range(8):
            rcol = idx % cols
            rrow = idx // cols
            rx = grid_x + rcol * (card_w + 12)
            ry = grid_y + rrow * (card_h + 12)
            rect = pygame.Rect(rx, ry, card_w, card_h)
            if self.revealed[idx] or self.locked[idx]:
                # show image if available
                img = self.deck[idx]
                if img:
                    try:
                        scaled = pygame.transform.smoothscale(img, (card_w, card_h))
                    except Exception:
                        scaled = pygame.transform.scale(img, (card_w, card_h))
                    self.screen.blit(scaled, rect)
                else:
                    pygame.draw.rect(self.screen, (200,160,120), rect, border_radius=8)
            else:
                pygame.draw.rect(self.screen, (100,100,110), rect, border_radius=8)

        # continue button when completed
        if self.completed:
            self.cont_rect.center = (panel_x + panel_w//2, panel_y + panel_h - 76)
            now = pygame.time.get_ticks()
            if now < getattr(self, 'auto_advance_until', 0):
                # show countdown instead of active button
                pygame.draw.rect(self.screen, (200,200,200), self.cont_rect, border_radius=16)
                pygame.draw.rect(self.screen, (140,140,140), self.cont_rect, 3, border_radius=16)
                f = pygame.font.SysFont('Verdana', 20, bold=True)
                remaining = max(0, int((self.auto_advance_until - now + 999)//1000))
                t = f.render(f'Avanzar en {remaining}', True, (100,100,100))
                self.screen.blit(t, (self.cont_rect.x + (self.cont_rect.w - t.get_width())//2, self.cont_rect.y + (self.cont_rect.h - t.get_height())//2))
            else:
                pygame.draw.rect(self.screen, (245,245,245), self.cont_rect, border_radius=12)
                pygame.draw.rect(self.screen, (30,120,30), self.cont_rect, 3, border_radius=12)
                f = pygame.font.SysFont('Verdana', 22, bold=True)
                t = f.render('Continuar', True, (0,0,0))
                self.screen.blit(t, (self.cont_rect.x + (self.cont_rect.w - t.get_width())//2, self.cont_rect.y + (self.cont_rect.h - t.get_height())//2))

        # message (transient); when completed we already show the modal/button so avoid duplicate
        if self.message and not self.completed:
            m = self.font_text.render(self.message, True, (255,200,80))
            self.screen.blit(m, (panel_x + 30, (self.cont_rect.y if self.completed else panel_y + panel_h - 40)))
