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

from thread import start_new_thread

# for localized messages
from . import _

from Components.config import config

from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.HelpMenu import HelpableScreen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

# Plugin internal
from ServiceList import ServiceList
from Cutlist import Cutlist
from CutListAT import CutListAT, CutFileAT, SearchStrings
from CutlistPlayer import CutlistPlayer


#######################################################
# Screen
class CutlistDownloader(Screen, HelpableScreen):
	skinfile = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/CutlistDownloader/skin.xml")
	skin = open(skinfile).read()

	def __init__(self, session, services):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# Dict[service] = List of cutlist ids
		self.cutlists = dict((k, None) for k in services)

		# Dict[id] = Cutfile
		self.cutfiles = {}

		self.customAT = None

		# Buttons
		self["key_red"] = StaticText(_("Show")) #"_("Download") )
		self["key_green"] = StaticText(_("Custom"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Remove"))

		self["custom_actions"] = HelpableActionMap(self, "CutlistDownloaderActions",
		{
			"ok": (self.select, _("Show available Cutlists")),
			"exit": (self.exit, _("Exit")),
			"red": (self.select, _("Show available Cutlists")),
			"green": (self.custom, _("Customize search string")),
			#"yellow":			(self.bestdownload,			 _("Page up")),
			"blue": (self.remove, _("Remove Marker")),
		}, -1)

		self["list"] = ServiceList([(s, '-') for s in self.cutlists.iterkeys()])

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		from plugin import NAME, VERSION
		self.setTitle(NAME + " " + VERSION)
		for service in self.cutlists.iterkeys():
			self.cutlists[service] = CutListAT(service, boundFunction(self.updateService, service))

	def updateService(self, service, list):
		if service is not None:
			self["list"].updateService(service, len(list))

	def exit(self):
		#for downloader in self.downloader:
		#	downloader.cancel()
		self.close()

	# Overwrite Screen close function
	def close(self):
		# Save Download Counter
		config.plugins.cutlistdownloader.download_counter.save()
		config.plugins.cutlistdownloader.offset.save()
		config.plugins.cutlistdownloader.save()
		# Call baseclass function
		Screen.close(self)

	#######################################################
	# Select Worker
	def select(self):
		service = self["list"].getCurrent()
		if service:
			cutlistat = self.cutlists[service]
			if cutlistat:
				self.showSelection(service, [("%-35s  R%.1f (%2d) #%3d" % (str(c.name[:35]), float(c.rating), int(c.ratingcount), int(c.downloadcount)), str(c.id)) for c in cutlistat.getList()])

	def showSelection(self, service, list):
		dlg = self.session.openWithCallback(
			boundFunction(self.selected, service),
			ChoiceBox,
			_("Name  Rating (RatingCount)  #Downloads"),
			list,
		)
		dlg.setTitle("Download Cutlist")

	def selected(self, service, ret):
		if service and ret is not None:
			id = ret[1]
			if id in self.cutfiles:
				print "Cutlist from Cache"
				self.startPlayer(service, self.cutfiles[id].getCutList())
			else:
				print "Cutlist from Cutlist.at"
				self.cutfiles[id] = CutFileAT(id, boundFunction(self.startPlayer, service))

	def startPlayer(self, service, cutlist):
		if service and cutlist:
			cue = Cutlist(service)
			print "Backup", cue.getCutList()
			self.session.openWithCallback(boundFunction(self.playerClosed, service, cue), CutlistPlayer, service, cutlist)

	def playerClosed(self, service, cue, cutlist=None):
		if cutlist:
			print "PLAYERCLOSED with SAVING"
			# Save again to remove Last
			cue.setCutList(cutlist)
		else:
			print "PLAYERCLOSED without SAVING"
		#	# Save cutlist backup to disk
			cue.save()

	#######################################################
	# Customize Worker
	def custom(self):
		service = self["list"].getCurrent()
		searchs = SearchStrings(service).getSearchList()
		if searchs:
			self.session.openWithCallback(
				boundFunction(self.customized, service),
				InputBox,
				text=searchs[0],
				title=_("Enter custom search string:"),
				windowTitle=_("Custom search")
			)

	def customized(self, service, search):
		print search
		if search:
			self.customAT = CutListAT(service, boundFunction(self.customResults, service), search)

	def customResults(self, service, list):
		self.showSelection(service, [("%-35s  R%.1f (%2d) #%3d" % (str(c.name[:35]), float(c.rating), int(c.ratingcount), int(c.downloadcount)), str(c.id)) for c in list])

	#######################################################
	# Remove Worker
	def remove(self):
		service = self["list"].getCurrent() # self["list"].getServices()
		if service:
			dlg = self.session.openWithCallback(
				boundFunction(self.removeCallback, [service]),
				ChoiceBox,
				_("What do You want to remove?"),
				[
					(_("Marker"), [Cutlist.CUT_TYPE_MARK]),
					(_("Cut In/Out"), [Cutlist.CUT_TYPE_IN, Cutlist.CUT_TYPE_OUT]),
					(_("Last"), [Cutlist.CUT_TYPE_LAST]),
					(_("All"), [Cutlist.CUT_TYPE_MARK, Cutlist.CUT_TYPE_IN, Cutlist.CUT_TYPE_OUT, Cutlist.CUT_TYPE_LAST]),
				]
			)
			dlg.setTitle("Clean Cutlist")

	def removeCallback(self, services, ret):
		if ret is not None:
			#start_new_thread( self.removeWhats, (services, ret[1]) )
			self.removeWhats(services, ret[1])

	def removeWhats(self, services, whats):
		print "Removing marker..."

		for service in services:
			# Load CutList
			cutlist = Cutlist(service)
			# Remove and write CutList
			cutlist.removeWhats(whats)

			print os.path.basename(service.getPath())
		print "Remove marker Finished"
