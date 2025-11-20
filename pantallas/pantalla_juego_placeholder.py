import pygame


class PantallaJuegoPlaceholder:
    """Placeholder para un minijuego: título y botón 'Finalizar' que
    simula completar el minijuego y avanzar al siguiente.
    """
    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 34, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 20)
        self.finish_rect = pygame.Rect(0, 0, 220, 56)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            w,h = self.screen.get_size()
            self.finish_rect.center = (w//2, h - 80)
            if self.finish_rect.collidepoint(event.pos):
                return 'next'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return 'next'
        return None

    def update(self):
        return

    def draw(self):
        w,h = self.screen.get_size()
        # use the same background as rules (area.jpg) if available, otherwise fallback
        try:
            bg_img = pygame.image.load('assets/area.jpg')
            bg = pygame.transform.scale(bg_img, (w, h))
            self.screen.blit(bg, (0,0))
        except Exception:
            try:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
                self.screen.blit(bg, (0,0))
            except Exception:
                self.screen.fill((18,20,24))

        title_surf = self.font_title.render(self.titulo, True, (240,240,240))
        self.screen.blit(title_surf, ((w - title_surf.get_width())//2, 40))

        info = self.font_text.render('Aquí iría la lógica del minijuego (placeholder).', True, (220,220,220))
        self.screen.blit(info, ((w - info.get_width())//2, 140))

        # central rounded panel occupying ~80% of the window (centered)
        panel_w = int(w * 0.8)
        panel_h = int(h * 0.8)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # semi-transparent panel surface for nicer overlay on the background
        # draw rounded translucent panel
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0,0,0,0))
        pygame.draw.rect(panel_surf, (18, 20, 24, 220), pygame.Rect(0, 0, panel_w, panel_h), border_radius=18)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3, border_radius=18)

        # inside the panel, draw a placeholder left/right layout scaled to panel
        margin = 28
        inner_w = panel_w - margin*2
        inner_h = panel_h - margin*2 - 80  # leave space for title at top inside panel
        left = pygame.Rect(panel_x + margin, panel_y + margin + 40, int(inner_w * 0.45), inner_h)
        right = pygame.Rect(left.right + 24, left.y, int(inner_w * 0.55) - 24, inner_h)
        pygame.draw.rect(self.screen, (70,120,170), left, border_radius=12)
        pygame.draw.rect(self.screen, (36,36,36), right, border_radius=12)

        # finish button
        self.finish_rect.center = (w//2, h - 80)
        pygame.draw.rect(self.screen, (245,245,245), self.finish_rect, border_radius=14)
        pygame.draw.rect(self.screen, (200,30,30), self.finish_rect, 3, border_radius=14)
        f = pygame.font.SysFont('Verdana', 22, bold=True)
        txt = f.render('Finalizar (simular)', True, (0,0,0))
        self.screen.blit(txt, (self.finish_rect.x + (self.finish_rect.width - txt.get_width())//2,
                               self.finish_rect.y + (self.finish_rect.height - txt.get_height())//2))
