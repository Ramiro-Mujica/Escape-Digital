import pygame
from core.gestor_registros import cargar_registros


class PantallaRecords:
    """Muestra los records (scrollable) y permite volver al inicio."""
    def __init__(self, screen, estado):
        self.screen = screen
        self.estado = estado
        self.font_title = pygame.font.SysFont('Verdana', 34, bold=True)
        self.font_row = pygame.font.SysFont('Verdana', 20)
        self.records = cargar_registros()
        self.scroll = 0
        self.row_height = self.font_row.get_height() + 12
        self.back_rect = pygame.Rect(20, 20, 140, 44)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                # volver al inicio para nuevo registro
                try:
                    # clear name in estado
                    self.estado.nombre = ''
                except Exception:
                    pass
                return 'replay'
        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 40
            self._clamp_scroll()
        # keyboard scroll
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll += 40
                self._clamp_scroll()
            elif event.key == pygame.K_DOWN:
                self.scroll -= 40
                self._clamp_scroll()
        return None

    def _clamp_scroll(self):
        h = self.screen.get_height()
        # visible area inside the central panel (approximate to match draw)
        panel_h = int(h * 0.78)
        visible_h = max(100, panel_h - 160)
        content_h = len(self.records) * self.row_height
        min_scroll = min(0, visible_h - content_h)
        if self.scroll < min_scroll:
            self.scroll = min_scroll
        if self.scroll > 0:
            self.scroll = 0

    def update(self):
        # reload records in case updated
        self.records = cargar_registros()

    def _truncate_text(self, text, font, max_w):
        try:
            if font.size(text)[0] <= max_w:
                return text
            # binary-ish reduce until it fits (simple loop is fine for short strings)
            ell = '…'
            lo = 0
            hi = len(text)
            # naive trim from end
            while hi > 0:
                hi -= 1
                s = text[:hi] + ell
                if font.size(s)[0] <= max_w:
                    return s
            return ell
        except Exception:
            return text

    def draw(self):
        w,h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/bg_records.jpg'), (w, h))
            self.screen.blit(bg, (0, 0))
        except Exception:
            self.screen.fill((18,20,24))

        # central rounded panel for records
        panel_w = int(w * 0.9)
        panel_h = int(h * 0.78)
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        try:
            pygame.draw.rect(panel_surf, (18, 20, 24, 220), panel_surf.get_rect(), border_radius=18)
            pygame.draw.rect(panel_surf, (200,200,200), panel_surf.get_rect(), 3, border_radius=18)
            self.screen.blit(panel_surf, (panel_x, panel_y))
        except Exception:
            panel_surf.fill((18,20,24,220))
            self.screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3)

        # title inside panel
        title = self.font_title.render('Records', True, (240,240,240))
        self.screen.blit(title, (panel_x + (panel_w - title.get_width())//2, panel_y + 14))

        # area list
        start_y = panel_y + 72
        x = panel_x + 36
        y = start_y + self.scroll
        box_w = panel_w - 72
        avatar_size = 48
        gap = 12
        # compute row height to accommodate avatar comfortably
        row_h = max(self.row_height, avatar_size + 12)
        # draw each row with avatar on left and single-line text to the right
        for i, r in enumerate(self.records):
            row_y = y + i * row_h
            row_rect = pygame.Rect(x, row_y, box_w, row_h - 6)
            # alternate color (light rows shown inside dark panel)
            color = (44, 46, 50) if i % 2 == 0 else (36, 38, 42)
            pygame.draw.rect(self.screen, color, row_rect, border_radius=8)

            # draw avatar if available
            av_path = r.get('avatar')
            tx = row_rect.x + 12
            if av_path:
                try:
                    av_img = pygame.image.load(av_path).convert_alpha()
                    av_img = pygame.transform.smoothscale(av_img, (avatar_size, avatar_size))
                    av_rect = pygame.Rect(row_rect.x + 8, row_rect.y + (row_rect.h - avatar_size) // 2, avatar_size, avatar_size)
                    self.screen.blit(av_img, av_rect.topleft)
                    tx = av_rect.right + gap
                except Exception:
                    tx = row_rect.x + 12

            # text: rank. name — time s — date (single line, truncated if needed)
            name = r.get('name') or r.get('jugador') or '---'
            timev = r.get('time') if r.get('time') is not None else r.get('tiempo')
            timev = timev if timev is not None else '---'
            datev = r.get('date') or r.get('fecha') or ''
            full_text = f"{i+1}. {name} — {timev}s — {datev}"
            # available width for text
            text_max_w = row_rect.x + row_rect.w - tx - 12
            display_text = self._truncate_text(full_text, self.font_row, text_max_w)
            surf = self.font_row.render(display_text, True, (220, 220, 220))
            # vertically center text within row
            ty = row_rect.y + (row_rect.h - surf.get_height()) // 2
            self.screen.blit(surf, (tx, ty))

        # scrollbar indicator when needed (inside panel)
        content_h = len(self.records) * self.row_height
        visible_h = panel_h - (start_y - panel_y) - 36
        if content_h > visible_h:
            track_h = visible_h
            thumb_h = max(40, int(track_h * visible_h / content_h))
            max_scroll = content_h - visible_h
            scroll_pos = -self.scroll
            thumb_y = start_y + int((scroll_pos / max_scroll) * (track_h - thumb_h))
            track_x = panel_x + panel_w - 28
            pygame.draw.rect(self.screen, (70,70,70), (track_x, start_y, 12, track_h), border_radius=6)
            pygame.draw.rect(self.screen, (140,140,140), (track_x, thumb_y, 12, thumb_h), border_radius=6)

        # draw back button centered at bottom of panel (no red borders)
        label = 'Volver al inicio'
        txt = self.font_row.render(label, True, (0,0,0))
        pw = txt.get_width() + 24
        max_pw = int(panel_w * 0.6)
        pw = min(pw, max_pw)
        self.back_rect.w = pw
        self.back_rect.h = 44
        self.back_rect.center = (panel_x + panel_w//2, panel_y + panel_h - 34)
        pygame.draw.rect(self.screen, (245,245,245), self.back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (0,0,0), self.back_rect, 2, border_radius=10)
        tx = self.back_rect.x + 12
        ty = self.back_rect.y + (self.back_rect.h - txt.get_height()) // 2
        self.screen.blit(txt, (tx, ty))
