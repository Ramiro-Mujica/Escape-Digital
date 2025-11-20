import pygame
import random


class PantallaJuego2:
    """Juego 2: Adaptado a la pantalla; opción múltiple con pistas visibles.
    Reproduce la lógica del otro proyecto: hay opciones con atributos y pistas
    mostradas en la parte superior izquierda. Al acertar aparece '¡Correcto!'
    y el botón 'Continuar'.
    """
    def __init__(self, screen, index, titulo):
        self.screen = screen
        self.index = index
        self.titulo = titulo
        self.font_title = pygame.font.SysFont('Verdana', 30, bold=True)
        self.font_text = pygame.font.SysFont('Verdana', 20)
        self.small_font = pygame.font.SysFont('Verdana', 16)

        # opciones serán diccionarios (ahora 9 opciones en total)
        self.opciones = self._generar_opciones(9)
        self.pistas, self.respuesta_correcta = self._generar_pistas(self.opciones)
        self.correct_index = int(self.respuesta_correcta) - 1

        self.btn_rects = [pygame.Rect(0,0, int( (self.screen.get_width()*0.6)//3 ) - 16, 120) for _ in self.opciones]
        self.alert = ''
        self.alert_until = 0
        self.completed = False
        self.cont_rect = pygame.Rect(0,0,240,56)

    def handle_events(self, event):
        if self.completed:
            # only allow continuing after the auto-advance countdown has expired
            now = pygame.time.get_ticks()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx,my = event.pos
                self.cont_rect.center = (self.screen.get_width()//2, self.screen.get_height() - 80)
                if self.cont_rect.collidepoint((mx,my)) and now >= getattr(self, 'auto_advance_until', float('inf')):
                    return 'next'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and now >= getattr(self, 'auto_advance_until', float('inf')):
                return 'next'
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            w,h = self.screen.get_size()
            panel_w = int(w * 0.9)
            panel_h = int(h * 0.9)
            panel_x = (w - panel_w)//2
            panel_y = (h - panel_h)//2
            # layout options vertically
            start_y = panel_y + 140
            # determine grid positions for 3x3
            cols = 3
            gap = 16
            card_w = int((panel_w * 0.62) / cols)
            card_h = 120
            grid_x = panel_x + int(panel_w * 0.32)
            for i, r in enumerate(self.btn_rects):
                col = i % cols
                row = i // cols
                r.w = card_w - 8
                r.h = card_h
                r.x = grid_x + col * (card_w + gap)
                r.y = start_y + row * (card_h + gap)
                if r.collidepoint(event.pos):
                    if i == self.correct_index:
                        self.completed = True
                        now = pygame.time.get_ticks()
                        self.alert = '¡Correcto! Terminaste este juego.'
                        self.alert_until = now + 2000
                        # schedule auto-advance in 5 seconds
                        self.auto_advance_until = now + 5000
                        try:
                            from core.audio import get_audio
                            get_audio().play_effect('success')
                        except Exception:
                            pass
                    else:
                        self.alert = 'Respuesta incorrecta. Intenta de nuevo.'
                        self.alert_until = pygame.time.get_ticks() + 1200
                        try:
                            from core.audio import get_audio
                            get_audio().play_effect('fail')
                        except Exception:
                            pass
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
        return None

    def update(self):
        if self.alert and pygame.time.get_ticks() > self.alert_until:
            self.alert = ''

    def draw(self):
        w,h = self.screen.get_size()
        try:
            bg = pygame.transform.scale(pygame.image.load('assets/area.jpg'), (w, h))
            self.screen.blit(bg, (0,0))
        except Exception:
            try:
                bg = pygame.transform.scale(pygame.image.load('assets/bg_start.jpg'), (w, h))
                self.screen.blit(bg, (0,0))
            except Exception:
                self.screen.fill((18,20,24))

        # Use a large rounded frame that occupies most of the screen
        panel_w = int(w * 0.92)
        panel_h = int(h * 0.9)
        panel_x = (w - panel_w)//2
        panel_y = (h - panel_h)//2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # draw rounded panel so corners are transparent and consistent
        try:
            pygame.draw.rect(panel_surf, (8,8,12,200), panel_surf.get_rect(), border_radius=18)
            pygame.draw.rect(panel_surf, (200,200,200), panel_surf.get_rect(), 3, border_radius=18)
            self.screen.blit(panel_surf, (panel_x, panel_y))
        except Exception:
            panel_surf.fill((8,8,12,200))
            self.screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(self.screen, (200,200,200), panel_rect, 3)

        t = self.font_title.render(self.titulo, True, (240,240,240))
        self.screen.blit(t, (panel_x + 24, panel_y + 18))

        # question + pistas
        q = 'Selecciona la opción correcta para continuar'
        self.screen.blit(self.font_text.render(q, True, (240,240,240)), (panel_x + 30, panel_y + 80))

        # draw pistas: single-column list on left with better spacing and style
        hint_x = panel_x + 24
        hint_y = panel_y + 120
        hint_w = int(panel_w * 0.22)
        # card background for hints area (rounded)
        try:
            hints_bg = pygame.Surface((hint_w, panel_h - 240), pygame.SRCALPHA)
            pygame.draw.rect(hints_bg, (24, 26, 28, 220), hints_bg.get_rect(), border_radius=12)
            pygame.draw.rect(hints_bg, (60, 60, 60), hints_bg.get_rect(), 2, border_radius=12)
            self.screen.blit(hints_bg, (hint_x - 8, hint_y - 8))
        except Exception:
            hints_bg = pygame.Surface((hint_w, panel_h - 240), pygame.SRCALPHA)
            hints_bg.fill((24, 26, 28, 220))
            self.screen.blit(hints_bg, (hint_x - 8, hint_y - 8))
        # show up to 9 hints stacked with clearer typography
        hy = hint_y
        for i, linea in enumerate(self.pistas[:9]):
            surf = self.small_font.render(f"{i+1}. {linea}", True, (255, 230, 180))
            self.screen.blit(surf, (hint_x + 6, hy))
            hy += self.small_font.get_height() + 8

        # draw options as a 3x3 grid to the right of hints
        cols = 3
        gap = 16
        card_w = int((panel_w * 0.66) / cols)
        card_h = 96
        grid_x = panel_x + int(panel_w * 0.32)
        # vertical start for the grid
        start_y = panel_y + 140
        for i, op in enumerate(self.opciones):
            r = self.btn_rects[i]
            col = i % cols
            row = i // cols
            r.w = card_w - 8
            r.h = card_h
            r.x = grid_x + col * (card_w + gap)
            r.y = start_y + row * (card_h + gap)
            # hover highlight
            mx,my = pygame.mouse.get_pos()
            hover = r.collidepoint((mx,my))
            card_col = (245,245,245) if not hover else (255, 250, 230)
            pygame.draw.rect(self.screen, card_col, r, border_radius=12)
            pygame.draw.rect(self.screen, (180,180,180), r, 2, border_radius=12)
            # number badge
            badge = pygame.Rect(r.x+8, r.y+8, 36, 36)
            pygame.draw.ellipse(self.screen, (200,30,30), badge)
            n = self.small_font.render(str(i+1), True, (255,255,255))
            self.screen.blit(n, (badge.x + (badge.w - n.get_width())//2, badge.y + (badge.h - n.get_height())//2))
            # show the option index (badge) and the candidate numeric value prominently
            try:
                # numeric candidate (the value the player must guess) shown prominently
                num_val = str(op.get('numero', ''))
                num_font = pygame.font.SysFont('Verdana', 32, bold=True)
                num_surf = num_font.render(num_val, True, (30,30,30))
                # center the numeric value within the left area of the card (next to badge)
                num_x = r.x + 10 + 44
                num_y = r.y + (r.h - num_surf.get_height())//2
                self.screen.blit(num_surf, (num_x, num_y))
            except Exception:
                # fallback to small symbol if something goes wrong
                try:
                    sym_s = self.font_text.render(str(op.get('simbolo', '')), True, (30,30,30))
                    self.screen.blit(sym_s, (r.x + 26, r.y + (r.h - sym_s.get_height())//2))
                except Exception:
                    pass
            # card title area
            pygame.draw.rect(self.screen, (34,36,38), (r.x + 72, r.y + 8, r.w - 88, 28), border_radius=8)
            self.screen.blit(self.font_text.render(str(op['color']), True, (220,220,220)), (r.x + 80, r.y + 12))
        # continue button when completed
        if self.completed:
            self.cont_rect.center = (panel_x + panel_w//2, panel_y + panel_h - 76)
            now = pygame.time.get_ticks()
            if now < getattr(self, 'auto_advance_until', 0):
                # Do not show color text — colors are irrelevant for the hints.
                # Show symbol (if any) instead to give a neutral visual cue.
                try:
                    sym = str(op.get('simbolo', ''))
                    self.screen.blit(self.font_text.render(sym, True, (220,220,220)), (r.x + 80, r.y + 12))
                except Exception:
                    pass
                pygame.draw.rect(self.screen, (140,140,140), self.cont_rect, 3, border_radius=12)
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

        # only show transient alerts when not already showing the completed modal
        if self.alert and not self.completed:
            a = self.font_text.render(self.alert, True, (255,200,80))
            self.screen.blit(a, (panel_x + 30, (self.cont_rect.y if self.completed else panel_y + panel_h - 100)))

    def _generar_opciones(self, n=9):
        # listas suficientemente largas para crear n opciones
        colores = ["Rojo","Azul","Verde","Amarillo","Violeta","Naranja","Rosa","Marrón","Gris"]
        simbolos = ["★","◆","●","■","▲","=","✦","✶","✸"]
        # generar una lista de números aleatorios únicos para variedad
        numeros = random.sample(list(range(2, 50)), n)
        random.shuffle(colores)
        random.shuffle(simbolos)
        opciones = []
        for i in range(n):
            color = colores[i % len(colores)]
            simbolo = simbolos[i % len(simbolos)]
            numero = numeros[i]
            opciones.append({'color': color, 'simbolo': simbolo, 'numero': numero})
        return opciones

    def _generar_pistas(self, opciones):
        correcto = random.randint(0, len(opciones)-1)
        op = opciones[correcto]
        pistas = []
        # 1: parity
        pistas.append(f"Número {'par' if op['numero']%2==0 else 'impar'}")
        # 2: comparison: Mayor / Menor / Intermedio
        if op['numero'] == max(o['numero'] for o in opciones):
            pistas.append('Mayor')
        elif op['numero'] == min(o['numero'] for o in opciones):
            pistas.append('Menor')
        else:
            pistas.append('Intermedio')
        # 3: multiplicity hint (pick a small divisor and state multiplo/no multiplo)
        divisores = [2, 3, 5, 7]
        d = random.choice(divisores)
        if op['numero'] % d == 0:
            pistas.append(f'Múltiplo de {d}')
        else:
            pistas.append(f'No múltiplo de {d}')
        # Optionally include a second multiplicity hint with a different divisor
        d2 = random.choice([x for x in divisores if x != d])
        if op['numero'] % d2 == 0:
            pistas.append(f'Múltiplo de {d2}')
        else:
            pistas.append(f'No múltiplo de {d2}')

        # limit to 3-4 hints for clarity
        pistas = pistas[:4]
        return pistas, str(correcto+1)
