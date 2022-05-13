from threading import Thread
from twisted.internet import reactor, task
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import time
from pyVNC import constants
from pyVNC.constants import *

from pyVNC.Buffer import DisplayBuffer, ArrayBuffer, Buffer
from pyVNC.VNCFactory import VNCFactory
import logging
logger = logging.getLogger("pyVNC")

class Client(Thread):
    def __init__(self, host="127.0.0.1", password=None, port=5902, depth=32, fast=False, shared=True, gui=False, array=False, callbacks=[]):
        Thread.__init__(self)
        pygame.init()
        self.has_gui = gui
        self.screen = DisplayBuffer(array) if gui else ArrayBuffer()
        self.host = host
        self.password = password
        self.port = port
        self.depth = depth
        self.fast = fast
        self.shared = shared
        self.callbacks = callbacks

    def send_key(self, key, duration=0.001):
        if key in constants.MODIFIERS:
            self.screen.protocol.key_event(constants.MODIFIERS[key], down=1)
        elif key in constants.KEYMAPPINGS:
            self.screen.protocol.key_event(constants.KEYMAPPINGS[key], down=1)
        elif type(key) == str:
            self.screen.protocol.key_event(ord(key), down=1)

        time.sleep(duration)

        if key in constants.MODIFIERS:
            self.screen.protocol.key_event(constants.MODIFIERS[key], down=0)
        elif key in constants.KEYMAPPINGS:
            self.screen.protocol.key_event(constants.KEYMAPPINGS[key], down=0)
        elif type(key) == str:
            self.screen.protocol.key_event(ord(key), down=0)

    def send_press(self, key):
        if key in constants.MODIFIERS:
            self.screen.protocol.key_event(constants.MODIFIERS[key], down=1)
        elif key in constants.KEYMAPPINGS:
            self.screen.protocol.key_event(constants.KEYMAPPINGS[key], down=1)
        elif type(key) == str:
            self.screen.protocol.key_event(ord(key), down=1)

    def send_release(self, key):
        if key in constants.MODIFIERS:
            self.screen.protocol.key_event(constants.MODIFIERS[key], down=0)
        elif key in constants.KEYMAPPINGS:
            self.screen.protocol.key_event(constants.KEYMAPPINGS[key], down=0)
        elif type(key) == str:
            self.screen.protocol.key_event(ord(key), down=0)

    def send_mouse(self, event="Left", position=(0, 0)):
        # Left 1, Middle 2, Right 3,
        button_id = None
        if event == "Left":
            button_id = 1
        elif event == "Middle":
            button_id = 2
        elif event == "Right":
            button_id = 4

        self.screen.protocol.pointer_event(position[0], position[1], 0)
        self.screen.protocol.pointer_event(position[0], position[1], button_id)

    def add_callback(self, interval, cb):
        l = task.LoopingCall(cb)
        l.start(interval)

    def run_block(self):
        reactor.connectTCP(
            self.host,  # remote hostname
            self.port,  # TCP port number
            VNCFactory(
                self.screen,  # the application/display
                self.depth,  # color depth
                self.fast,  # if a fast connection is used
                self.password,  # password or none
                int(self.shared),  # shared session flag
            )
        )

        # Create callbacks
        for cb_pair in self.callbacks:
            try:
                fps, cb = cb_pair
                interval = fps / 1000
                self.add_callback(interval, cb)

            except:
                logger.error("Callbacks must be formed as (fps, callback_fn)")

        # run the application
        reactor.callLater(0.1, self.screen.loop)
        task.LoopingCall(self.check_events).start(0.0001)
        reactor.run(installSignalHandlers=False)

    def run(self):
        self.run_block()

    def check_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                reactor.stop()
                pygame.display.quit()
                pygame.quit()
            if e.type == KEYDOWN:
                if e.key in MODIFIERS:
                    self.screen.key_event(MODIFIERS[e.key], down=1)
                elif e.key in KEYMAPPINGS:
                    self.screen.key_event(KEYMAPPINGS[e.key], down=1)
                elif e.unicode:
                    self.screen.key_event(ord(e.unicode), down=0)
                else:
                    print("warning: unknown key %r" % (e))

            if e.type == KEYUP:
                if e.key in MODIFIERS:
                    self.screen.key_event(MODIFIERS[e.key], down=0)
                if e.key in KEYMAPPINGS:
                    self.screen.key_event(KEYMAPPINGS[e.key], down=0)

            if e.type == MOUSEMOTION:
                self.buttons = e.buttons[0] and 1
                self.buttons |= e.buttons[1] and 2
                self.buttons |= e.buttons[2] and 4
                self.screen.pointer_event(e.pos[0], e.pos[1], self.buttons)

            if e.type == MOUSEBUTTONUP:
                if e.button == 1: self.buttons &= ~1
                if e.button == 2: self.buttons &= ~2
                if e.button == 3: self.buttons &= ~4
                if e.button == 4: self.buttons &= ~8
                if e.button == 5: self.buttons &= ~16
                self.screen.pointer_event(e.pos[0], e.pos[1], self.buttons)

            if e.type == MOUSEBUTTONDOWN:
                if e.button == 1: self.buttons |= 1
                if e.button == 2: self.buttons |= 2
                if e.button == 3: self.buttons |= 4
                if e.button == 4: self.buttons |= 8
                if e.button == 5: self.buttons |= 16
                self.screen.pointer_event(e.pos[0], e.pos[1], self.buttons)
