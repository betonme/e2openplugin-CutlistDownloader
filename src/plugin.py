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

import os, sys, traceback

# for localized messages
from . import _

# Config
from Components.config import *

# Plugin
from Plugins.Plugin import PluginDescriptor

from enigma import eServiceReference

from Tools.BoundFunction import boundFunction
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox


# Plugin internal
from Cutlist import Cutlist
from CutlistDownloader import CutlistAT


#######################################################
# Constants
NAME = _("CutlistDownloader")
VERSION = "0.2"
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
config.plugins.cutlistdownloader.download_counter            = ConfigNumber(default = 0)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	#TODO setup
	
	#TODO icon
	descriptors.append( PluginDescriptor(
																			name = _("Download Cutlist(s)"),
																			description = _("Download Cutlist(s)"),
																			where = PluginDescriptor.WHERE_MOVIELIST,
																			fnc = downloadCutlist,
																			needsRestart = False) )

	#TODO icon
	descriptors.append( PluginDescriptor(
																			name = _("Remove Cutlist(s) marker"),
																			description = _("Remove Cutlist(s) marker"),
																			where = PluginDescriptor.WHERE_MOVIELIST,
																			fnc = removeMarker,
																			needsRestart = False) )

	return descriptors


#######################################################
# Download from Cutlist.at
def downloadCutlist(session, service, services=None, *args, **kwargs):
	print "CutlistDownloader downloadCutlist"
	try:
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		
		### For testing only
		import CutlistDownloaderScreen
		reload(CutlistDownloaderScreen)
		###
		session.open(CutlistDownloaderScreen.CutlistDownloaderScreen, boundFunction(downloadCutlistWorker, services), _("Download Cutlist(s)") )
		
	except Exception, e:
		print "CutlistDownloader downloadCutlist exception: " + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

def downloadCutlistWorker(services, output):
	downloader = []
	try:
		output("Download Cutlists for:")
	except: pass
	def cutlistDownloaded(service, cutlist):
		result = _("Failed")
		if cutlist:
			result = _("Success")
			# Load CutList
			cuts = Cutlist( service )
			if cuts:
				# Update and write CutList
				cuts.updateCutList(cutlist)
				
				config.plugins.cutlistdownloader.download_counter.value += 1
				if (config.plugins.cutlistdownloader.download_counter.value == 10) \
					or (config.plugins.cutlistdownloader.download_counter.value == 100) \
					or (config.plugins.cutlistdownloader.download_counter.value % 1000 == 0):
					from plugin import ABOUT
					about = ABOUT.format( **{'downloads': config.plugins.cutlistdownloader.download_counter.value} )
					AddPopup(
						about,
						MessageBox.TYPE_INFO,
						0,
						'CD_PopUp_ID_About'
					)
		
		try:
			output( os.path.basename( service.getPath() ) + " " + str(result) )
		except: pass
		services.remove( service )
		if not services:
			try:
				output( _("Finished") )
			except: pass
			config.plugins.cutlistdownloader.download_counter.save()
	
	for service in services:
		if service and service.getName():
			if service.type == eServiceReference.idDVB:
				# Download CutList
				downloader.append( CutlistAT( boundFunction(cutlistDownloaded, service), service) )
			else:
				print "CutlistDownloader downloadCutlist: No dvb transportstream movie"


#######################################################
# Remove marker
def removeMarker(session, service, services=None, *args, **kwargs):
	print "CutlistDownloader removeMarker"
	try:
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		
		### For testing only
		import CutlistDownloaderScreen
		reload(CutlistDownloaderScreen)
		###
		session.open(CutlistDownloaderScreen.CutlistDownloaderScreen, boundFunction(removeMarkerWorker, services), _("Remove Marker") )
		
	except Exception, e:
		print "CutlistDownloader removeMarker exception: " + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

def removeMarkerWorker(services, output):
	try:
		output("Removing marker for:")
	except: pass
	
	for service in services:
		# Load CutList
		cuts = Cutlist( service )
		# Remove and write CutList
		cuts.removeMarksCutList()
		
		try:
			output( os.path.basename( service.getPath() ) )
		except: pass
	try:
		output( _("Finished") )
	except: pass

