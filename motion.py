#!/usr/bin/env python
#   Copyright (C) 2010 Antonio Cuni

"""
Prerequisites
=============

To run the program you need:

  - Python

  - pygame

  - opencv and its python bindings

  - PIL (Python Imaging Library)


Usage
=====

- Launch workout.py: a window that displays your webcam should appear

- press any key: after 2 seconds, a shoot is taken: this will be used as the
  "base image" to detect motion

- then, counting begins: every time the program detect that the image captured
  by the webcam has changed from "base" to something different, the counter is
  incremented

- an image is considered different than "base" if the rms difference between
  the two is above a certain threshold. You can change it by changing the
  THRESHOLD constant at the beginning of the module

- to reset the counter, press any key except "q" or "ESC"

- to exit the program, press "q" or "ESC"

"""

__version__='0.1'
__author__ ='Antonio Cuni <anto.cuni@gmail.com>'

import os
import sys
import time
import math

import pygame
from pygame.locals import QUIT, KEYDOWN, K_q, K_ESCAPE, K_r, K_COMMA, K_PERIOD

import Image
import ImageChops
import opencv.highgui


FPS = 25.0
THRESHOLD = 28  # the rms value above which an image is considered different
                # than the base


CAMERA = opencv.highgui.cvCreateCameraCapture(0)

class WebcamDisplay:

    def __init__(self, screen, fps):
        self.screen = screen
        self.fps = fps
        self.exit = False

    def loop(self):
        while not self.exit:
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    sys.exit(0)
                elif event.type == KEYDOWN:
                    if self.keydown(event):
                        return

            img = self.get_image()
            self.process_image(img)
            self.blit_image(img)
            self.post_blit_image(img)
            self.redraw_screen()

    def get_image(self):
        img = opencv.highgui.cvQueryFrame(CAMERA)
        return opencv.adaptors.Ipl2PIL(img)

    def process_image(self, img):
        pass

    def blit_image(self, img):
        pg_img = pygame.image.frombuffer(img.tostring(), img.size, img.mode)
        self.screen.blit(pg_img, (0,0))

    def post_blit_image(self, img):
        pass

    def redraw_screen(self):
        pygame.display.flip()
        pygame.time.delay(int(1000 * 1.0/self.fps))

    def keydown(self, event):
        return True # exit

    def display_text(self, font, txt, pos='center', rect=None):
        if rect is None:
            rect = self.screen.get_rect()
        text = font.render(txt, True, (255, 0, 0))
        textRect = text.get_rect()
        if pos == 'topleft':
            textRect.topleft = (0, 0)
        elif pos == 'topright':
            textRect.topright = rect.topright
        elif pos == 'bottomleft':
            textRect.bottomleft = rect.bottomleft
        elif pos == 'bottomright':
            textRect.bottomright = rect.bottomright
        else: # default: center
            textRect.centerx = rect.centerx
            textRect.centery = rect.centery
        # Blit the text
        self.screen.blit(text, textRect)


class GrabImage(WebcamDisplay):

    COUNTDOWN = 3

    def __init__(self, screen, fps):
        WebcamDisplay.__init__(self, screen, fps)
        self.start = None
        self.bigfont = pygame.font.Font(None, 400)

    def keydown(self, event):
        self.start = 'now'
        return False

    def post_blit_image(self, img):
        if self.start is None:
            return
        elif self.start == 'now':
            self.start = time.time()
        diff = round(self.COUNTDOWN + self.start - time.time())
        self.display_text(self.bigfont, '%d' % diff)
        if diff == 0:
            print 'grabbing base image'
            self.img = img
            self.exit = True


class MotionDetect(WebcamDisplay):

    def __init__(self, screen, fps, threshold, imgbase):
        WebcamDisplay.__init__(self, screen, fps)
        self.threshold = threshold
        self.bigfont = pygame.font.Font(None, 400)
        self.font = pygame.font.Font(None, 50)
        self.state = 'full'
        self.rebase = False
        self.total = 0
        self.info_rect = pygame.Rect(642, 242, WIDTH-642, HEIGHT-242)
        self.set_imgbase(imgbase)
        self.reset_counter()
        #self.click = pygame.mixer.Sound('click.wav')

    def set_imgbase(self, imgbase):
        self.imgbase = imgbase
        thumb = imgbase.resize((320, 240))
        pg_base_thumb = pygame.image.frombuffer(thumb.tostring(), thumb.size, thumb.mode)
        self.pg_base_thumb = pg_base_thumb

    def reset_counter(self):
        self.count = 0
        self.start = time.time()

    def rmsdiff(self, img1, img2):
        "Calculate the root-mean-square difference between two images"
        hist = ImageChops.difference(img1, img2).histogram()
        seq = [h*(i**2) for h, i in zip(hist, range(256))]
        total = sum(seq)
        return math.sqrt(total / (float(img1.size[0]) * img1.size[1]))

    def keydown(self, event):
        if event.key in (K_q, K_ESCAPE):
            return True # exit
        elif event.key == K_r:
            self.rebase = True
        elif event.key == K_COMMA:
            self.threshold -= 1
        elif event.key == K_PERIOD:
            self.threshold += 1
        else:
            self.reset_counter()
        return False

    def process_image(self, img):
        if self.rebase:
            self.rebase = False
            self.set_imgbase(img)
            self.state = 'empty'
            return
        diff = self.rmsdiff(self.imgbase, img)
        print diff
        if diff > self.threshold:
            newstate = 'full'
        else:
            newstate = 'empty'
            
        if self.state != newstate and newstate == 'full':
            #self.click.play()
            os.system('play ok.ogg & 2>/dev/null')
            self.count += 1
            self.total += 1
        self.state = newstate

    def post_blit_image(self, img):
        self.screen.blit(self.pg_base_thumb, (642,0))
        self.screen.fill((0,0,0), self.info_rect)
        self.display_text(self.bigfont, str(self.count))
        diff = int(time.time() - self.start)
        minutes, seconds = divmod(diff, 60)
        self.display_text(self.font, str(self.total), pos='topright', rect=self.info_rect)
        self.display_text(self.font, str(self.threshold), pos='bottomright', rect=self.info_rect)
        self.display_text(self.font, '%d:%02d' % (minutes, seconds), rect=self.info_rect)

WIDTH = 640 + 320 + 2
HEIGHT = 480

def main():
    pygame.init()
    #pygame.mixer.init()
    window = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("Motion detection")
    screen = pygame.display.get_surface()

    # grab the base image
    webcam = GrabImage(screen, FPS)
    webcam.loop()
    baseimg = webcam.img

    webcam = MotionDetect(screen, FPS, THRESHOLD, baseimg)
    webcam.loop()

if __name__ == '__main__':
    main()
