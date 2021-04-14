#######################################################################
#
#    Console for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import os
import sys
import traceback

# for localized messages
from . import _

from Components.config import config

from Components.ActionMap import HelpableActionMap
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Plugin internal
from Cutlist import Cutlist
from CutlistService import CutlistService

CUT_JUMP = 1


#######################################################
# Screen
class CutlistPlayer(MoviePlayer, Cutlist):
	def __init__(self, session, service, cutlistat):

		self.service = service
		#self.backup = []
		self.cutlistat = cutlistat
		self.cut_list = []

		Cutlist.__init__(self)
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

		self["custom_actions"] = HelpableActionMap(self, "CutlistPlayerActions",
		{
			"left": (self.left, _("Move Cutlist to the left")),
			"right": (self.right, _("Move Cutlist to the right")),
			"ok": (self.switch, _("Switch between Marker and Cut-In/Out")),
			"exit": (self.cancel, _("Exit without saving")),
			#"up":					(self["list"].pageUp,			_("Page up")),
			#"down":				(self["list"].pageDown,		_("Page up")),
			#"red":					(self.ok,									_("Download Single Cutlist")),
			"green": (self.save, _("Save new cutlist")),
			#"yellow":			(self.bestdownload,				_("Page up")),
			#"blue":				(self.remove,							_("Remove Marker")),
		}, -3)

		self["Service"] = CutlistService(session.nav, self)

	def switch(self):
		self.toggleMarker()
		self.uploadCuesheet()

	# Cutlist relevant functions
	def downloadCuesheet(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			cue = service.cueSheet()
			if cue is not None:
				# E2 Bug: setCutListEnable won't work
				cue.setCutListEnable(0)
				#cue.setCutListEnable(2)
				#cue.setCutListEnable(3)
				#self.backup = cue.getCutList()
		# Set our cutlist
		self.cut_list = self.cutlistat
		self.uploadCuesheet()
		if self.cut_list:
			self.pauseService()
			self.doSeek(self.cut_list[0][0])

	def right(self):
		print "RIGHT"
		config.plugins.cutlistdownloader.offset.value = config.plugins.cutlistdownloader.offset.value + CUT_JUMP
		print self.cut_list
		cl = []
		for pts, what in self.cut_list:
			cl.append((pts + CUT_JUMP * 90 * 1000, what))
		self.cut_list = cl
		print cl
		self.uploadCuesheet()
		#pts = self.cueGetCurrentPosition()
		#self.doSeek(pts + CUT_JUMP*90*1000)
		self.doSeekRelative(+CUT_JUMP)

	def left(self):
		print "LEFT"
		config.plugins.cutlistdownloader.offset.value = config.plugins.cutlistdownloader.offset.value - CUT_JUMP
		print self.cut_list
		cl = []
		for pts, what in self.cut_list:
			cl.append((pts - CUT_JUMP * 90 * 1000, what))
		self.cut_list = cl
		print cl
		self.uploadCuesheet()
		pts = self.cueGetCurrentPosition()
		self.doSeek(pts - CUT_JUMP * 90 * 1000)

	def cancel(self):
		self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))

	def cancelConfirm(self, result):
		if not result:
			# Save new cutlist
			self.close(self.cut_list)
		else:
			# Restore backup
			#self.cut_list = self.backup
			#self.doSeek(self.getCutListLast())
			#self.uploadCuesheet()
			self.close()

	def save(self):
		self.close(self.cut_list)

	# Overwrite InfoBar
	def serviceStarted(self):
		if self.execing:
			self.doShow()

	def jumpPreviousMark(self):
		self.doSeek(self.getPreviousMark(self.cueGetCurrentPosition()))

	def jumpNextMark(self):
		current = self.cueGetCurrentPosition()
		print current
		next = self.getNextMark(current)
		print next
		#self.doSeek( next )
		#self.doSeek( self.getNextMark( self.cueGetCurrentPosition() ) )
		self.doSeekRelative(next - current)

	def showMovies(self):
		pass

	def toggleShow(self):
		pass

	def doShow(self):
		self.show()

	def hide(self):
		pass

	def handleLeave(self, how):
		self.is_closing = True
		self.close()
