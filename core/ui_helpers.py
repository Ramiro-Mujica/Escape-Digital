import pygame
from pantallas.pantalla_reglas import draw_persistent_hud as reglas_draw_hud


def draw_persistent_hud(screen, estado, fallback_draw=None):
    """Try to draw HUD using the reglas helper; fallback to provided function."""
    try:
        reglas_draw_hud(screen, estado)
        return
    except Exception:
        pass

    if fallback_draw:
        try:
            fallback_draw(screen, estado)
        except Exception:
            pass


def draw_game_over_modal(screen, remaining_seconds):
    try:
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((6, 6, 8, 220))
        screen.blit(overlay, (0, 0))
        box_w = min(800, int(w * 0.84))
        box_h = min(360, int(h * 0.44))
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2
        box = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(screen, (28, 30, 34), box, border_radius=18)
        pygame.draw.rect(screen, (200, 80, 80), box, 4, border_radius=18)
        title_f = pygame.font.SysFont('Verdana', 36, bold=True)
        title_s = title_f.render('Has perdido todas las vidas', True, (240, 240, 240))
        screen.blit(title_s, (box_x + (box_w - title_s.get_width())//2, box_y + 28))
        sub_f = pygame.font.SysFont('Verdana', 20)
        sub_s = sub_f.render(f'Redirigiendo al inicio en {remaining_seconds} s...', True, (220, 220, 220))
        screen.blit(sub_s, (box_x + (box_w - sub_s.get_width())//2, box_y + 28 + title_s.get_height() + 18))
    except Exception:
        pass
