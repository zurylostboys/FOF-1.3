#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyostila                                  #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

#altered by myfingershurt to adapt to Alarian mod

import Player
from Song import Note, Tempo, Bars
from Mesh import Mesh
import Theme
import Config
import Log
import pygame

from OpenGL.GL import *
import math
import os
import random

PLAYER1DRUMS   = [Player.BASS, Player.DRUM1A, Player.DRUM2A, Player.DRUM3A, Player.DRUM4A, Player.DRUM1B, Player.DRUM2B, Player.DRUM3B, Player.DRUM4B]
PLAYER2DRUMS   = [Player.PLAYER_2_BASS, Player.PLAYER_2_DRUM1A,Player.PLAYER_2_DRUM2A, Player.PLAYER_2_DRUM3A, Player.PLAYER_2_DRUM4A,
                  Player.PLAYER_2_DRUM1B, Player.PLAYER_2_DRUM2B, Player.PLAYER_2_DRUM3B, Player.PLAYER_2_DRUM4B] 

#Normal guitar key color order: Green, Red, Yellow, Blue, Orange
#Drum fret color order: Red, Yellow, Blue, Green
#actual drum note numbers:
#0 = bass drum (stretched Orange fret), normally Green fret
#1 = drum Red fret, normally Red fret
#2 = drum Yellow fret, normally Yellow fret
#3 = drum Blue fret, normally Blue fret
#4 = drum Green fret, normally Orange fret

#So, with regard to note number coloring, swap note.number 0's color wih note.number 4.


class Drum:
  def __init__(self, engine, editorMode = False, player = 0):
    self.engine         = engine
    self.isDrum = True
  
    self.lastFretWasBassDrum = False
    self.lastFretWasT1 = False   #Faaa Drum sound
    self.lastFretWasT2 = False
    self.lastFretWasT3 = False
    self.lastFretWasC = False


    self.canGuitarSolo = False
    self.sameNoteHopoString = False

    self.tempoBpm = 120   #MFH - default is NEEDED here...
    
    #death_au: blazingamer's 3D notes put into drums
    self.twoDnote = Theme.twoDnote #blazingamer 
    self.twoDkeys = Theme.twoDkeys #blazingamer 
    
    if self.engine.config.get("game", "large_drum_neck"):
      self.boardWidth     = 4.0
      self.boardLength    = 12.0
    elif self.twoDnote == False or self.twoDkeys == False:
      self.boardWidth     = 3.6 #death_au
      self.boardLength    = 9.0 #death_au
    else:
      self.boardWidth     = 3.0
      self.boardLength    = 9.0

    self.beatsPerBoard  = 5.0
    self.strings        = 4
    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings
    #self.fretColors     = [(0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (.6, .6, .6), (0, 0, 1)]
    self.fretColors     = Theme.fretColors
    self.playedNotes    = []
    self.missedNotes    = []
    self.editorMode     = editorMode
    self.selectedString = 0
    self.time           = 0.0
    self.pickStartPos   = 0
    self.leftyMode      = False
    #self.player         = player


    Log.debug("Drum class initialization!")
    
    self.currentBpm     = 50.0
    self.currentPeriod  = 60000.0 / self.currentBpm
    self.targetBpm      = self.currentBpm
    self.targetPeriod   = 60000.0 / self.targetBpm
    self.lastBpmChange  = -1.0
    self.baseBeat       = 0.0

    #self.indexFps       = self.engine.config.get("video", "fps") #QQstarS
    #########For Animations
    self.Animspeed      = 30#Lower value = Faster animations
    #For Animated Starnotes
    self.indexCount     = 0
    #Alarian, For animated hitglow
    self.HCount         = 0
    self.Hitanim        = True

    #myfingershurt: to keep track of pause status here as well
    self.paused = False

    self.spEnabled = True
    self.starPower = 0
    self.starPowerActive = False
    self.starPowerGained = False
    self.starNotesSet = False
    self.killPoints = False
    self.maxStars = []
    self.starNotes = []

    #get difficulty
    self.difficulty = self.engine.config.get("player%d" %(player), "difficulty")

    self.ScoreMultiplier = 1

      
    #myfingershurt:
    #self.hopoStyle        = self.engine.config.get("game", "hopo_style")
    self.hopoStyle = 0
    self.LastStrumWasChord = False
    self.spRefillMode = self.engine.config.get("game","sp_notes_while_active")
    self.hitglow_color = self.engine.config.get("video", "hitglow_color") #this should be global, not retrieved every fret render.

    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    self.notedisappear = self.engine.config.get("game", "notedisappear")

    self.hitw = self.engine.config.get("game", "hit_window")  #this should be global, not retrieved every BPM change.
    if self.hitw == 0:
      self.hitw = 0.70
    elif self.hitw == 1:
      self.hitw = 1.0
    elif self.hitw == 2:
      self.hitw = 1.2
    else:
      self.hitw = 1

    self.twoChord       = 0
    self.hopoActive     = 0
    
    #myfingershurt: need a separate variable to track whether or not hopos are actually active
    self.wasLastNoteHopod = False
    
    
    self.hopoLast       = -1
    self.hopoColor      = (0, .5, .5)
    self.player         = player
    self.scoreMultiplier = 1

    self.hit = [False, False, False, False, False]

    self.neck = self.engine.config.get("coffee", "neck_choose")

    #Get theme
    #themename = self.engine.config.get("coffee", "themename")
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme
    #if themename == "8bit":
    #  self.theme = 0
    #elif themename == "Gh3":
    #  self.theme = 1
    ##myfingershurt: using Rock Band theme specific file check to determine theme instead of folder name:  
    ##elif themename == "Rb":
    ##elif self.engine.fileExists(os.path.join("Themes",themename,"overdriveneck.png")):
    ##elif self.engine.fileExists(os.path.join("Themes",themename,"overdrive fill.png")):
    #elif self.engine.data.theme == 2:
    #  self.theme = 2
    #else:
    #  self.theme = 0

    if self.theme < 2:    #make board same size as guitar board if GH based theme so it rockmeters dont interfere
      self.boardWidth     = 3.0
      self.boardLength    = 9.0
    
    self.nstype = self.engine.config.get("game", "nstype")
    #MFH- fixing neck speed
    if self.nstype < 3:   #not constant mode: 
      self.speed = self.engine.config.get("coffee", "neckSpeed")*0.01
    else:   #constant mode
      #self.speed = self.engine.config.get("coffee", "neckSpeed")
      self.speed = 400 - self.engine.config.get("coffee", "neckSpeed")    #invert this value

      
    self.bigMax = 1


    if player == 0:
      self.keys = PLAYER1DRUMS 
      self.actions = PLAYER1DRUMS
    else:
      self.keys =  PLAYER2DRUMS
      self.actions = PLAYER2DRUMS
      
    self.setBPM(self.currentBpm)

    engine.loadImgDrawing(self, "glowDrawing", "glow.svg",  textureSize = (128, 128))
    if self.neck == "0":
      self.max = self.engine.config.get("coffee", "max_neck")
      i = random.randint(1,self.max)
      engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+str(i)+".png"),  textureSize = (256, 256))
    else:
      engine.loadImgDrawing(self, "neckDrawing", os.path.join("necks","Neck_"+self.neck+".png"),  textureSize = (256, 256))
    engine.loadImgDrawing(self, "hitflames1Drawing", os.path.join("Themes",themename,"hitflames1.png"),  textureSize = (128, 128))
    engine.loadImgDrawing(self, "hitflames2Drawing", os.path.join("Themes",themename,"hitflames2.png"),  textureSize = (128, 128))

    try:
      engine.loadImgDrawing(self, "hitglowAnim", os.path.join("Themes",themename,"hitglowanimation.png"),  textureSize = (128, 128))
    except IOError:
      engine.loadImgDrawing(self, "hitglowDrawing", os.path.join("Themes",themename,"hitglow.png"),  textureSize = (128, 128))
      engine.loadImgDrawing(self, "hitglow2Drawing", os.path.join("Themes",themename,"hitglow2.png"),  textureSize = (128, 128))
      self.Hitanim = False

    
    if self.twoDkeys == True: #death_au
      #myfingershurt: adding drumfretshacked.png for image-corrected drum fret angles in RB:
      try:
        engine.loadImgDrawing(self, "fretButtons", os.path.join("Themes",themename,"drumfretshacked.png"))    
      except IOError:
        engine.loadImgDrawing(self, "fretButtons", os.path.join("Themes",themename,"FretButtons.png"))
    else: #death_au
      try:  
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("Themes", themename, "key.dae")))
      except IOError:
        engine.resource.load(self,  "keyMesh",  lambda: Mesh(engine.resource.fileName("key.dae")))
        
    #Spinning starnotes or not?
    #self.starspin = self.engine.config.get("video", "Starspin")
    self.starspin = False
    #myfingershurt: allowing any non-Rock Band theme to have spinning starnotes if the SpinNotes.png is available in that theme's folder
    #if self.starspin == True and self.theme == 1:
    #if self.starspin == True and self.theme < 2:
      #myfingershurt: check for SpinNotes, if not there then no animation
      #try:  
      #  engine.loadImgDrawing(self, "noteButtons", os.path.join("Themes",themename,"SpinNotes.png"))
      #except IOError:
      #  self.starspin = False
      #  engine.loadImgDrawing(self, "noteButtons", os.path.join("Themes",themename,"Notes.png"))
    #else:
  
    try:
      engine.loadImgDrawing(self, "noteButtons", os.path.join("Themes",themename,"DrumNotes.png"))
      self.separateDrumNotes = True
    except IOError:
      engine.loadImgDrawing(self, "noteButtons", os.path.join("Themes",themename,"Notes.png"))
      self.separateDrumNotes = False
 
    try:
      engine.loadImgDrawing(self, "centerLines", os.path.join("Themes",themename,"drumcenterlines.png"))
    except IOError:
      #engine.loadImgDrawing(self, "centerLines", os.path.join("Themes",themename,"center_lines.png"))
      self.centerLines = None



    engine.loadImgDrawing(self, "sideBars", os.path.join("Themes",themename,"side_bars.png"))
    engine.loadImgDrawing(self, "bpm_halfbeat", os.path.join("Themes",themename,"bpm_halfbeat.png"))
    engine.loadImgDrawing(self, "bpm_beat", os.path.join("Themes",themename,"bpm_beat.png"))
    engine.loadImgDrawing(self, "bpm_measure", os.path.join("Themes",themename,"bpm_measure.png"))

    if self.theme == 0 or self.theme == 1:
      engine.loadImgDrawing(self, "hitlightning", os.path.join("Themes",themename,"lightning.png"),  textureSize = (128, 128))

      #myfingershurt: the starpower neck file should be in the theme folder... and also not required:
      try:
        engine.loadImgDrawing(self, "oNeck", os.path.join("Themes",themename,"starpowerneck.png"),  textureSize = (256, 256))
      except IOError:
        self.oNeck = None

    elif self.theme == 2:
      engine.loadImgDrawing(self, "OsideBars", os.path.join("Themes",themename,"overdrive side_bars.png"),  textureSize = (256, 256))
      #engine.loadImgDrawing(self, "oCenterLines", os.path.join("Themes",themename,"overdrive center_lines.png"),  textureSize = (256, 256))
      self.oCenterLines = None
      
      #myfingershurt: the overdrive neck file should be in the theme folder... and also not required:
      try:
        engine.loadImgDrawing(self, "oNeck", os.path.join("Themes",themename,"overdriveneck.png"),  textureSize = (256, 256))
      except IOError:
        self.oNeck = None





    #t'aint no tails in drums, yo.
    self.simpleTails = True
    self.tail1 = None
    self.tail2 = None
    self.bigTail1 = None
    self.bigTail2 = None

    #however, lets make them available just in case someone decides they're required:
    engine.loadImgDrawing(self, "tail1", "tail1.png",  textureSize = (128, 128))
    engine.loadImgDrawing(self, "tail2", "tail2.png",  textureSize = (128, 128))
    engine.loadImgDrawing(self, "bigTail1", "bigtail1.png",  textureSize = (128, 128))
    engine.loadImgDrawing(self, "bigTail2", "bigtail2.png",  textureSize = (128, 128))
    

    
    self.hopoColor  = Theme.hopoColor
    self.spotColor = Theme.spotColor   
    self.keyColor = Theme.keyColor
    self.key2Color = Theme.key2Color
    self.tracksColor = Theme.tracksColor
    self.barsColor = Theme.barsColor
    self.flameColors = Theme.flameColors
    self.gh3flameColor = Theme.gh3flameColor
    self.flameSizes = Theme.flameSizes
    self.glowColor  = Theme.glowColor
    self.twoChordMax = self.engine.config.get("player%d" % (player), "two_chord_max")
    self.disableVBPM  = self.engine.config.get("game", "disable_vbpm")
    self.disableNoteSFX  = self.engine.config.get("video", "disable_notesfx")
    self.disableFretSFX  = self.engine.config.get("video", "disable_fretsfx")
    self.disableFlameSFX  = self.engine.config.get("video", "disable_flamesfx")



  def selectPreviousString(self):
    self.selectedString = (self.selectedString - 1) % self.strings

  def selectString(self, string):
    self.selectedString = string % self.strings

  def selectNextString(self):
    self.selectedString = (self.selectedString + 1) % self.strings

  def noteBeingHeld(self):
    noteHeld = False
    #for i in range(0,5):
    #  if self.hit[i] == True:
    #    noteHeld = True
    return noteHeld

  def isKillswitchPossible(self):
    possible = False
    #for i in range(0,5):
    #  if self.hit[i] == True:
    #    possible = True
    return possible



  #def setBPM(self, bpm, hyper = False):
  def setBPM(self, bpm):
    if bpm > 200:
      bpm = 200

    #MFH - Neck speed determination:
    #options = {0: _("BPM"), 1: _("Difficulty"), 2: _("BPM & Diff"), 3: _("Percentage")})
    if self.nstype == 0:    #BPM mode
      self.neckSpeed = (340 - bpm)/self.speed
    elif self.nstype == 1:   #Difficulty mode
      if self.difficulty == 0:    #expert
        self.neckSpeed = 220/self.speed
      elif self.difficulty == 1:
        self.neckSpeed = 250/self.speed
      elif self.difficulty == 2:
        self.neckSpeed = 280/self.speed
      else:   #easy
        self.neckSpeed = 300/self.speed
    elif self.nstype == 2:   #BPM & Diff mode
      if self.difficulty == 0:    #expert
        self.neckSpeed = (226-(bpm/10))/self.speed
      elif self.difficulty == 1:
        self.neckSpeed = (256-(bpm/10))/self.speed
      elif self.difficulty == 2:
        self.neckSpeed = (286-(bpm/10))/self.speed
      else:   #easy
        self.neckSpeed = (306-(bpm/10))/self.speed
    else: #Percentage mode - pre-calculated
      self.neckSpeed = self.speed

    # Alarian: Hitwindows/-margins
    self.earlyMargin       = 250 - bpm/5 - 70*self.hitw
    self.lateMargin        = 250 - bpm/5 - 70*self.hitw
    self.noteReleaseMargin = 200 - bpm/5 - 70*self.hitw


  def setMultiplier(self, multiplier):
    self.ScoreMultiplier = multiplier
    


      
  def renderNeck(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    if self.starPowerActive and self.theme == 0:#8bit
      color = (.3,.7,.9)
    elif self.starPowerActive and self.theme == 1:
      color = (.3,.7,.9)
    else:
      color = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    #myfingershurt: every theme can have oNeck:
    #if self.theme == 2 and self.starPowerActive:
    if self.starPowerActive and self.oNeck:
      self.oNeck.texture.bind()
    else:
      self.neckDrawing.texture.bind()

    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(color[0],color[1],color[2], v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(color[0],color[1],color[2], 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)

  def drawTrack(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return 0.125 * beat / beatsPerUnit    # glorandwarf: was 0.12

    if self.theme == 0 or self.theme == 1:
      size = 2
    else:
      size = 0

    v            = visibility
    w            = self.boardWidth
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    glEnable(GL_TEXTURE_2D)
    #if self.theme == 2 and self.starPowerActive:
    #  self.oCenterLines.texture.bind()
    #else:
    if self.centerLines != None:
      self.centerLines.texture.bind()
    
    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(1, 1, 1, v)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2+size)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2+size)
    
    glColor4f(1, 1, 1, v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1+size)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1+size)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(1, 1, 1, 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()

    glDisable(GL_TEXTURE_2D)

  def drawSideBars(self, visibility, song, pos):
    if not song:
      return

    def project(beat):
      return 0.125 * beat / beatsPerUnit  # glorandwarf: was 0.12

    v            = visibility
    w            = self.boardWidth + 0.15
    l            = self.boardLength

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    offset       = (pos - self.lastBpmChange) / self.currentPeriod + self.baseBeat 

    c = (1,1,1)

    glEnable(GL_TEXTURE_2D)
    if self.theme == 2 and self.starPowerActive:
      self.OsideBars.texture.bind()
    else:
      self.sideBars.texture.bind()
    
    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset - 2 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -2)
    glTexCoord2f(1.0, project(offset - 2 * beatsPerUnit))
    glVertex3f( w / 2, 0, -2)
    
    glColor4f(c[0], c[1], c[2], v)
    glTexCoord2f(0.0, project(offset - 1 * beatsPerUnit))
    glVertex3f(-w / 2, 0, -1)
    glTexCoord2f(1.0, project(offset - 1 * beatsPerUnit))
    glVertex3f( w / 2, 0, -1)
    
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f(-w / 2, 0, l * .7)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit * .7))
    glVertex3f( w / 2, 0, l * .7)
    
    glColor4f(c[0], c[1], c[2], 0)
    glTexCoord2f(0.0, project(offset + l * beatsPerUnit))
    glVertex3f(-w / 2, 0, l)
    glTexCoord2f(1.0, project(offset + l * beatsPerUnit))
    glVertex3f( w / 2, 0, l)
    glEnd()

    glDisable(GL_TEXTURE_2D)

  def drawBPM(self, visibility, song, pos):
    if not song:
      return

    v            = visibility
    w            = self.boardWidth

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    track = song.track[self.player]

    glEnable(GL_TEXTURE_2D)

    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if not isinstance(event, Bars):
        continue   

      glPushMatrix()

      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0
        
      if event.barType == 0: #half-beat
        sw  = 0.1 #width
        self.bpm_halfbeat.texture.bind()
      elif event.barType == 1: #beat
        sw  = 0.1 #width
        self.bpm_beat.texture.bind()
      elif event.barType == 2: #measure
        sw  = 0.1 #width
        self.bpm_measure.texture.bind()

      glColor4f(1, 1, 1, v)
      glBegin(GL_TRIANGLE_STRIP)
      glTexCoord2f(0.0, 1.0)
      glVertex3f(-(w / 2), 0, z + sw)
      glTexCoord2f(0.0, 0.0)
      glVertex3f(-(w / 2), 0, z - sw)
      glTexCoord2f(1.0, 1.0)
      glVertex3f(w / 2,    0, z + sw)
      glTexCoord2f(1.0, 0.0)
      glVertex3f(w / 2,    0, z - sw)
      glEnd()
      glPopMatrix()

    glDisable(GL_TEXTURE_2D)
    
  def renderTracks(self, visibility):
    if self.tracksColor[0] == -1:
      return
    w = self.boardWidth / self.strings
    v = 1.0 - visibility

    if self.editorMode:
      x = (self.strings / 2 - self.selectedString) * w
      s = 2 * w / self.strings
      z1 = -0.5 * visibility ** 2
      z2 = (self.boardLength - 0.5) * visibility ** 2
      
      glColor4f(1, 1, 1, .15)
      
      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(x - s, 0, z1)
      glVertex3f(x + s, 0, z1)
      glVertex3f(x - s, 0, z2)
      glVertex3f(x + s, 0, z2)
      glEnd()

    sw = 0.025
    for n in range(self.strings - 1, -1, -1):
      glBegin(GL_TRIANGLE_STRIP)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -2)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -2)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, -1)
      glVertex3f((n - self.strings / 2) * w + sw, -v, -1)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], (1.0 - v) * .75)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength * .7)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength * .7)
      glColor4f(self.tracksColor[0], self.tracksColor[1], self.tracksColor[2], 0)
      glVertex3f((n - self.strings / 2) * w - sw, -v, self.boardLength)
      glVertex3f((n - self.strings / 2) * w + sw, -v, self.boardLength)
      glEnd()
      v *= 2

    #sw = 0.01
    #c = 0.5
    #c2 = 1
    #if self.TracksType == 1:
    #  c = 0.
    #  c2 = 2                                                               
    #for n in range(self.strings - c2, -1, -1):
    #  glBegin(GL_TRIANGLE_STRIP)
    #  glColor4f(*(self.TracksColor + (0,)))
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w - sw, -v, -2)
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w + sw, -v, -2)
    #  glColor4f(*(self.TracksColor + (visibility * .75,)))
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w - sw, -v, -1)
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w + sw, -v, -1)
    #  glColor4f(*(self.TracksColor + (visibility * .75,)))
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w - sw, -v, self.boardLength * .7)
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w + sw, -v, self.boardLength * .7)
    #  glColor4f(*(self.TracksColor + (0,)))
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w - sw, -v, self.boardLength)
    #  glVertex3f(c + (n - (self.strings - 1) / 2) * w + sw, -v, self.boardLength)
    #  glEnd()
    #  v *= 2
      
      

  def renderBars(self, visibility, song, pos):
    if not song or self.tracksColor[0] == -1:
      return

    #Distance between bars
    #beatsPerUnit = (5.0 * ( self.currentBpm/(self.fakeBpm/2.0))) / self.boardLength
    #currentBeat = pos / (60000.0/self.currentBpm)
    #beat = int(currentBeat)
    #self.barDistance = ((beat+1 - currentBeat) / beatsPerUnit) - ((beat - currentBeat) / beatsPerUnit)
    #if self.hyperS:
    #  self.barDistance = self.barDistance * 1.5
    ##Speed of the bars
    #currentBeat = pos / self.fakePeriod
    #beat = int(currentBeat)
    #self.zB = (beat - currentBeat) / (self.beatsPerBoard / self.boardLength)
    #if self.zB < self.zBa:
    #  self.zBArray.append( abs(self.zB - self.zBa) )
    #  self.barSpeed = - abs(self.zB - self.zBa)
    #else:
    #  add = 0.0
    #  if len(self.zBArray) == 0:
    #    cont = 1.0
    #  else:
    #    cont = len(self.zBArray)
    #  while len(self.zBArray) > 0:
    #    add += self.zBArray[0]
    #    self.zBArray.pop(0)
    #  prom = add / cont
    #  self.barSpeed = - prom
    #self.zBa = self.zB

    w = self.boardWidth
    v = 1.0 - visibility
    sw = 0.02

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    pos         -= self.lastBpmChange
    offset       = pos / self.currentPeriod * beatsPerUnit
    currentBeat  = pos / self.currentPeriod
    beat         = int(currentBeat)

    
    #z = self.Za  + self.barSpeed
    #if z < -3:
    #  z = self.Z2a + self.barSpeed
    #self.Za = z
    #self.Z2a = z + self.barDistance

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glPushMatrix()
    #while z < self.boardLength:      
    while beat < currentBeat + self.beatsPerBoard:
      z = (beat - currentBeat) / beatsPerUnit

      if z > self.boardLength * .8:
        c = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        c = max(0, 1 + z)
      else:
        c = 1.0
        
      glRotate(v * 90, 0, 0, 1)

      if (beat % 1.0) < 0.001:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .75)
      else:
        glColor4f(self.barsColor[0], self.barsColor[1], self.barsColor[2], visibility * c * .5)

      glBegin(GL_TRIANGLE_STRIP)
      glVertex3f(-(w / 2), -v, z + sw)
      glVertex3f(-(w / 2), -v, z - sw)
      glVertex3f(w / 2,    -v, z + sw)
      glVertex3f(w / 2,    -v, z - sw)
      glEnd()      

      if self.editorMode:
        beat += 1.0 / 4.0
      else:
        beat += 1
    glPopMatrix()

    Theme.setSelectedColor(visibility * .5)
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(-w / 2, 0,  sw)
    glVertex3f(-w / 2, 0, -sw)
    glVertex3f(w / 2,  0,  sw)
    glVertex3f(w / 2,  0, -sw)
    glEnd()


  #myfingershurt:
  def renderNote(self, length, sustain, color, flat = False, tailOnly = False, isTappable = False, big = False, fret = 0, spNote = False, isOpen = False):
  #def renderNote(self, visibility, f, length, sustain, color, colortail, tailOnly = False, playedstart = False, playedcontinue = False, hopo = 0, isOpen = False):   
    #if self.jurgenStarted:
    #    mesh = self.jurgenNoteMesh
    #else:
    #    mesh = self.noteMesh
    #if not mesh:
    #  return
    #if playedstart == False:
    #  p = 1
    #elif playedstart == True and playedcontinue == False:
    #  p = 1
    #  colortail = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
    #else:
    #  p = 3   
    #glColor4f(*colortail)
    #if sustain:
    #  if playedstart == False or (playedstart == True and playedcontinue == False):
    #    size = (.075, length + 0.00001)
    #  else:
    #    size = (.125, length + 0.00001)
    #  ## Draw the first part of the tail
    #  self.Poligon1(size[1] - self.tail2Size, colortail)
    #  ## Draw the second part of the tail
    #  self.Poligon2(size[1] - self.tail2Size, colortail)      


    if not self.simpleTails:#Tail Colors
    #if self.theme == 1:#Tail Colors
    #  if big == False and tailOnly == True:
    #    glColor4f(.6,.6,.6,.7)

    #  else:
        glColor4f(1,1,1,1)
    else:
      if big == False and tailOnly == True:
        glColor4f(.2 + .4, .2 + .4, .2 + .4, 1)
      else:
        glColor4f(*color)
        if self.starPowerActive and self.theme == 0 and not color == (0,0,0,1):#8bit
          glColor4f(.3,.7,.9,1)
        elif self.starPowerActive and self.theme == 1 and not color == (0,0,0,1):
          glColor4f(.3,.7,.9,1)

    if flat:
      glScalef(1, .1, 1)

    beatsPerUnit = self.beatsPerBoard / self.boardLength

    if sustain:
      if not length == None:
        size = (.08, length + 0.00001)

        if size[1] > self.boardLength:
          s = self.boardLength
        else:
          s = (length + 0.00001)

        #myfingershurt: so any theme containing appropriate files can use new tails
        #if self.theme == 1:#Tail Graphics
        if not self.simpleTails:
          #if big == False and tailOnly == True:#Missed note
          #  tex1 = self.tail0
          #  tex2 = self.taile0
            
          if big == True and tailOnly == True:
            zsize = .25
            size = (.17, s - zsize)
            if self.starPowerActive and not color == (0,0,0,1):
              tex1 = self.btail6
              tex2 = self.btaile6
            else:
              if fret == 0:
                tex1 = self.btail1
                tex2 = self.btaile1
              elif fret == 1:
                tex1 = self.btail2
                tex2 = self.btaile2
              elif fret == 2:
                tex1 = self.btail3
                tex2 = self.btaile3
              elif fret == 3:
                tex1 = self.btail4
                tex2 = self.btaile4
              elif fret == 4:
                tex1 = self.btail5
                tex2 = self.btaile5
          else:
            zsize = .15
            size = (.1, s - zsize)
            if tailOnly:#Note let go
              tex1 = self.tail0
              tex2 = self.taile0
            else:
              if self.starPowerActive and not color == (0,0,0,1):
                tex1 = self.tail6
                tex2 = self.taile6
              else:
                if fret == 0:
                  tex1 = self.tail1
                  tex2 = self.taile1
                elif fret == 1:
                  tex1 = self.tail2
                  tex2 = self.taile2
                elif fret == 2:
                  tex1 = self.tail3
                  tex2 = self.taile3
                elif fret == 3:
                  tex1 = self.tail4
                  tex2 = self.taile4
                elif fret == 4:
                  tex1 = self.tail5
                  tex2 = self.taile5
        else:
          if big == True and tailOnly == True:
            zsize = .25
            size = (.11, s - zsize)
            tex1 = self.bigTail1
            tex2 = self.bigTail2
          else:
            zsize = .15
            size = (.08, s - zsize)
            tex1 = self.tail1
            tex2 = self.tail2

        glEnable(GL_TEXTURE_2D)
        tex1.texture.bind()

        glBegin(GL_TRIANGLE_STRIP)

        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0], 0, 0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0], 0, 0)
        glTexCoord2f(0.0,1.0)
        glVertex3f(-size[0], 0, size[1])
        glTexCoord2f(1.0,1.0)
        glVertex3f( size[0], 0, size[1])
        glEnd()

        glDisable(GL_TEXTURE_2D)

        glEnable(GL_TEXTURE_2D)
        tex2.texture.bind()

        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0], 0, size[1] - (.01))
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0], 0, size[1] - (.01))
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-size[0], 0, size[1] + (zsize))
        glTexCoord2f(1.0, 1.0)
        glVertex3f( size[0], 0, size[1] + (zsize))
        glEnd()

        glDisable(GL_TEXTURE_2D)

    if tailOnly:
      return

    #myfingershurt: this should be retrieved once at init, not repeatedly in-game whenever tails are rendered.
    #self.notedisappear = self.engine.config.get("game", "notedisappear")
    
    glPushMatrix()
    
    if self.notedisappear == True:#Notes keep on going when missed
      glColor4f(1,1,1,1)#capo
      glScalef(1, 1, 1)#capo
    else:
      if flat:#Notes disappear when missed
        glColor4f(.1,.1,.1,1)
      else:
        glColor4f(1,1,1,1)

    tailOnly == True

    if self.separateDrumNotes:
      if isOpen:
        size = (self.boardWidth/1.9, (self.boardWidth/self.strings)/3.0)
        texSize = (0,1)
        if spNote == True:
          texY = (0.6,0.8)
        else:
          texY = (0.2,0.4)
        #if self.starPowerActive:
        #  texY = (0.8,1)
        #  if isTappable:
        #    texSize = (0.2,0.4)
        #  else:
        #    texSize = (0,0.2)
      
      else:
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
        fret -= 1
        texSize = (fret/4.0,fret/4.0+0.25)
        if spNote == True:
          texY = (0.4,0.6)
        else:
          texY = (0.0,0.2)
    
    else:   #automatically generate drum notes from Notes.png

      #myfingershurt: swapping notes 0 and 4:
      if fret == 0:
        #fret = 4     #fret 4 is angled, get fret 2 :)
        fret = 2
      elif fret == 4:
        fret = 0

    
      if self.theme < 2:
  #      if self.starspin:
  #        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
  #        texSize = (fret/5.0,fret/5.0+0.2)
  #        if spNote == True:
  #          spIndex = 0
  #          self.indexCount = self.indexCount + 1
  
  #          if self.indexCount > self.Animspeed-1:
  #            self.indexCount = 0
  #          spIndex = (self.indexCount * 16 - (self.indexCount * 16) % self.Animspeed) / self.Animspeed
  ##          if self.indexCount > self.indexFps-1:
  ##            self.indexCount = 0
  ##          spIndex = (self.indexCount * 16 - (self.indexCount * 16) % self.indexFps) / self.indexFps
  
  #          if spIndex > 15:
  #            spIndex = 0
  #          if isTappable:
  #            texY = (0.9-spIndex*0.05, 0.925-spIndex*0.05)
  #          else:
  #            texY = (0.875-spIndex*0.05, 0.9-spIndex*0.05)
  #        else:
  #          if isTappable:
  #            texY = (0.025,0.05)
  #          else:
  #            texY = (0,0.025)
  #        if self.starPowerActive:
  #          texY = (0.10,0.125) #QQstarS
  #          if isTappable:
  #            texSize = (0.2,0.4)
  #          else:
  #            texSize = (0,0.2)
  #      else:
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
        texSize = (fret/5.0,fret/5.0+0.2)
        if spNote == True:
          if isTappable:
            texY = (0.6, 0.8)
          else:
            texY = (0.4,0.6)
        else:
          if isTappable:
            texY = (0.2,0.4)
          else:
            texY = (0,0.2)
        if self.starPowerActive:
          texY = (0.8,1)
          if isTappable:
            texSize = (0.2,0.4)
          else:
            texSize = (0,0.2)
            
      elif self.theme == 2:
        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2)
        texSize = (fret/5.0,fret/5.0+0.2)
        if spNote == True:
          if isTappable:
            texY = (3*0.166667, 4*0.166667)
          else:
            texY = (2*0.166667, 3*0.166667)
        else:
          if isTappable:
            texY = (1*0.166667, 2*0.166667)
          else:
            texY = (0, 1*0.166667)
            
        #rock band fret 0 needs to be reversed just like the fret to match angles better 
        if fret == 0:
          texSize = (fret/5.0+0.2,fret/5.0)
        
        #myfingershurt: adding spNote==False conditional so that star notes can appear in overdrive
        if self.starPowerActive and spNote == False:
          if isTappable:
            texY = (5*0.166667, 1)
          else:
            texY = (4*0.166667, 5*0.166667)

      if isOpen:
        size = (self.boardWidth/2.0, (self.boardWidth/self.strings)/40.0)
          
    glEnable(GL_TEXTURE_2D)
    self.noteButtons.texture.bind()


    glBegin(GL_TRIANGLE_STRIP)

    glTexCoord2f(texSize[0],texY[0])
    glVertex3f(-size[0], 0.2, size[1])
    glTexCoord2f(texSize[1],texY[0])
    glVertex3f( size[0], 0.2, size[1])
    glTexCoord2f(texSize[0],texY[1])
    glVertex3f(-size[0], -0.2, -size[1])
    glTexCoord2f(texSize[1],texY[1])
    glVertex3f( size[0], -0.2, -size[1])

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    #glColor4f(*color)
    #glPushMatrix()
    #glEnable(GL_DEPTH_TEST)
    #glDepthMask(1)
    #glShadeModel(GL_SMOOTH)
    #glRotatef(90, 0, 1, 0)
    #glRotatef(-90, 1, 0, 0)
    #glColor3f(.75 * p * color[0], .75 * p * color[1], .75 * p * color[2])
    #if not isOpen:
    #  mesh.render("Mesh")
    #if isOpen:
    #  self.openNoteMesh.render("Mesh")
    #  glColor3f(1, 1, 1)
    #  self.openNoteMesh.render("Mesh_001")
    #  glColor3f(0.25 * p * color[0], 0.25 * p * color[1], 0.25 * p * color[2])
    #  self.openNoteMesh.render("Mesh_002")
    #else:
    #  glColor3f(1, 1, 1)
    #  mesh.render("Mesh_001")
    #  glColor3f(0.25 * p * color[0], 0.25 * p * color[1], 0.25 * p * color[2])
    #  mesh.render("Mesh_002")
    #glDepthMask(0)
    #glPopMatrix()


  #def renderNotes(self, visibility, song, pos):
  def renderNotes(self, visibility, song, pos, killswitch):
    if not song:
      return

    ## Scale the board according to the current tempo
    #if not self.editorMode:
    #  if self.boardSpeed == 0 or self.boardSpeed == 1:
    #    self.beatsPerBoard = 5.0 * (self.fakeBpm / self.fakeCurrentBpm)
    #  elif self.boardSpeed == 2:
    #    self.beatsPerBoard = 5.0 * (self.fakeBpm / self.currentBpm)

    #beatsPerUnit = self.beatsPerBoard / self.boardLength
    #w = self.boardWidth / self.strings
    #track = song.track[self.player]
    self.bigMax = 0

    self.currentPeriod = self.neckSpeed
    self.targetPeriod  = self.neckSpeed

    self.killPoints = False

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    num = 0
    enable = True
    for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
      if isinstance(event, Tempo):
        self.tempoBpm = event.bpm
        if self.lastBpmChange > 0 and self.disableVBPM == True:
            continue
        if (pos - time > self.currentPeriod or self.lastBpmChange < 0) and time > self.lastBpmChange:
          self.baseBeat         += (time - self.lastBpmChange) / self.currentPeriod
          self.targetBpm         = event.bpm
          self.lastBpmChange     = time
          self.setBPM(self.targetBpm) # glorandwarf: was setDynamicBPM(self.targetBpm)
        continue
      
      if not isinstance(event, Note):
        continue

      if (event.noteBpm == 0.0):
        event.noteBpm = self.tempoBpm

      for q in self.starNotes:
        if time == q:
          event.star = True
          enable = False
      for q in self.maxStars:
        if time == q:
          event.finalStar = True
          enable = False
    
    
    ##Maybe make this more efficient
    #for time, event in track.getEvents(pos - self.fakePeriod * 2, pos + self.fakePeriod * self.beatsPerBoard):
    #  if isinstance(event, Tempo):
    #    self.targetBpm = event.bpm
    #    continue
    #  
    #  if not isinstance(event, Note):
    #    continue
    #  if self.jurgenStarted and self.jPowerNotes:
    #    c = self.fretColors[6]
    #  else:  

      c = self.fretColors[event.number]
      
      
      
      isOpen = False
      if event.number == 0: #treat open string note differently
        x  = (self.strings / 2 - .5 - 1.5) * w
        isOpen     = True
        c = self.fretColors[4]          #myfingershurt: need to swap note 0 and note 4 colors for drums:
      else:   #one of the other 4 drum notes
        x  = (self.strings / 2 - .5 - (event.number - 1)) * w
        if event.number == 4:
          c = self.fretColors[0]        #myfingershurt: need to swap note 0 and note 4 colors for drums:

      #z  = ((time - pos) / self.fakePeriod) / beatsPerUnit
      z  = ((time - pos) / self.currentPeriod) / beatsPerUnit
      #z2 = ((time + event.length - pos) / self.fakePeriod) / beatsPerUnit
      z2 = ((time + event.length - pos) / self.currentPeriod) / beatsPerUnit

      if z > self.boardLength * .8:
        f = (self.boardLength - z) / (self.boardLength * .2)
      elif z < 0:
        f = min(1, max(0, 1 + z2))
      else:
        f = 1.0

      color      = (.1 + .8 * c[0], .1 + .8 * c[1], .1 + .8 * c[2], 1 * visibility * f)
      #colortail  = color
      #length     = event.length / self.fakePeriod / beatsPerUnit
      length = 0
      #hopo = event.hopo
      flat       = False
      tailOnly   = False
      spNote = False
      #playedstart = False
      #playedcontinue = False

      #myfingershurt: user setting for starpower refill / replenish notes
      #if self.starPowerActive and self.theme != 2:  #Rock Band theme allows SP notes in overdrive
      if self.starPowerActive:
        if self.spRefillMode == 0:    #mode 0 = no starpower / overdrive refill notes
          self.spEnabled = False
        elif self.spRefillMode == 1 and self.theme != 2:  #mode 1 = overdrive refill notes in RB themes only
          self.spEnabled = False
        #elif self.spRefillMode == 2:   #mode 2 = every theme gets starpower / overdrive refill notes
          #self.spEnabled = True


      if event.star and self.spEnabled:
        spNote = True
      if event.finalStar and self.spEnabled:
        spNote = True
        if event.played or event.hopod:
          if event.flameCount < 1 and not self.starPowerGained:
            if self.starPower < 100:
              self.starPower += 25
            if self.starPower > 100:
              self.starPower = 100
            self.starPowerGained = True

      if enable:
        self.spEnabled = True

      #if event.tappable < 2:
      isTappable = False
      #else:
      #  isTappable = True

      if self.notedisappear == True:#Notes keep on going when missed
        ###Capo###
        if event.played or event.hopod:
          tailOnly = True
          length += z
          z = 0
          if length <= 0:
            continue
        if z < 0 and not (event.played or event.hopod): 
          color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
          flat  = True
        ###endCapo###
      else:#Notes disappear when missed
        if z < 0:
          if event.played or event.hopod:
            tailOnly = True
            length += z
            z = 0
            if length <= 0:
              continue
          else:
            color = (.2 + .4, .2 + .4, .2 + .4, .5 * visibility * f)
            flat  = True

      sustain = False
        
      
      glPushMatrix()
      glTranslatef(x, (1.0 - visibility) ** (event.number + 1), z)
      self.renderNote(length, sustain = sustain, color = color, flat = flat, tailOnly = tailOnly, isTappable = isTappable, fret = event.number, spNote = spNote, isOpen = isOpen)
      glPopMatrix()

    #myfingershurt: end FOR loop / note rendering loop

    #if self.disableNoteSFX == True:
    #  return
    #glBlendFunc(GL_ONE, GL_ONE)
    #for time, event in self.playedNotes:
    #  c = self.fretColors[event.number]
    #  x = (self.strings / 2 - event.number) * w
    #  z = ((time - pos) / self.fakePeriod) / beatsPerUnit
    #  length     = event.length / self.fakePeriod / beatsPerUnit
    #  tailOnly   = False
    #  if event.played or event.hopod:
    #    tailOnly = True
    #    length += z
    #    z = 0
    #    if length <= 0:
    #      continue
    #  sustain = False
    #  if event.length >= 281.0:
    #    sustain = True
    #  glPushMatrix()
    #  glTranslatef(x, 0, z)
    #  for x in range(10):
    #    glScalef(1.05, 1, 1)
    #    glTranslatef(0, .005, 0)
    #    f = 1.0 - (x / 10.0)
    #    color = (f * c[0], f * c[1], f * c[2], 1)
    #    self.renderNote(visibility, f, length, sustain, color = color, colortail = color, tailOnly = tailOnly)
    #  glPopMatrix()
    #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        

  def renderFrets(self, visibility, song, controls):
    w = self.boardWidth / self.strings
    size = (.22, .22)
    v = 1.0 - visibility
    
    glEnable(GL_DEPTH_TEST)
    
    #Hitglow color option - myfingershurt sez this should be a Guitar class global, not retrieved ever fret render in-game...
    #self.hitglow_color = self.engine.config.get("video", "hitglow_color")
    
    for n in range(self.strings):
      f = self.fretWeight[n]
      c = self.fretColors[n + 1]

      if f and (controls.getState(self.keys[0])):
        f += 0.25

      glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      y = v + f / 6
      x = (self.strings / 2 - .5 - n) * w

      if self.twoDkeys == True: #death_au
        
        glPushMatrix()
        glTranslatef(x, v, 0)
        glDepthMask(1)
        glShadeModel(GL_SMOOTH)

        glColor4f(1,1,1,1)

        size = (self.boardWidth/self.strings/2, self.boardWidth/self.strings/2.4)
        whichFret = n+1
        if whichFret == 4:
          whichFret = 0
          #reversing fret 0 since it's angled in Rock Band
          texSize = (whichFret/5.0+0.2,whichFret/5.0)
        else:
        #texSize = (n/5.0,n/5.0+0.2)
          texSize = (whichFret/5.0,whichFret/5.0+0.2)

        texY = (0.0,1.0/3.0)
        if controls.getState(self.keys[n+1]):
          texY = (1.0/3.0,2.0/3.0)
        #myfingershurt: also want to show when alternate drumkeys are pressed!
        if controls.getState(self.keys[n+5]):
          texY = (1.0/3.0,2.0/3.0)
        if self.hit[n]:
          texY = (2.0/3.0,1.0)

        glEnable(GL_TEXTURE_2D)
        self.fretButtons.texture.bind()

        glBegin(GL_TRIANGLE_STRIP)

        glTexCoord2f(texSize[0],texY[0])
        glVertex3f( size[0], 0, size[1])
        glTexCoord2f(texSize[1],texY[0])
        glVertex3f(-size[0], 0, size[1])
        glTexCoord2f(texSize[0],texY[1])
        glVertex3f( size[0], 0, -size[1])
        glTexCoord2f(texSize[1],texY[1])
        glVertex3f(-size[0], 0, -size[1])

        glEnd()

        glDisable(GL_TEXTURE_2D)

        glDepthMask(0)
        glPopMatrix()
        
      else: #death_au
        if n == 3:
          c = self.fretColors[0]
        else:
          c = self.fretColors[n + 1]
      
        if self.keyMesh:
          glPushMatrix()
          glTranslatef(x, y + v * 6, 0)
          glDepthMask(1)
          glEnable(GL_LIGHTING)
          glEnable(GL_LIGHT0)
          glShadeModel(GL_SMOOTH)
          glRotatef(90, 0, 1, 0)
          glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 10.0, -10.0, 0.0))
          glLightfv(GL_LIGHT0, GL_AMBIENT,  (.2, .2, .2, 0.0))
          glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 0.0))
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)
          glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)

          #Mesh - Main fret
          #Key_001 - Top of fret (key_color)
          #Key_002 - Bottom of fret (key2_color)
          #Glow_001 - Only rendered when a note is hit along with the glow.svg
        
          if(self.keyMesh.find("Glow_001")) == True:
            self.keyMesh.render("Mesh")
            glColor3f(self.keyColor[0], self.keyColor[1], self.keyColor[2])
            self.keyMesh.render("Key_001")
            glColor3f(self.key2Color[0], self.key2Color[1], self.key2Color[2])
            self.keyMesh.render("Key_002")
          else:
            self.keyMesh.render()
          
          glDisable(GL_LIGHTING)
          glDisable(GL_LIGHT0)
          glDepthMask(0)
          glPopMatrix()
      ######################
      f = self.fretActivity[n]

      #if self.keyMesh:
      #  glPushMatrix()
      #  glTranslatef(x, y + v * 6, 0)
      #  glDepthMask(1)
      #  glEnable(GL_LIGHTING)
      #  glEnable(GL_LIGHT0)
      #  glShadeModel(GL_SMOOTH)
      #  glRotatef(90, 0, 1, 0)
      #  glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 10.0, -10.0, 0.0))
      #  glLightfv(GL_LIGHT0, GL_AMBIENT,  (.2, .2, .2, 0.0))
      #  glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 0.0))
      #  glRotatef(-90, 1, 0, 0)
      #  glRotatef(-90, 0, 0, 1)
      #  glColor4f(.1 + .8 * c[0] + f, .1 + .8 * c[1] + f, .1 + .8 * c[2] + f, visibility)
      #  self.keyMesh.render("Mesh")
      #  glColor3f(self.keyColor[0], self.keyColor[1], self.keyColor[2])
      #  self.keyMesh.render("Mesh_001")
      #  glColor3f(self.key2Color[0], self.key2Color[1], self.key2Color[2])
      #  self.keyMesh.render("Mesh_002")
      #  glDisable(GL_LIGHTING)
      #  glDisable(GL_LIGHT0)
      #  glDepthMask(0)
      #  glPopMatrix()

      if f and self.disableFretSFX != True:
        glBlendFunc(GL_ONE, GL_ONE)

        if self.glowColor[0] == -1:
          s = 1.0
        else:
          s = 0.0
        
        while s < 1:
          ms = s * (math.sin(self.time) * .25 + 1)
          if self.glowColor[0] == -2:
            glColor3f(c[0] * (1 - ms), c[1] * (1 - ms), c[2] * (1 - ms))
          else:
            glColor3f(self.glowColor[0] * (1 - ms), self.glowColor[1] * (1 - ms), self.glowColor[2] * (1 - ms))
          
          glPushMatrix()
          glTranslate(x, y, 0)
          glScalef(.1 + .02 * ms * f, .1 + .02 * ms * f, .1 + .02 * ms * f)
          glRotatef( 90, 0, 1, 0)
          glRotatef(-90, 1, 0, 0)
          glRotatef(-90, 0, 0, 1)
          if self.twoDkeys == False: #death_au
            if(self.keyMesh.find("Glow_001")) == True:
              self.keyMesh.render("Glow_001")
            else:
              self.keyMesh.render()
          glPopMatrix()
          s += 0.2
        #Hitglow color
        if self.hitglow_color == 0:
          glColor3f(c[0], c[1], c[2])#Same as fret
        elif self.hitglow_color == 1:
          glColor3f(1, 1, 1)#Actual color in .svg-file
        glEnable(GL_TEXTURE_2D)
        self.glowDrawing.texture.bind()
        f += 2

        glPushMatrix()
        glTranslate(x, y, 0)
        glRotate(f * 90 + self.time, 0, 1, 0)
        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-size[0] * f, 0, -size[1] * f)
        glTexCoord2f(1.0, 0.0)
        glVertex3f( size[0] * f, 0, -size[1] * f)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-size[0] * f, 0,  size[1] * f)
        glTexCoord2f(1.0, 1.0)
        glVertex3f( size[0] * f, 0,  size[1] * f)
        glEnd()
        glPopMatrix()
      
        glDisable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

      self.hit[n] = False
    glDisable(GL_DEPTH_TEST)

        
        
    #    s = 0.0
    #    while s < 1:
    #      ms = s * (math.sin(self.time) * .25 + 1)
    #      glColor3f(c[0] * (1 - ms), c[1] * (1 - ms), c[2] * (1 - ms))
    #      glPushMatrix()
    #      glTranslate(x, y, 0)
    #      glScalef(1 + .6 * ms * f, 1 + .6 * ms * f, 1 + .6 * ms * f)
    #      glRotatef( 90, 0, 1, 0)
    #      glRotatef(-90, 1, 0, 0)
    #      glRotatef(-90, 0, 0, 1)
    #      glColor3f(.50 * c[0] * (1 - ms), .50 * c[1] * (1 - ms), .50 * c[2] * (1 - ms))
    #      self.keyMesh.render("Mesh_003")
    #      glPopMatrix()
    #      s += 0.2
    #    glColor3f(c[0], c[1], c[2])
    #    glEnable(GL_TEXTURE_2D)
    #    self.glowDrawing.texture.bind()
    #    f += 2
    #    glPushMatrix()
    #    glTranslate(x, y, 0)
    #    glRotate(f * 90 + self.time, 0, 1, 0)
    #    glBegin(GL_TRIANGLE_STRIP)
    #    glTexCoord2f(0.0, 0.0)
    #    glVertex3f(-size[0] * f, 0, -size[1] * f)
    #    glTexCoord2f(1.0, 0.0)
    #    glVertex3f( size[0] * f, 0, -size[1] * f)
    #    glTexCoord2f(0.0, 1.0)
    #    glVertex3f(-size[0] * f, 0,  size[1] * f)
    #    glTexCoord2f(1.0, 1.0)
    #    glVertex3f( size[0] * f, 0,  size[1] * f)
    #    glEnd()
    #    glPopMatrix()
    #    glDisable(GL_TEXTURE_2D)
    #    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)       
    #  v *= 1.5
    #glDisable(GL_DEPTH_TEST)


  def renderFlames(self, visibility, song, pos, controls):
    if not song or self.flameColors[0][0][0] == -1:
      return

    beatsPerUnit = self.beatsPerBoard / self.boardLength
    w = self.boardWidth / self.strings
    track = song.track[self.player]

    size = (.22, .22)
    v = 1.0 - visibility

    #if self.disableFlame1SFX != True:
    if self.disableFlameSFX != True:
      for n in range(self.strings):
        f = self.fretWeight[n]
        
        #c = self.fretColors[n]
        c = self.fretColors[n+1]
        if f and controls.getState(self.keys[0]):
          f += 0.25      
        y = v + f / 6

        x = (self.strings / 2 -.5 - n) * w


        f = self.fretActivity[n]

        if f:
          ms = math.sin(self.time) * .25 + 1
          ff = f
          ff += 1.2
          
          glBlendFunc(GL_ONE, GL_ONE)

          flameSize = self.flameSizes[self.scoreMultiplier - 1][n]
          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
            flameColor = self.gh3flameColor
          else:
            flameColor = self.flameColors[self.scoreMultiplier - 1][n]
          #Below was an if that set the "flame"-color to the same as the fret color if there was no specific flamecolor defined.
          #if flameColor[0] == -2:
          #  flameColor = self.fretColors[n]

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.9710526315789473684210526315789
          flameColorMod2 = 10.592592592592592592592592592593
          
          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              glColor3f(.3,.7,.9)
            else: #Default starcolor (Rockband)
              glColor3f(.9,.9,.9)

          if not self.Hitanim:   
            glEnable(GL_TEXTURE_2D)
            self.hitglowDrawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .125, 0)
            glRotate(90, 1, 0, 0)
            glScalef(0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)
            #Alarian: Animated hitflames
          else:
            self.HCount = self.HCount + 1
            if self.HCount > self.Animspeed-1:
              self.HCount = 0
            HIndex = (self.HCount * 16 - (self.HCount * 16) % self.Animspeed) / self.Animspeed
            if HIndex > 15:
              HIndex = 0
            texX = (HIndex*(1/16.0), HIndex*(1/16.0)+(1/16.0))

            glColor3f(1,1,1)
            glEnable(GL_TEXTURE_2D)
            self.hitglowAnim.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .225, 0)
            glRotate(90, 1, 0, 0)
            
            #glScalef(1.3, 1, 2)
            #glScalef(1.7, 1, 2.6)
            glScalef(2, 1, 2.9)   #worldrave correct flame size

            
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(texX[0], 0.0)#upper left corner of frame square in .png
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)#"upper left" corner of surface that texture is rendered on
            glTexCoord2f(texX[1], 0.0)#upper right
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(texX[0], 1.0)#lower left
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(texX[1], 1.0)#lower right
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)

          ff += .3

          #flameSize = self.flameSizes[self.scoreMultiplier - 1][n]
          #flameColor = self.flameColors[self.scoreMultiplier - 1][n]

          flameColorMod0 = 1.1973333333333333333333333333333
          flameColorMod1 = 1.7842105263157894736842105263158
          flameColorMod2 = 12.222222222222222222222222222222
          
          glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
          if self.starPowerActive:
            if self.theme == 0 or self.theme == 1: #GH3 starcolor
              glColor3f(.3,.7,.9)
            else: #Default starcolor (Rockband)
              glColor3f(.8,.8,.8)

          if not self.Hitanim: 
            glEnable(GL_TEXTURE_2D)
            self.hitglow2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .25, .05)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)
          
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

          self.hit[n] = True

















          
          #firesize = (.075, .075)
          #firecolor = self.fireColor[n][self.ScoreMultiplier - 1]
          #firecolor = (firecolor[0] * 1.1973333333333333333333333333333, firecolor[1] * 1.9710526315789473684210526315789, firecolor[2] * 10.592592592592592592592592592593)
          #glColor3f(firecolor[0], firecolor[1], firecolor[2])
          #glEnable(GL_TEXTURE_2D)
          #self.hitglowDrawing.texture.bind()    
          #glPushMatrix()
          #glTranslate(x, y +.125, 0)
          #glRotate(90, 1, 0, 0)
          #glScalef(0.5 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
          #glBegin(GL_TRIANGLE_STRIP)
          #glTexCoord2f(0.0, 0.0)
          #glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
          #glTexCoord2f(1.0, 0.0)
          #glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
          #glTexCoord2f(0.0, 1.0)
          #glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
          #glTexCoord2f(1.0, 1.0)
          #glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
          #glEnd()
          #glPopMatrix()
          #glDisable(GL_TEXTURE_2D)
          #ff += .3
          #firesize = (.075, .075)
          #firecolor = self.fireColor[n][self.ScoreMultiplier - 1]
          #firecolor = (firecolor[0] * 1.1973333333333333333333333333333, firecolor[1] * 1.7842105263157894736842105263158, firecolor[2] * 12.222222222222222222222222222222)
          #glColor3f(firecolor[0], firecolor[1], firecolor[2])
          #glEnable(GL_TEXTURE_2D)
          #self.hitglow2Drawing.texture.bind()    
          #glPushMatrix()
          #glTranslate(x, y + .25, .05)
          #glRotate(90, 1, 0, 0)
          #glScalef(.40 + .6 * ms * ff, 1.5 + .6 * ms * ff, 1 + .6 * ms * ff)
          #glBegin(GL_TRIANGLE_STRIP)
          #glTexCoord2f(0.0, 0.0)
          #glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
          #glTexCoord2f(1.0, 0.0)
          #glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
          #glTexCoord2f(0.0, 1.0)
          #glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
          #glTexCoord2f(1.0, 1.0)
          #glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
          #glEnd()
          #glPopMatrix()
          #glDisable(GL_TEXTURE_2D)
          #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


    #if self.disableFlame2SFX != True:
    if self.disableFlameSFX != True:
      flameLimit = 10.0
      flameLimitHalf = round(flameLimit/2.0)
      for time, event in track.getEvents(pos - self.currentPeriod * 2, pos + self.currentPeriod * self.beatsPerBoard):
        if isinstance(event, Tempo):
          continue
        
        if not isinstance(event, Note):
          continue
        
        if (event.played or event.hopod) and event.flameCount < flameLimit:
          ms = math.sin(self.time) * .25 + 1

          if event.number == 0:
            x  = (self.strings / 2 - 2) * w
          else:
            x  = (self.strings / 2 +.5 - event.number) * w
          #x  = (self.strings / 2 - event.number) * w

          xlightning = (self.strings / 2 - event.number)*2.2*w
          ff = 1 + 0.25       
          y = v + ff / 6
          glBlendFunc(GL_ONE, GL_ONE)

          if self.theme == 2:
            y -= 0.5
          
          flameSize = self.flameSizes[self.scoreMultiplier - 1][event.number]
          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
            flameColor = self.gh3flameColor
          else:
            flameColor = self.flameColors[self.scoreMultiplier - 1][event.number]
          if flameColor[0] == -2:
            flameColor = self.fretColors[event.number]
          
          ff += 1.5 #ff first time is 2.75 after this

          if event.flameCount < flameLimitHalf:
            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.1,.1,.1)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y + .20, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.25 + .6 * ms * ff, event.flameCount/6.0 + .6 * ms * ff, event.flameCount / 6.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D) 

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.1,.1,.1)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .25 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff, (event.flameCount + 1) / 5.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.2,.2,.2)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff, (event.flameCount + 1) / 5.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)

            glColor3f(flameColor[0], flameColor[1], flameColor[2])
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.3,.3,.3)
            glEnable(GL_TEXTURE_2D)
            self.hitflames2Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x, y +.25 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1)/ 4.7 + .6 * ms * ff, (event.flameCount + 1) / 4.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()	  
            glDisable(GL_TEXTURE_2D)
          else:
            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.theme == 0 and event.finalStar and self.spEnabled:
              glColor3f(1,1,1)#lightning color
            elif self.theme == 1 and event.finalStar and self.spEnabled:
              glColor3f(1,1,1)#lightning color
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: 
                glColor3f(.3,.7,.9)#GH3 starcolor
              else:
                glColor3f(.4,.4,.4)#Default starcolor (Rockband)
            glEnable(GL_TEXTURE_2D)
            if self.theme == 0 and event.finalStar and self.spEnabled:
              self.hitlightning.texture.bind()
              wid, hei, = self.engine.view.geometry[2:4]
              glPushMatrix()
              glTranslate(xlightning, y, 3.3)
              glRotate(90, 1, 0, 0)
              glScalef(.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f( .4, 0, -2)
              glTexCoord2f(1.0, 0.0)
              glVertex3f(-.4, 0, -2)
              glTexCoord2f(0.0, 1.0)
              glVertex3f( .4, 0,  2)
              glTexCoord2f(1.0, 1.0)
              glVertex3f(-.4, 0,  2)
            elif self.theme == 1 and event.finalStar and self.spEnabled:
              self.hitlightning.texture.bind()
              wid, hei, = self.engine.view.geometry[2:4]
              glPushMatrix()
              glTranslate(xlightning, y, 3.3)
              glRotate(90, 1, 0, 0)
              glScalef(.15 + .5 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, 2)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f( .4, 0, -2)
              glTexCoord2f(1.0, 0.0)
              glVertex3f(-.4, 0, -2)
              glTexCoord2f(0.0, 1.0)
              glVertex3f( .4, 0,  2)
              glTexCoord2f(1.0, 1.0)
              glVertex3f(-.4, 0,  2)
            else:
              self.hitflames1Drawing.texture.bind()
              glPushMatrix()
              glTranslate(x, y + .35, 0)
              glRotate(90, 1, 0, 0)
              glScalef(.25 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff, event.flameCount / 3.0 + .6 * ms * ff)
              glBegin(GL_TRIANGLE_STRIP)
              glTexCoord2f(0.0, 0.0)
              glVertex3f(-flameSize * ff, 0, -flameSize * ff)
              glTexCoord2f(1.0, 0.0)
              glVertex3f( flameSize * ff, 0, -flameSize * ff)
              glTexCoord2f(0.0, 1.0)
              glVertex3f(-flameSize * ff, 0,  flameSize * ff)
              glTexCoord2f(1.0, 1.0)
              glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)      
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.5,.5,.5)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x - .005, y + .40 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.30 + .6 * ms * ff, (event.flameCount + 1)/ 2.5 + .6 * ms * ff, (event.flameCount + 1) / 2.5 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.6,.6,.6)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x + .005, y + .35 + .005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.35 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff, (event.flameCount + 1) / 2.0 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)

            flameColorMod0 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod1 = 0.1 * (flameLimit - event.flameCount)
            flameColorMod2 = 0.1 * (flameLimit - event.flameCount)
            
            glColor3f(flameColor[0] * flameColorMod0, flameColor[1] * flameColorMod1, flameColor[2] * flameColorMod2)
            if self.starPowerActive:
              if self.theme == 0 or self.theme == 1: #GH3 starcolor
                glColor3f(.3,.7,.9)
              else: #Default starcolor (Rockband)
                glColor3f(.7,.7,.7)
            glEnable(GL_TEXTURE_2D)
            self.hitflames1Drawing.texture.bind()    
            glPushMatrix()
            glTranslate(x+.005, y +.35 +.005, 0)
            glRotate(90, 1, 0, 0)
            glScalef(.40 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff, (event.flameCount + 1) / 1.7 + .6 * ms * ff)
            glBegin(GL_TRIANGLE_STRIP)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(-flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(1.0, 0.0)
            glVertex3f( flameSize * ff, 0, -flameSize * ff)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(-flameSize * ff, 0,  flameSize * ff)
            glTexCoord2f(1.0, 1.0)
            glVertex3f( flameSize * ff, 0,  flameSize * ff)
            glEnd()
            glPopMatrix()  
            glDisable(GL_TEXTURE_2D)
         

          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          event.flameCount += 1



















      #firelimit = 10.0
      #halffirelimit = round(firelimit/2.0)
      #for time, event in track.getEvents(pos - self.fakePeriod * 2, pos + self.fakePeriod * self.beatsPerBoard):
      #  if isinstance(event, Tempo):
      #    continue
      #  if not isinstance(event, Note):
      #    continue
      #  if (event.played or event.hopod) and event.firecount < firelimit:
      #    ms = math.sin(self.time) * .25 + 1
      #    if event.number == 0:
      #      x  = (self.strings / 2 - 2) * w
      #    else:
      #      x  = (self.strings / 2 +.5 - event.number) * w
      #    ff = 1 + 0.25       
      #    y = v + ff / 6
      #    glBlendFunc(GL_ONE, GL_ONE)
      #    firesize = self.fireSize[event.number][self.ScoreMultiplier - 1]
      #    firecolor = self.fireColor[event.number][self.ScoreMultiplier - 1]
      #    ff += 1.5
      #    if event.firecount < halffirelimit:
      #      glColor3f(firecolor[0], firecolor[1], firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames2Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x, y + .20, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.25 + .6 * ms * ff, event.firecount/6.0 + .6 * ms * ff, event.firecount/6.0 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()
      #      glDisable(GL_TEXTURE_2D) 
      #      glColor3f(firecolor[0], firecolor[1], firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames2Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x-.005, y +.25 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.30 + .6 * ms * ff, (event.firecount+1)/5.5 + .6 * ms * ff, (event.firecount+1)/5.5 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()	  
      #      glDisable(GL_TEXTURE_2D)
      #      glColor3f(firecolor[0], firecolor[1], firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames2Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x+.005, y +.25 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.35 + .6 * ms * ff, (event.firecount+1)/5.0 + .6 * ms * ff, (event.firecount+1)/5.0 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()	  
      #      glDisable(GL_TEXTURE_2D)
      #      glColor3f(firecolor[0], firecolor[1], firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames2Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x, y +.25 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.40 + .6 * ms * ff, (event.firecount+1)/4.7 + .6 * ms * ff, (event.firecount+1)/4.7 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()	  
      #      glDisable(GL_TEXTURE_2D)
      #    else:
      #      glColor3f(0.1*(firelimit-event.firecount)* firecolor[0], 0.1*(firelimit-event.firecount)* firecolor[1], 0.1*(firelimit-event.firecount)* firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames1Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x, y +.35, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.25 + .6 * ms * ff, event.firecount/3.0 + .6 * ms * ff, event.firecount/3.0 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()
      #      glDisable(GL_TEXTURE_2D)
      #      glColor3f(0.1*(firelimit-event.firecount)* firecolor[0], 0.1*(firelimit-event.firecount)* firecolor[1], 0.1*(firelimit-event.firecount)* firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames1Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x-.005, y +.40 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.30 + .6 * ms * ff, (event.firecount+1)/2.5 + .6 * ms * ff, (event.firecount+1)/2.5 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()  
      #      glDisable(GL_TEXTURE_2D)
      #      glColor3f(0.1*(firelimit-event.firecount)* firecolor[0], 0.1*(firelimit-event.firecount)* firecolor[1], 0.1*(firelimit-event.firecount)* firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames1Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x+.005, y +.35 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.35 + .6 * ms * ff, (event.firecount+1)/2.0 + .6 * ms * ff, (event.firecount+1)/2.0 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()  
      #      glDisable(GL_TEXTURE_2D)
      #      glColor3f(0.1*(firelimit-event.firecount)* firecolor[0], 0.1*(firelimit-event.firecount)* firecolor[1], 0.1*(firelimit-event.firecount)* firecolor[2])
      #      glEnable(GL_TEXTURE_2D)
      #      self.hitflames1Drawing.texture.bind()    
      #      glPushMatrix()
      #      glTranslate(x+.005, y +.35 +.005, 0)
      #      glRotate(90, 1, 0, 0)
      #      glScalef(.40 + .6 * ms * ff, (event.firecount+1)/1.7 + .6 * ms * ff, (event.firecount+1)/1.7 + .6 * ms * ff)
      #      glBegin(GL_TRIANGLE_STRIP)
      #      glTexCoord2f(0.0, 0.0)
      #      glVertex3f(-firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(1.0, 0.0)
      #      glVertex3f( firesize[0] * ff, 0, -firesize[1] * ff)
      #      glTexCoord2f(0.0, 1.0)
      #      glVertex3f(-firesize[0] * ff, 0,  firesize[1] * ff)
      #      glTexCoord2f(1.0, 1.0)
      #      glVertex3f( firesize[0] * ff, 0,  firesize[1] * ff)
      #      glEnd()
      #      glPopMatrix()  
      #      glDisable(GL_TEXTURE_2D)
      #    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      #    event.firecount += 1
        

  #def render(self, visibility, song, pos, controls):
  def render(self, visibility, song, pos, controls, killswitch):
  

    if not self.starNotesSet == True:
      totalNotes = 0
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        totalNotes += 1

      stars = []
      maxStars = []

      maxPhrase = totalNotes/120

      for q in range(0,maxPhrase):
        for n in range(0,10):
          stars.append(totalNotes/maxPhrase*(q)+n+maxPhrase/4)
        maxStars.append(totalNotes/maxPhrase*(q)+10+maxPhrase/4)
      
      self.starNotesSet = True
      i = 0
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        for a in stars:
          if i == a:
            self.starNotes.append(time)
        for a in maxStars:
          if i == a:
            self.maxStars.append(time)
        i += 1

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    if self.leftyMode:
      glScale(-1, 1, 1)

    self.renderNeck(visibility, song, pos)
    if self.theme == 0 or self.theme == 1 or self.theme == 2:
      self.drawTrack(visibility, song, pos)
      self.drawBPM(visibility, song, pos)
      self.drawSideBars(visibility, song, pos)
    else:
      self.renderTracks(visibility)
      self.renderBars(visibility, song, pos)
    self.renderNotes(visibility, song, pos, killswitch)
    self.renderFrets(visibility, song, controls)
    self.renderFlames(visibility, song, pos, controls)
    
    if self.leftyMode:
      glScale(-1, 1, 1)

  def getMissedNotes(self, song, pos, catchup = False):
    if not song:
      return

    m1      = self.lateMargin
    m2      = self.lateMargin * 2

    #if catchup == True:
    #  m2 = 0
      
    track   = song.track[self.player]
    notes   = [(time, event) for time, event in track.getEvents(pos - m1, pos - m2) if isinstance(event, Note)]
    notes   = [(time, event) for time, event in notes if (time >= (pos - m2)) and (time <= (pos - m1))]
    notes   = [(time, event) for time, event in notes if not event.played and not event.hopod and not event.skipped]

    if catchup == True:
      for time, event in notes:
        event.skipped = True

    return sorted(notes, key=lambda x: x[1].number)        
    #return notes
    
  #def getRequiredNotes(self, song, pos):
  #  track = song.track[self.player]
  #  notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
  #  notes = [(time, event) for time, event in notes if not (event.played)]
  #  notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
  #  return notes

  def getRequiredNotes(self, song, pos):
    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not event.played]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
    return sorted(notes, key=lambda x: x[1].number)

  def getRequiredNotes2(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    if notes:
      t     = min([time for time, event in notes])
      notes = [(time, event) for time, event in notes if time - t < 1e-3]
      
    return sorted(notes, key=lambda x: x[1].number)
    
  def getRequiredNotes3(self, song, pos, hopo = False):

    track   = song.track[self.player]
    notes = [(time, event) for time, event in track.getEvents(pos - self.lateMargin, pos + self.earlyMargin) if isinstance(event, Note)]
    notes = [(time, event) for time, event in notes if not (event.hopod or event.played or event.skipped)]
    notes = [(time, event) for time, event in notes if (time >= (pos - self.lateMargin)) and (time <= (pos + self.earlyMargin))]
    #if notes:
    #  t     = min([time for time, event in notes])
    #  notes = [(time, event) for time, event in notes if time - t < 1e-3]

    return sorted(notes, key=lambda x: x[1].number)

  
  def hitNote(self, time, note):
     self.pickStartPos = max(self.pickStartPos, time)
     self.playedNotes = [(time, note)]
     note.played       = True
     return True  

  def areNotesTappable(self, notes):
    if not notes:
      return
    for time, note in notes:
      if note.tappable > 1:
        return True
    return False

  
  def startPick(self, song, pos, controls, hopo = False):
    if not song:
      return False

    if self.lastFretWasBassDrum:
      if controls.getState(self.keys[1]) or controls.getState(self.keys[2]) or controls.getState(self.keys[3]) or controls.getState(self.keys[4]) or controls.getState(self.keys[5]) or controls.getState(self.keys[6]) or controls.getState(self.keys[7]) or controls.getState(self.keys[8]):
        self.lastFretWasBassDrum = False
    elif controls.getState(self.keys[0]):
      self.lastFretWasBassDrum = True
    else:
      self.lastFretWasBassDrum = False
      
    #Faaa Drum sound
    if self.lastFretWasT1:
      if controls.getState(self.keys[0]) or controls.getState(self.keys[2]) or controls.getState(self.keys[3]) or controls.getState(self.keys[4]) or controls.getState(self.keys[6]) or controls.getState(self.keys[7]) or controls.getState(self.keys[8]):
        self.lastFretWasT1 = False
    elif controls.getState(self.keys[1]) or controls.getState(self.keys[5]):
      self.lastFretWasT1 = True
    else:
      self.lastFretWasT1 = False

    if self.lastFretWasT2:
      if controls.getState(self.keys[0]) or controls.getState(self.keys[1]) or controls.getState(self.keys[3]) or controls.getState(self.keys[4]) or controls.getState(self.keys[5]) or controls.getState(self.keys[7]) or controls.getState(self.keys[8]):
        self.lastFretWasT2 = False
    elif controls.getState(self.keys[2]) or controls.getState(self.keys[6]):
      self.lastFretWasT2 = True
    else:
      self.lastFretWasT2 = False

    if self.lastFretWasT3:
      if controls.getState(self.keys[0]) or controls.getState(self.keys[1]) or controls.getState(self.keys[2]) or controls.getState(self.keys[4]) or controls.getState(self.keys[5]) or controls.getState(self.keys[6]) or controls.getState(self.keys[8]):
        self.lastFretWasT3 = False
    elif controls.getState(self.keys[3]) or controls.getState(self.keys[7]):
      self.lastFretWasT3 = True
    else:
      self.lastFretWasT3 = False		  

    if self.lastFretWasC:
      if controls.getState(self.keys[0]) or controls.getState(self.keys[1]) or controls.getState(self.keys[2]) or controls.getState(self.keys[3]) or controls.getState(self.keys[5]) or controls.getState(self.keys[6]) or controls.getState(self.keys[7]):
        self.lastFretWasC = False
    elif controls.getState(self.keys[4]) or controls.getState(self.keys[8]):
      self.lastFretWasC = True
    else:
      self.lastFretWasC = False
  
    notes = self.getRequiredNotes(song, pos)

    # no notes?
    if not notes:
      return False
    self.playedNotes = []
    self.pickStartPos = pos
    
    #adding bass drum hit every bass fret:
    
    for time, note in notes:
      if ((note.number == 0 and controls.getState(self.keys[0]))
       or (note.number == 1 and (controls.getState(self.keys[1]) or controls.getState(self.keys[5])))
       or (note.number == 2 and (controls.getState(self.keys[2]) or controls.getState(self.keys[6]))) 
       or (note.number == 3 and (controls.getState(self.keys[3]) or controls.getState(self.keys[7]))) 
       or (note.number == 4 and (controls.getState(self.keys[4]) or controls.getState(self.keys[8])))):
        return self.hitNote(time, note)         

    return False        
    
  def startPick2(self, song, pos, controls, hopo = False):
    res = self.startPick(song, pos, controls, hopo)
    return res

  def startPick3(self, song, pos, controls, hopo = False):
    res = self.startPick(song, pos, controls, hopo)
    return res


  def endPick(self, pos):
    self.playedNotes = []
    for time, note in self.playedNotes:
      if time + note.length > pos + self.noteReleaseMargin:
        return False
    return True
    
  def getPickLength(self, pos):
    if not self.playedNotes:
      return 0.0
    
    # The pick length is limited by the played notes
    pickLength = pos - self.pickStartPos
    for time, note in self.playedNotes:
      pickLength = min(pickLength, note.length)
    return pickLength

  def run(self, ticks, pos, controls):
    self.time += ticks
    #myfingershurt: must not decrease SP if paused.
    if self.starPowerActive == True and self.paused == False:
      self.starPower -= ticks/200.0
      if self.starPower <= 0:
        self.starPower = 0
        self.starPowerActive = False
    

    activeFrets = [(note.number - 1) for time, note in self.playedNotes]

    
    for n in range(self.strings):
      if   n == 0 and (controls.getState(self.keys[1]) or controls.getState(self.keys[5])):
            self.fretWeight[n] = 0.5  
      elif n == 1 and (controls.getState(self.keys[2]) or controls.getState(self.keys[6])):
            self.fretWeight[n] = 0.5  
      elif n == 2 and (controls.getState(self.keys[3]) or controls.getState(self.keys[7])):
            self.fretWeight[n] = 0.5  
      elif n == 3 and (controls.getState(self.keys[4]) or controls.getState(self.keys[8])):
            self.fretWeight[n] = 0.5  
      elif controls.getState(self.keys[0]):
            self.fretWeight[n] = 0.5
      else:
        self.fretWeight[n] = max(self.fretWeight[n] - ticks / 64.0, 0.0)
      if n in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 32.0, 1.0)
      else:
        self.fretActivity[n] = max(self.fretActivity[n] - ticks / 64.0, 0.0)
      if -1 in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 24.0, 0.6)

    # glorandwarf: moved the update bpm code - was after the for statement below
    # update bpm
    if self.currentBpm != self.targetBpm:
      diff = self.targetBpm - self.currentBpm
      if (round((diff * .03), 4) != 0):
        self.currentBpm = round(self.currentBpm + (diff * .03), 4)
      else:
        self.currentBpm = self.targetBpm
      self.setBPM(self.currentBpm) # glorandwarf: was setDynamicBPM(self.currentBpm)

    for time, note in self.playedNotes:
      if pos > time + note.length:
        return False

    #self.setMargin()

    return True
