import pygame
import numpy as np
from pyVNC.constants import *
from twisted.internet import reactor


class Buffer:

    def __init__(self):
        self.canvas = None
        self._canvas = None
        self.protocol = None
        self.size = (None, None)
        self.area = (None, None, None, None)

    def set_protocol(self, protocol):
        self.protocol = protocol

    def set_rfb_size(self, width, height, depth=32):
        self.size = (width, height)
        self.area = (0, 0, width, height)

        self.canvas = pygame.Surface(self.size, 0, 32)

    def update_complete(self):
        pass

    def loop(self):
        pass


class ArrayBuffer(Buffer):

    def __init__(self):
        super().__init__()
        self._canvas = np.ndarray(shape=(10, 10, 3), dtype=np.uint8)

    def update_complete(self):
        self._canvas = pygame.surfarray.array3d(self.canvas).swapaxes(0, 1)

    def get_array(self):
        return self._canvas


class DisplayBuffer(Buffer):

    def __init__(self, include_array):
        super().__init__()
        self.include_array = include_array
        self.window = None
        self.background = None
        self.window_style = 0  # Fullscreen

    def set_rfb_size(self, width, height, depth=32):
        super().set_rfb_size(width, height, depth)

        if depth not in [32, 8]:
            raise ValueError("color depth not supported")

        pygame.mouse.set_cursor(*POINTER)
        pygame.key.set_repeat(500, 30)
        self.window = pygame.display.set_mode(self.size, self.window_style, depth)
        self.background = pygame.Surface(self.size, depth)
        self.background.fill(0)  # black

    def update_complete(self):
        if self.include_array:
            self._canvas = pygame.surfarray.array3d(self.canvas).swapaxes(0, 1)

        self.window.blit(self.canvas, (0, 0))
        pygame.display.update()

    def get_array(self):
        return self._canvas

    def loop(self, dum=None):
        reactor.callLater(0.005, self.loop)

    def key_event(self, key, down):
        self.protocol.key_event(key, down)

    def pointer_event(self, x, y, buttons):
        self.protocol.pointer_event(x, y, buttons)
