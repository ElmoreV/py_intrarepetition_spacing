# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 17:35:49 2023

@author: Elmor
"""


# Gemaakt door: Elmore Vaal
import pygame

# from pygame import *
# import numpy as np
# from copy import deepcopy


class PyGameLoop:
    """

    Template


    class NewLoop(PyGameLoop):


        def setup(self):
            pass

        def handle_event(self,event):
            pass

        def update(self):
            pass

        def draw(self):
            pass

        def cleanup(self):
            pass


    """

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

    def __init__(self):
        pygame.init()
        # pygame.mixer.init()
        self.scr_w = 1500
        self.scr_h = 900
        self.flags = pygame.DOUBLEBUF  # Speedup drawing
        self.screenSurface = pygame.display.set_mode(
            (self.scr_w, self.scr_h), self.flags, 32
        )
        self.screenSurface.set_alpha(None)  # Speedup drawing
        self.keys = [0, 0, 0, 0]
        self.do_not_draw = False  # To shut down rendering sometimes
        pygame.display.set_caption("pygame render")

        pygame.font.init()  # you have to call this at the start,
        # if you want to use this module.
        # self.font = pygame.font.SysFont('Comic Sans MS', 30)
        self.font_renderers = {None: {32: pygame.font.Font(None, 32)}}

    def setup(self):
        raise NotImplementedError()

    def handle_events(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def draw(self):
        raise NotImplementedError

    def draw_text(self, text, x, y, color=(0, 0, 0), font=None, font_size=32):
        if not font in self.font_renderers:
            self.font_renderers[font] = {
                font_size: pygame.font.SysFont(font, font_size)
            }

        if not font_size in self.font_renderers[font]:
            self.font_renderers[font][font_size] = pygame.font.SysFont(
                font, font_size
            )

        selected_font_renderer = self.font_renderers[font][font_size]

        textSurfaceObj = selected_font_renderer.render(text, True, color)

        textRectObj = textSurfaceObj.get_rect()
        textRectObj.center = (x, y)
        self.screenSurface.blit(textSurfaceObj, textRectObj)

    def cleanup(self):
        raise NotImplementedError()

    def catch_keys(self, event):
        # Catch keys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.keys[self.UP] = 1
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.keys[self.DOWN] = 1
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.keys[self.LEFT] = 1
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.keys[self.RIGHT] = 1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.keys[self.UP] = 0
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.keys[self.DOWN] = 0
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.keys[self.LEFT] = 0
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.keys[self.RIGHT] = 0

    def loop(self, fps=30):
        self.setup()

        # step=0 # current step
        # blank = False # Do or do not clear screen before drawing

        running = True
        restart = False

        self.timer = pygame.time.Clock()
        try:
            while running:
                for event in pygame.event.get():
                    # Exit commands are 'ESC' or 'Q'
                    if (
                        event.type == pygame.QUIT
                        or (
                            event.type == pygame.KEYUP
                            and event.key == pygame.K_ESCAPE
                        )
                        or (
                            event.type == pygame.KEYDOWN
                            and (event.unicode == "q" or event.unicode == "Q")
                        )
                    ):
                        running = False
                    if event.type == pygame.KEYDOWN and (
                        event.unicode == "r" or event.unicode == "R"
                    ):
                        restart = True
                        running = False
                    self.catch_keys(event)

                    self.handle_event(event)
                if running == False:
                    break

                self.update()
                if not self.do_not_draw:
                    self.screenSurface.fill((0, 0, 0))
                    self.draw()
                    pygame.display.flip()
                self.timer.tick(fps)  # 17 Hz
            self.cleanup()
            if restart:
                self.loop(fps)
            else:
                pygame.display.quit()
                pygame.quit()
        except Exception as e:
            self.cleanup()
            pygame.display.quit()
            pygame.quit()
            raise e
