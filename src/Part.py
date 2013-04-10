#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
# Frets on Fire                                                     #
# Copyright (C) 2006-2009                                           #
#               Sami Kyöstilä                                       #
#               Alex Samonte                                        #
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

from Language import _

class Part:
  def __init__(self, id, text):
    self.id   = id
    self.text = text
    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

NO_PART                 = -2
PARTY_PART              = -1  
GUITAR_PART             = 0
RHYTHM_PART             = 1
BASS_PART               = 2
LEAD_PART               = 3
DRUM_PART               = 4
VOCAL_PART              = 5
  
parts = {
  NO_PART: Part(NO_PART, _("No Player 2")),
  PARTY_PART: Part(PARTY_PART, _("Party Mode")),
  GUITAR_PART: Part(GUITAR_PART, _("Guitar")),
  RHYTHM_PART: Part(RHYTHM_PART, _("Rhythm Guitar")),
  BASS_PART:   Part(BASS_PART,   _("Bass Guitar")),
  LEAD_PART:   Part(LEAD_PART,   _("Lead Guitar")),
  DRUM_PART:   Part(DRUM_PART,   _("Drums")),
  VOCAL_PART:  Part(VOCAL_PART,  _("Vocals")),
}

