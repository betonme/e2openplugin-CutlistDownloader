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

from Components.config import *

from Components.ActionMap import ActionMap
from Components.ActionMap import HelpableActionMap
from Components.ScrollLabel import ScrollLabel
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
#from Screens.ChoiceBox import ChoiceBox
#from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen

# Plugin internal


#######################################################
# Console
class CutlistDownloaderScreen(Screen):
	def __init__(self, session, worker, title):
		Screen.__init__(self, session)
		self.skinName = ["TestBox", "Console"]

		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"ok": self.cancel,
			"back": self.cancel,
			"up": self["text"].pageUp,
			"down": self["text"].pageDown
		}, -1)

		self.title = title
		self.worker = worker

		self.onLayoutFinish.append(self.layoutFinished)
		self.onShow.append(self.showScreen)

	def layoutFinished(self):
		self.setTitle(self.title)

	def showScreen(self):
		self.worker(self.appendText)

	def setText(self, text):
		self["text"].setText(text)

	def appendText(self, text):
		text = self["text"].getText() + '\n' + text
		self.setText(text)

	def cancel(self):
		self.close()

	# Overwrite Screen close function
	def close(self):
		# Call baseclass function
		Screen.close(self)
