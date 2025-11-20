import pygame


class Slider:
    def __init__(self, label, minv, maxv, getter, setter, fmt=None):
        self.label = label
        self.min = minv
        self.max = maxv
        self.get = getter
        self.set = setter
        self.dragging = False
        self.knob_r = 12
        self.fmt = fmt if fmt is not None else (lambda v: f"{v:.2f}" if isinstance(v, float) else str(v))

    def _compute_geometry(self, menu_x, menu_y, track_x, track_w, label_y, idx, label_h):
        # idx 0..n vertical spacing
        y_off = label_y + idx * (label_h + 40)
        track = pygame.Rect(track_x, y_off + label_h + 8, track_w, 12)
        minus = pygame.Rect(track.x - 44, track.y - 6, 36, 28)
        plus = pygame.Rect(track.x + track.w + 8, track.y - 6, 36, 28)
        return track, minus, plus

    def draw(self, screen, menu_x, menu_y, track_x, track_w, label_y, idx, font):
        # draw label
        label_s = font.render(self.label + ':', True, (20, 20, 20))
        screen.blit(label_s, (menu_x + 40, label_y + idx * (font.get_height() + 40)))
        label_h = font.get_height()
        track, minus, plus = self._compute_geometry(menu_x, menu_y, track_x, track_w, label_y, idx, label_h)
        pygame.draw.rect(screen, (220, 220, 220), track, border_radius=6)
        val = self.get()
        try:
            rel = (float(val) - self.min) / float(self.max - self.min)
        except Exception:
            rel = 0.0
        rel = max(0.0, min(1.0, rel))
        filled = int(rel * track.w)
        if filled > 0:
            pygame.draw.rect(screen, (200, 50, 50), (track.x, track.y, filled, track.h), border_radius=6)
        cx = track.x + filled
        # knob
        outer = (255, 255, 255)
        inner = (150, 30, 30)
        mx, my = pygame.mouse.get_pos()
        knob_rect = pygame.Rect(int(cx - self.knob_r), int(track.y + track.h//2 - self.knob_r), self.knob_r*2, self.knob_r*2)
        if self.dragging:
            outer = (255, 240, 240)
            inner = (220, 60, 60)
        elif knob_rect.collidepoint((mx, my)):
            outer = (250, 250, 250)
        try:
            pygame.draw.circle(screen, outer, (cx, track.y + track.h//2), self.knob_r)
            pygame.draw.circle(screen, inner, (cx, track.y + track.h//2), 6)
        except Exception:
            pass
        # +/- buttons
        pygame.draw.rect(screen, (245, 245, 245), minus, border_radius=6)
        pygame.draw.rect(screen, (245, 245, 245), plus, border_radius=6)
        pygame.draw.rect(screen, (160, 160, 160), minus, 2, border_radius=6)
        pygame.draw.rect(screen, (160, 160, 160), plus, 2, border_radius=6)
        minus_s = font.render('-', True, (20, 20, 20))
        plus_s = font.render('+', True, (20, 20, 20))
        screen.blit(minus_s, (minus.x + (minus.w - minus_s.get_width())//2, minus.y + (minus.h - minus_s.get_height())//2))
        screen.blit(plus_s, (plus.x + (plus.w - plus_s.get_width())//2, plus.y + (plus.h - plus_s.get_height())//2))
        # value text
        try:
            val_txt = self.fmt(self.get())
        except Exception:
            val_txt = str(self.get())
        val_s = font.render(val_txt, True, (20,20,20))
        screen.blit(val_s, (track.x + track.w + 56, track.y + (track.h - val_s.get_height())//2))

    def handle_event(self, event, menu_x, menu_y, track_x, track_w, label_y, idx, font):
        label_h = font.get_height()
        track, minus, plus = self._compute_geometry(menu_x, menu_y, track_x, track_w, label_y, idx, label_h)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx,my = event.pos
            if minus.collidepoint((mx,my)):
                # step down
                cur = float(self.get())
                step = (self.max - self.min)/20.0
                self.set(max(self.min, cur - step))
                return True
            if plus.collidepoint((mx,my)):
                cur = float(self.get())
                step = (self.max - self.min)/20.0
                self.set(min(self.max, cur + step))
                return True
            # knob or track
            knob_rect = pygame.Rect(int(track.x - self.knob_r), int(track.y - self.knob_r), track.w + self.knob_r*2, track.h + self.knob_r*2)
            if knob_rect.collidepoint((mx,my)):
                # start dragging and set value
                self.dragging = True
                rel = (mx - track.x) / float(max(1, track.w))
                val = self.min + rel * (self.max - self.min)
                self.set(val)
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx,my = event.pos
                rel = (mx - track.x) / float(max(1, track.w))
                val = self.min + rel * (self.max - self.min)
                self.set(val)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        return False
