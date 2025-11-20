import pygame
import random


class PantallaJuegoMemoria:
    """Juego de parejas: tarjetas volteables dentro del panel 90%.
    """
    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 28, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 18)
        self.cols = 4
        self.rows = 3
        # create pairs (use numbers or letters)
        total = self.cols * self.rows
        values = list(range(total//2)) * 2
        random.shuffle(values)
        self.values = values
        self.revealed = [False] * total
        self.matched = [False] * total
        self.first = None
        self.lock_until = 0
        self.alert = ''
        self.alert_until = 0

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            now = pygame.time.get_ticks()
            if now < self.lock_until:
                return None
            w,h = self.screen.get_size()
            panel_w = int(w * 0.9)
            panel_h = int(h * 0.9)
            panel_x = (w - panel_w)//2
            panel_y = (h - panel_h)//2
            # compute grid area
            margin = 28
            grid_rect = pygame.Rect(panel_x + margin, panel_y + 80, panel_w - margin*2, panel_h - 180)
            # card sizes
            card_w = grid_rect.w // self.cols - 12
            card_h = grid_rect.h // self.rows - 12
            mx,my = event.pos
            for r in range(self.rows):
                for c in range(self.cols):
                    idx = r*self.cols + c
                    x = grid_rect.x + c*(card_w + 12)
                    y = grid_rect.y + r*(card_h + 12)
                    rect = pygame.Rect(x, y, card_w, card_h)
                    if rect.collidepoint((mx,my)) and not self.matched[idx]:
                        if self.revealed[idx]:
                            return None
                        self.revealed[idx] = True
                        if self.first is None:
                            self.first = idx
                        else:
                            # check pair
                            if self.values[self.first] == self.values[idx]:
                                self.matched[self.first] = True
                                self.matched[idx] = True
                                self.first = None
                                # check win
                                if all(self.matched):
                                    return 'next'
                            else:
                                # show briefly then hide
                                self.lock_until = pygame.time.get_ticks() + 900
                                # store mismatch pair to flip back
                                f = self.first
                                s = idx
                                def flip_back():
                                    self.revealed[f] = False
                                    self.revealed[s] = False
                                # schedule flip in update by storing tuple
                                self._to_flip = (f, s)
                                self.first = None
                                self.alert = 'No es pareja. Intenta de nuevo.'
                                self.alert_until = pygame.time.get_ticks() + 1200
                        return None
        return None

    def update(self):
        now = pygame.time.get_ticks()
        if getattr(self, '_to_flip', None) and now >= self.lock_until:
            a,b = self._to_flip
            self.revealed[a] = False
            self.revealed[b] = False
            self._to_flip = None
        if self.alert and now > self.alert_until:
            self.alert = ''

    def draw(self):
        w,h = self.screen.get_size()
        # background
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/area.jpg'), (w, h))
            self.screen.blit(bg, (0,0))
        except Exception:
            try:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
                self.screen.blit(bg, (0,0))
            except Exception:
                self.screen.fill((18,20,24))

        # panel
        panel_w = int(w * 0.9)
        panel_h = int(h * 0.9)
        panel_x = (w - panel_w)//2
        panel_y = (h - panel_h)//2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((18,20,24,220))
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3, border_radius=18)

        # title
        t = self.font_title.render(self.titulo, True, (240,240,240))
        self.screen.blit(t, (panel_x + 24, panel_y + 18))

        # grid
        margin = 28
        grid_rect = pygame.Rect(panel_x + margin, panel_y + 80, panel_w - margin*2, panel_h - 180)
        card_w = grid_rect.w // self.cols - 12
        card_h = grid_rect.h // self.rows - 12
        for r in range(self.rows):
            for c in range(self.cols):
                idx = r*self.cols + c
                x = grid_rect.x + c*(card_w + 12)
                y = grid_rect.y + r*(card_h + 12)
                rect = pygame.Rect(x, y, card_w, card_h)
                if self.matched[idx]:
                    pygame.draw.rect(self.screen, (40,160,100), rect, border_radius=10)
                    txt = self.font_text.render(str(self.values[idx]), True, (255,255,255))
                    self.screen.blit(txt, (rect.x + (rect.w - txt.get_width())//2, rect.y + (rect.h - txt.get_height())//2))
                elif self.revealed[idx]:
                    pygame.draw.rect(self.screen, (220,220,220), rect, border_radius=10)
                    txt = self.font_text.render(str(self.values[idx]), True, (0,0,0))
                    self.screen.blit(txt, (rect.x + (rect.w - txt.get_width())//2, rect.y + (rect.h - txt.get_height())//2))
                else:
                    pygame.draw.rect(self.screen, (100,100,140), rect, border_radius=10)

        # alert
        if self.alert:
            a = self.font_text.render(self.alert, True, (255,200,80))
            self.screen.blit(a, (panel_x + 30, panel_y + panel_h - 100))