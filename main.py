import pygame
from pantallas.pantalla_inicio import PantallaInicio
from pantallas.pantalla_reglas import PantallaReglas
from pantallas.pantalla_juego_cesar import PantallaJuegoCesar
from pantallas.pantalla_juego_quiz import PantallaJuegoQuiz
from pantallas.pantalla_juego_2 import PantallaJuego2
from pantallas.pantalla_juego_parejas import PantallaJuegoParejas
from pantallas.pantalla_juego_simon import PantallaJuegoSimon
from pantallas.pantalla_records import PantallaRecords
from core.estado import EstadoGlobal
from core.gestor_registros import guardar_registro

RULES_TEXTS = [
    "Juego 1 - César:\nRegla: cada letra se desplaza 3 posiciones hacia adelante en el alfabeto.\nEjemplo: para la palabra 'hola' la letra 'h' corresponde a 'k' (h -> k).\nEn el juego verás una palabra CIFRADA y deberás escribir la original. La letra 'ñ' no se considera.",
    "Juego 2 - Minidesafío:\nUn pequeño reto adaptado a la pantalla. Selecciona la respuesta correcta para avanzar. (Interfaz simple adaptada al panel central).",
    "Juego 3 - Parejas (Memory):\nEncuentra las parejas iguales dentro del recuadro central (utilizamos imágenes de assets).\nAl fallar se mostrarán las tarjetas unos instantes y luego se ocultarán. Completa todas las parejas para avanzar.",
    "Juego 4 - Patrón (Simon-lite):\nMemoriza la secuencia mostrada. Cada ronda la secuencia crecerá. Hay una espera aproximada de 3 segundos entre rondas al mostrar el siguiente patrón.\nSe requieren 5 rondas correctas para avanzar.",
    "Juego 5 - Quiz:\nResponde 3 preguntas de diferentes categorías. Si fallas alguna, volverás a la pregunta 1 con nuevas preguntas. Usa las teclas 1, 2, 3 o haz clic en las opciones para responder."
]

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("Scape-Game-Ultimate - Demo flujo")
    reloj = pygame.time.Clock()
    estado = EstadoGlobal()

    try:
        font_title = pygame.font.Font('assets/fonts/escape_room.ttf', 36)
        font_text = pygame.font.Font('assets/fonts/escape_room.ttf', 20)
    except:
        font_title = pygame.font.SysFont('Courier New', 36, bold=True)
        font_text = pygame.font.SysFont('Courier New', 20)

    inicio = PantallaInicio(pantalla, estado)