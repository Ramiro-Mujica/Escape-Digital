import pygame


def load_pointer(path='assets/puntero.png'):
    try:
        img = pygame.image.load(path).convert_alpha()
        pygame.mouse.set_visible(False)
        return img
    except Exception:
        try:
            pygame.mouse.set_visible(True)
        except Exception:
            pass
        return None


def draw_pointer(screen, puntero_img):
    if puntero_img is None:
        return
    try:
        mx, my = pygame.mouse.get_pos()
        w_win, h_win = screen.get_size()
        target_w = max(20, min(72, int(w_win * 0.04)))
        iw, ih = puntero_img.get_size()
        if iw != target_w:
            target_h = max(12, int(ih * (target_w / iw)))
            scaled = pygame.transform.smoothscale(puntero_img, (target_w, target_h))
        else:
            scaled = puntero_img
        px = mx - scaled.get_width() // 2
        py = my - scaled.get_height() // 2
        screen.blit(scaled, (px, py))
    except Exception:
        pass
