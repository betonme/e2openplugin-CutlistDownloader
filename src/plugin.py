#######################################################################
#
#    CutlistDownloader for Enigma-2
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

# Config
from Components.config import *

# Plugin
from Plugins.Plugin import PluginDescriptor

from enigma import eServiceReference

# Plugin internal
from CutListAT import BestCutListAT


#######################################################
# Constants
NAME = _("CutlistDownloader")
VERSION = "0.4"
SUPPORT = "http://bit.ly/cutlistdownloaderihad"
DONATE = "http://bit.ly/cutlistdownloaderpaypal"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  {downloads:d} successful downloads\n") \
				+ _("  Support: ") + SUPPORT + "\n" \
				+ _("  Feel free to donate\n") \
				+ _("  PayPal: ") + DONATE

# Config options
config.plugins.cutlistdownloader = ConfigSubsection()

# Internal
config.plugins.cutlistdownloader.download_counter = ConfigNumber(default=0)
config.plugins.cutlistdownloader.offset           = ConfigNumber(default=5*60)  # In seconds


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	#TODO setup
	
	#TODO icon
	descriptors.append( PluginDescriptor(
																			name=_("Open" + " " + NAME),
																			description=_("Open" + " " + NAME),
																			where=PluginDescriptor.WHERE_MOVIELIST,
																			fnc=openCutlistDownloader,
																			needsRestart=False) )

#	descriptors.append( PluginDescriptor(
#																			name = _("Download Cutlist(s)"),
#																			description = _("Download Cutlist(s)"),
#																			where = PluginDescriptor.WHERE_MOVIELIST,
#																			fnc = downloadCutlists,
#																			needsRestart = False) )

	return descriptors


#######################################################
# Download from Cutlist.at
def openCutlistDownloader(session, service, services=None, *args, **kwargs):
	print "CutlistDownloader Open"
	try:
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		
		### For testing only
		import CutlistDownloader
		reload(CutlistDownloader)
		###
		session.open( CutlistDownloader.CutlistDownloader, services )
		
	except Exception, e:
		print "CutlistDownloader downloadCutlist exception: " + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

#UNTESTED
#
#downloader = []
#def downloadCutlists(session, service, services=None, *args, **kwargs):
#	print "CutlistDownloader download and save"
#	try:
#		if services:
#			if not isinstance(services, list):
#				services = [services]	
#		else:
#			services = [service]
#		
#		def save(service, cutlist):
#			if cutlist:
#				from Cutlist import Cutlist
#				cue = Cutlist(service)
#				cue.setCutList(cutlist)
#				cue.save
#		
#		from Tools.BoundFunction import boundFunction
#		downloader.append( BestCutListAT(service, boundFunction(save, service)) )
#		
#	except Exception, e:
#		print "CutlistDownloader downloadCutlist exception: " + str(e)
#		exc_type, exc_value, exc_traceback = sys.exc_info()
#		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


bestCutList = None

def bestCutlist(service, callback, *args, **kwargs):
	print "CutlistDownloader Best"
	global bestCutList
	bestCutList = BestCutListAT(service, callback)

