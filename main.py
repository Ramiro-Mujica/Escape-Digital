import pygame
from core.estado import EstadoGlobal
from core.app_controller import AppController


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((900, 600))
    pygame.display.set_caption('Escape Digital')

    estado = EstadoGlobal()
    controller = AppController(pantalla, estado)
    try:
        controller.run()
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
