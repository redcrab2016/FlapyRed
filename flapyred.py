import pygame as pg
from itertools import cycle
import random
from enum import Enum
from pygame.locals import *


class Flappy:
    class GameState(Enum):
        INIT = 0
        PREPARE = 1
        WELCOME = 2
        FLY = 3
        GAMEOVER = 4
        EXIT = 99

    class GameInput(Enum):
        IDLE = 0
        ACTION = 1
        EXIT = 99

    def __init__(self):
        self.playerHeight = self.crashTest = self.playerFlapped = self.pipeVelX = self.playerVelY = None
        self.playerFlapAcc = self.playerRotThr = self.playerVelRot = self.playerRot = self.playerAccY = None
        self.playerMinVelY = self.playerMaxVelY = self.lowerPipes = self.upperPipes = self.newPipe2 = None
        self.newPipe1 = self.score = self.basex = self.loopIter = self.deltay = self.baseShift = None
        self.messagey = self.messagex = self.playery = self.playerx = self.playerIndexGen = self.playerIndex = None

        self.FPS = 30
        self.SCREENWIDTH = 288
        self.SCREENHEIGHT = 512
        self.PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
        self.BASEY = self.SCREENHEIGHT * 0.79
        # image, sound and hitmask  dicts
        self.IMAGES, self.SOUNDS, self.HITMASKS = {}, {}, {}

        # list of all possible players (tuple of 3 positions of flap)
        self.PLAYERS_LIST = (
            # red bird
            (
                'assets/sprites/redbird-upflap.png',
                'assets/sprites/redbird-midflap.png',
                'assets/sprites/redbird-downflap.png',
            ),
            # blue bird
            (
                'assets/sprites/bluebird-upflap.png',
                'assets/sprites/bluebird-midflap.png',
                'assets/sprites/bluebird-downflap.png',
            ),
            # yellow bird
            (
                'assets/sprites/yellowbird-upflap.png',
                'assets/sprites/yellowbird-midflap.png',
                'assets/sprites/yellowbird-downflap.png',
            ),
        )

        # list of backgrounds
        self.BACKGROUNDS_LIST = (
            'assets/sprites/background-day.png',
            'assets/sprites/background-night.png',
        )

        # list of pipes
        self.PIPES_LIST = (
            'assets/sprites/pipe-green.png',
            'assets/sprites/pipe-red.png',
        )

        self.GAME_STATE = Flappy.GameState.INIT
        self.GAME_STATE_TICK = 0
        self.GAME_HANDLER = {}
        self.GAME_INPUT = Flappy.GameInput.IDLE

        self.SCREEN = None
        self.FPSCLOCK = None

        self.GAME_HANDLER = {
            Flappy.GameState.INIT: Flappy.game_state_init,
            Flappy.GameState.PREPARE: Flappy.game_state_prepare,
            Flappy.GameState.WELCOME: Flappy.game_state_welcome,
            Flappy.GameState.FLY: Flappy.game_state_play,
            Flappy.GameState.GAMEOVER: Flappy.game_state_gameover,
            Flappy.GameState.EXIT: Flappy.game_state_exit
        }

    def play(self):
        self.game_next_state(Flappy.GameState.INIT)
        """ Main Game loop"""
        while self.GAME_STATE != Flappy.GameState.EXIT:
            self.game_input()
            self.GAME_STATE_TICK += 1
            self.GAME_HANDLER[self.GAME_STATE](self)
            self.game_render()

    def game_next_state(self, next_state):
        """Set the next game state"""
        if next_state != self.GAME_STATE:
            self.GAME_STATE = next_state
            self.GAME_STATE_TICK = 0

    def is_game_start_state(self):
        """return true is the game is on first iteration of its current state"""
        return self.GAME_STATE_TICK == 1

    def game_input(self):
        """Translate system input event into game event : exit event will change game state to EXIT"""
        self.GAME_INPUT = Flappy.GameInput.IDLE
        try:
            for event in pg.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.GAME_INPUT = Flappy.GameInput.EXIT
                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    self.GAME_INPUT = Flappy.GameInput.ACTION
        except:
            pass
        if self.GAME_INPUT == Flappy.GameInput.EXIT:
            self.game_next_state(Flappy.GameState.EXIT)

    def game_render(self):
        """ Finalise the rendering by showing up all blit that occurs, then wait enough time to respect FPS"""
        try:
            pg.display.update()
            self.FPSCLOCK.tick(self.FPS)
        except:
            pass

    def game_state_init(self):
        """STATE INIT : prepare all needed resource and prepare the SDL context"""
        print("game init")
        pg.init()
        self.FPSCLOCK = pg.time.Clock()
        self.SCREEN = pg.display.set_mode((self.SCREENWIDTH, self.SCREENHEIGHT))
        pg.display.set_caption('Flappy Bird')

        # numbers sprites for score display
        self.IMAGES['numbers'] = (
            pg.image.load('assets/sprites/0.png').convert_alpha(),
            pg.image.load('assets/sprites/1.png').convert_alpha(),
            pg.image.load('assets/sprites/2.png').convert_alpha(),
            pg.image.load('assets/sprites/3.png').convert_alpha(),
            pg.image.load('assets/sprites/4.png').convert_alpha(),
            pg.image.load('assets/sprites/5.png').convert_alpha(),
            pg.image.load('assets/sprites/6.png').convert_alpha(),
            pg.image.load('assets/sprites/7.png').convert_alpha(),
            pg.image.load('assets/sprites/8.png').convert_alpha(),
            pg.image.load('assets/sprites/9.png').convert_alpha()
        )

        # game over sprite
        self.IMAGES['gameover'] = pg.image.load('assets/sprites/gameover.png').convert_alpha()
        # message sprite for welcome screen
        self.IMAGES['message'] = pg.image.load('assets/sprites/message.png').convert_alpha()
        # base (ground) sprite
        self.IMAGES['base'] = pg.image.load('assets/sprites/base.png').convert_alpha()

        self.SOUNDS['die'] = pg.mixer.Sound('assets/audio/die.ogg')
        self.SOUNDS['hit'] = pg.mixer.Sound('assets/audio/hit.ogg')
        self.SOUNDS['point'] = pg.mixer.Sound('assets/audio/point.ogg')
        self.SOUNDS['swoosh'] = pg.mixer.Sound('assets/audio/swoosh.ogg')
        self.SOUNDS['wing'] = pg.mixer.Sound('assets/audio/wing.ogg')
        self.game_next_state(Flappy.GameState.PREPARE)

    def game_state_prepare(self):
        """STATE PREPARE : prepare the context for a new game play iteration"""
        print("game prepare")
        # select random background sprites
        randBg = random.randint(0, len(self.BACKGROUNDS_LIST) - 1)
        self.IMAGES['background'] = pg.image.load(self.BACKGROUNDS_LIST[randBg]).convert()

        # select random player sprites
        randPlayer = random.randint(0, len(self.PLAYERS_LIST) - 1)
        self.IMAGES['player'] = (
            pg.image.load(self.PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pg.image.load(self.PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pg.image.load(self.PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(self.PIPES_LIST) - 1)
        self.IMAGES['pipe'] = (
            pg.transform.flip(
                pg.image.load(self.PIPES_LIST[pipeindex]).convert_alpha(), False, True),
            pg.image.load(self.PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hitmask for pipes
        self.HITMASKS['pipe'] = (
            Flappy.getHitmask(self.IMAGES['pipe'][0]),
            Flappy.getHitmask(self.IMAGES['pipe'][1]),
        )

        # hitmask for player
        self.HITMASKS['player'] = (
            Flappy.getHitmask(self.IMAGES['player'][0]),
            Flappy.getHitmask(self.IMAGES['player'][1]),
            Flappy.getHitmask(self.IMAGES['player'][2]),
        )
        self.game_next_state(Flappy.GameState.WELCOME)

    def game_state_welcome(self):
        """STATE: WELCOME : Welcome scene"""
        # First interation in current state
        if self.is_game_start_state():
            print("game welcome")
            """Shows welcome screen animation of flappy bird"""
            # index of player to blit on screen
            self.playerIndex = 0
            self.playerIndexGen = cycle([0, 1, 2, 1])
            # iterator used to change playerIndex after every 5th iteration
            self.loopIter = 0

            self.playerx = int(self.SCREENWIDTH * 0.2)
            self.playery = int((self.SCREENHEIGHT - self.IMAGES['player'][0].get_height()) / 2)

            self.messagex = int((self.SCREENWIDTH - self.IMAGES['message'].get_width()) / 2)
            self.messagey = int(self.SCREENHEIGHT * 0.12)

            self.basex = 0
            # amount by which base can maximum shift to left
            self.baseShift = self.IMAGES['base'].get_width() - self.IMAGES['background'].get_width()
        # Process game event
        if self.GAME_INPUT == Flappy.GameInput.ACTION:
            self.game_next_state(Flappy.GameState.FLY)

        # adjust playery, playerIndex, basex
        if (self.loopIter + 1) % 5 == 0:
            self.playerIndex = next(self.playerIndexGen)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 4) % self.baseShift)
        amplitude = 8
        framenum = self.GAME_STATE_TICK
        self.deltay = (framenum % (2 * amplitude) - amplitude) * (-2 * (int(framenum / (2 * amplitude)) % 2) + 1)

        # draw sprites
        self.SCREEN.blit(self.IMAGES['background'], (0, 0))
        self.SCREEN.blit(self.IMAGES['player'][self.playerIndex],
                         (self.playerx, self.playery + self.deltay))
        self.SCREEN.blit(self.IMAGES['message'], (self.messagex, self.messagey))
        self.SCREEN.blit(self.IMAGES['base'], (self.basex, self.BASEY))

    def game_state_play(self):
        """STATE PLAY : The game scene itself"""
        # First interation in current state
        if self.is_game_start_state():
            print("game fly")
            self.score = self.playerIndex = self.loopIter = 0
            self.playerx, self.playery = int(self.SCREENWIDTH * 0.2), self.playery + self.deltay

            self.baseShift = self.IMAGES['base'].get_width() - self.IMAGES['background'].get_width()

            # get 2 new pipes to add to upperPipes lowerPipes list
            self.newPipe1 = self.getRandomPipe()
            self.newPipe2 = self.getRandomPipe()

            # list of upper pipes
            self.upperPipes = [
                {'x': self.SCREENWIDTH + 200, 'y': self.newPipe1[0]['y']},
                {'x': self.SCREENWIDTH + 200 + (self.SCREENWIDTH / 2), 'y': self.newPipe2[0]['y']},
            ]

            # list of lowerpipe
            self.lowerPipes = [
                {'x': self.SCREENWIDTH + 200, 'y': self.newPipe1[1]['y']},
                {'x': self.SCREENWIDTH + 200 + (self.SCREENWIDTH / 2), 'y': self.newPipe2[1]['y']},
            ]

            dt = self.FPSCLOCK.tick(self.FPS) / 1000
            self.pipeVelX = -128 * dt

            # player velocity, max velocity, downward acceleration, acceleration on flap
            self.playerVelY = -9  # player's velocity along Y, default same as playerFlapped
            self.playerMaxVelY = 10  # max vel along Y, max descend speed
            self.playerMinVelY = -8  # min vel along Y, max ascend speed
            self.playerAccY = 1  # players downward acceleration
            self.playerRot = 45  # player's rotation
            self.playerVelRot = 3  # angular speed
            self.playerRotThr = 20  # rotation threshold
            self.playerFlapAcc = -9  # players speed on flapping
            self.playerFlapped = False  # True when player flaps
        # Process game event
        if self.GAME_INPUT == Flappy.GameInput.ACTION:
            if self.playery > -2 * self.IMAGES['player'][0].get_height():
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
                self.SOUNDS['wing'].play()
        # check for crash here
        self.crashTest = self.checkCrash({'x': self.playerx, 'y': self.playery, 'index': self.playerIndex},
                                         self.upperPipes, self.lowerPipes)
        if self.crashTest[0]:
            self.game_next_state(Flappy.GameState.GAMEOVER)
            return

        # check for score
        playerMidPos = self.playerx + self.IMAGES['player'][0].get_width() / 2
        for pipe in self.upperPipes:
            pipeMidPos = pipe['x'] + self.IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score += 1
                self.SOUNDS['point'].play()

        # playerIndex basex change
        if (self.loopIter + 1) % 3 == 0:
            self.playerIndex = next(self.playerIndexGen)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)

        # rotate the player
        if self.playerRot > -90:
            self.playerRot -= self.playerVelRot

        # player's movement
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY
        if self.playerFlapped:
            self.playerFlapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            self.playerRot = 45

        playerHeight = self.IMAGES['player'][self.playerIndex].get_height()
        self.playery += min(self.playerVelY, self.BASEY - self.playery - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if 3 > len(self.upperPipes) > 0 and 0 < self.upperPipes[0]['x'] < 5:
            newPipe = self.getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if len(self.upperPipes) > 0 and self.upperPipes[0]['x'] < -self.IMAGES['pipe'][0].get_width():
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)

        # draw sprites
        self.SCREEN.blit(self.IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            self.SCREEN.blit(self.IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            self.SCREEN.blit(self.IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        self.SCREEN.blit(self.IMAGES['base'], (self.basex, self.BASEY))
        # print score so player overlaps the score
        self.showScore(self.score)

        # Player rotation has a threshold
        visibleRot = self.playerRotThr
        if self.playerRot <= self.playerRotThr:
            visibleRot = self.playerRot

        playerSurface = pg.transform.rotate(self.IMAGES['player'][self.playerIndex], visibleRot)
        self.SCREEN.blit(playerSurface, (self.playerx, self.playery))

    def game_state_gameover(self):
        """STATE GAME OVER : Game Over Scene"""
        if self.is_game_start_state():
            print("game over")
            """crashes the player down and shows gameover image"""
            self.playerx = self.SCREENWIDTH * 0.2
            self.playerHeight = self.IMAGES['player'][0].get_height()
            self.playerAccY = 2
            self.playerVelRot = 7
            # play hit and die sounds
            self.SOUNDS['hit'].play()
            if not self.crashTest[1]:
                self.SOUNDS['die'].play()

        if self.GAME_INPUT == Flappy.GameInput.ACTION:
            if self.playery + self.playerHeight >= self.BASEY - 1:
                self.game_next_state(Flappy.GameState.PREPARE)
                return

        # player y shift
        if self.playery + self.playerHeight < self.BASEY - 1:
            self.playery += min(self.playerVelY, self.BASEY - self.playery - self.playerHeight)

        # player velocity change
        if self.playerVelY < 15:
            self.playerVelY += self.playerAccY

        # rotate only when it's a pipe crash
        if not self.crashTest[1]:
            if self.playerRot > -90:
                self.playerRot -= self.playerVelRot

        # draw sprites
        self.SCREEN.blit(self.IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            self.SCREEN.blit(self.IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            self.SCREEN.blit(self.IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        self.SCREEN.blit(self.IMAGES['base'], (self.basex, self.BASEY))
        self.showScore(self.score)

        playerSurface = pg.transform.rotate(self.IMAGES['player'][1], self.playerRot)
        self.SCREEN.blit(playerSurface, (self.playerx, self.playery))
        self.SCREEN.blit(self.IMAGES['gameover'], (50, 180))

    def game_state_exit(self):
        """STATE EXIT : End of the game. No more play. Release SDL context"""
        print("game exit")
        pg.quit()

    def showScore(self, score):
        """displays score in center of screen"""
        scoreDigits = [int(x) for x in list(str(score))]
        totalWidth = 0  # total width of all numbers to be printed

        for digit in scoreDigits:
            totalWidth += self.IMAGES['numbers'][digit].get_width()

        Xoffset = (self.SCREENWIDTH - totalWidth) / 2

        for digit in scoreDigits:
            self.SCREEN.blit(self.IMAGES['numbers'][digit], (Xoffset, self.SCREENHEIGHT * 0.1))
            Xoffset += self.IMAGES['numbers'][digit].get_width()

    def checkCrash(self, player, upperPipes, lowerPipes):
        """returns True if player collides with base or pipes."""
        pi = player['index']
        player['w'] = self.IMAGES['player'][0].get_width()
        player['h'] = self.IMAGES['player'][0].get_height()

        # if player crashes into ground
        if player['y'] + player['h'] >= self.BASEY - 1:
            return [True, True]
        else:

            playerRect = pg.Rect(player['x'], player['y'],
                                 player['w'], player['h'])
            pipeW = self.IMAGES['pipe'][0].get_width()
            pipeH = self.IMAGES['pipe'][0].get_height()

            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                # upper and lower pipe rects
                uPipeRect = pg.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
                lPipeRect = pg.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

                # player and upper/lower pipe hitmasks
                pHitMask = self.HITMASKS['player'][pi]
                uHitmask = self.HITMASKS['pipe'][0]
                lHitmask = self.HITMASKS['pipe'][1]

                # if bird collided with upipe or lpipe
                uCollide = Flappy.pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
                lCollide = Flappy.pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

                if uCollide or lCollide:
                    return [True, False]

        return [False, False]

    def pixelCollision(rect1, rect2, hitmask1, hitmask2):
        """Checks if two objects collide and not just their rects"""
        rect = rect1.clip(rect2)

        if rect.width == 0 or rect.height == 0:
            return False

        x1, y1 = rect.x - rect1.x, rect.y - rect1.y
        x2, y2 = rect.x - rect2.x, rect.y - rect2.y

        for x in range(rect.width):
            for y in range(rect.height):
                if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                    return True
        return False

    def getRandomPipe(self):
        """returns a randomly generated pipe"""
        # y of gap between upper and lower pipe
        gapY = random.randrange(0, int(self.BASEY * 0.6 - self.PIPEGAPSIZE))
        gapY += int(self.BASEY * 0.2)
        pipeHeight = self.IMAGES['pipe'][0].get_height()
        pipeX = self.SCREENWIDTH + 10

        return [
            {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe
            {'x': pipeX, 'y': gapY + self.PIPEGAPSIZE},  # lower pipe
        ]

    def getHitmask(image):
        """returns a hitmask using an image's alpha."""
        mask = []
        for x in range(image.get_width()):
            mask.append([])
            for y in range(image.get_height()):
                mask[x].append(bool(image.get_at((x, y))[3]))
        return mask


if __name__ == '__main__':
    print("Get ready")
    Flappy().play()
    print("Bye bye")
