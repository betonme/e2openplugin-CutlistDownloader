#!/usr/bin/python
#
# CutlistDownloader.py
# Enhanced Movie Center
# Copyright (C) 2012 betonme @ IHAD
# 
# Based on:
#  cutLin.py
#  Version 0.8.1
#  http://www.otrforum.com/showthread.php?50954-cutLin-py-Linux-Schneideskript-f%FCr-cutlist-at-und-de
#  Thanks to bowmore and freddyk for testing.
#  Copyright (C) 2008 Dan Kuoni
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or (at
# your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re

from twisted.web.client import getPage

from time import localtime, strftime


import xml.dom.minidom
#TODO use cElementTree 
#OR
#JSON http://cutlist.at/info/
#import json
#cutlists = json.load("...")
#id = cutlists[0]['id'] # id der ersten Cutlist  


# Enigma2 relevant imports
from Components.config import config
from enigma import eServiceCenter, eServiceReference, iServiceInformation
from ServiceReference import ServiceReference


#############################################################################
# Server URLs
getXMLUrl = "http://www.cutlist.at/getxml.php?name="

getFileUrl = "http://www.cutlist.at/getfile.php?id="


#############################################################################
# Cutlist Class
class cutlist:
	def __init__(self,node): #,serverID):
		#self.serverID=serverID
		# Parse XML Node "cutlist"
		# 1. id and name
		try:
			tmp=node.getElementsByTagName("id")
			self.id=tmp[0].firstChild.data
			tmp=node.getElementsByTagName("name")
			self.name=tmp[0].firstChild.data
		except:
			# If this happens, the server is broken
			self.id=-1
			self.name=""
		# 2. user-rating 
		try:
			tmp=node.getElementsByTagName("rating")
			self.rating=tmp[0].firstChild.data
		except:
			self.rating="0" 
		# 3. Name of the author
		try:
			tmp=node.getElementsByTagName("author")
			self.author=tmp[0].firstChild.data
		except:
			self.author="unknown"
		# 4. ErrorCodes
		try:
			tmp=node.getElementsByTagName("errors")
			self.errorCodes=tmp[0].firstChild.data
			self.errors=""
			if self.errorCodes[0]==1: 
				self.errors=self.errors + "Missing Beginning! " 
			if self.errorCodes[1]==1: 
				self.errors=self.errors + "Missing Ending! "
			if self.errorCodes[2]==1: 
				self.errors=self.errors + "Missing Audio! "
			if self.errorCodes[3]==1: 
				self.errors=self.errors + "Missing Video! "
			if self.errorCodes[4]==1: 
				self.errors=self.errors + "Unknown error! "
			if self.errorCodes[5]==1: 
				self.errors=self.errors + "EPG error! "
			# If none of the above is true, then there are no errors.
			if self.errors=="": 
				self.errors="No errors."
			else:
				self.errors= self.errors
		except:
			self.errorCodes="000000"
			self.errors="No information available."

		# 5. Ratingcount of user ratings 
		try:
			tmp=node.getElementsByTagName("ratingcount")
			self.ratingcount=tmp[0].firstChild.data
		except:
			self.ratingcount="0"
		# 5. Rating by author
		try:
			tmp=node.getElementsByTagName("ratingbyauthor")
			self.ratingByAuthor=tmp[0].firstChild.data
		except:
			self.ratingByAuthor="-"
		# 6. Number of cuts
		try:
			tmp=node.getElementsByTagName("cuts")
			self.cuts=int(tmp[0].firstChild.data)
		except:
			self.cuts=0
		# 7. With frames or with seconds ? 
		try:
			tmp=node.getElementsByTagName("withframes")
			self.withframes=int(tmp[0].firstChild.data)
		except:
			self.withframes=0
		try:
			tmp=node.getElementsByTagName("withtime")
			self.withtime=int(tmp[0].firstChild.data)
		except:
			self.withtime=0
		# 8. Duration
		try:
			tmp=node.getElementsByTagName("duration")
			self.duration=tmp[0].firstChild.data
		except:
			self.duration=0
		# 9. Actual content
		try:
			tmp=node.getElementsByTagName("actualcontent")
			self.actualcontent=tmp[0].firstChild.data
		except:
			self.actualcontent="-"
		# 10. Filename
		try:
			tmp=node.getElementsByTagName("filename")
			self.filename=tmp[0].firstChild.data
		except:
			self.filename=""
		# 11. Usercomment
		try:
			tmp=node.getElementsByTagName("usercomment")
			self.usercomment=unicode(tmp[0].firstChild.data)
		except:
			self.usercomment="-"
		# Downloadcount
		try:
			tmp=node.getElementsByTagName("downloadcount")
			self.downloadcount=unicode(tmp[0].firstChild.data)
		except:
			self.downloadcount="-"


class CutlistAT():
	def __init__(self, service):
		self.service = service
		self.callback = None
		self.cancelled = False
		
		self.regexp_seriesepisodes = re.compile('(.*)[ _][Ss]{,1}\d{1,2}[EeXx]\d{1,2}.*')  #Only for S01E01 01x01
		self.searchs = []
		
		self.list = []
		#self.cutlist = []

	def getService(self):
		return self.service

	#def getCutList(self):
	#	return self.cutlist

	def getListLength(self):
		return len(self.list)

	def getList(self):
		return self.list

	# searchList
	def searchList(self, callback):
		self.callback = callback
		
		service = self.service
		try:
			if isinstance(service, eServiceReference):
				ref = service
			elif isinstance(service, ServiceReference):
				ref = service.ref
			else:
				return
			
			name = ref.getName()
			info = eServiceCenter.getInstance().info(ref)
			
			begin = info and info.getInfo(ref, iServiceInformation.sTimeCreate) or -1
			if begin != -1:
				end = begin + (info.getLength(ref) or 0)
			else:
				end = os.path.getmtime(ref.getPath())
				begin = end - (info.getLength(ref) or 0)
				#MAYBE we could also try to parse the filename and extract the date
			
			#channel = ServiceReference(ref).getServiceName() #info and info.getName(service)
			
			begins = [localtime(begin), localtime(begin - 10*60), localtime(begin + 10*60)]
			
			# Is there a better way to handle the title encoding 
			try:
				name.decode('utf-8')
			except UnicodeDecodeError:
				try:
					name = name.decode("cp1252").encode("utf-8")
				except UnicodeDecodeError:
					name = name.decode("iso-8859-1").encode("utf-8")
			
			# Modify title to get search string
			name = name.lower()
			
			name = name.replace('\xc3\xa4', 'ae')
			name = name.replace('\xc3\xb6', 'oe')
			name = name.replace('\xc3\xbc', 'ue')
			name = name.replace('\xc3\x9f', 'ss')
			
			name = name.replace('-', '_')
			name = name.replace(',', '_')
			name = name.replace('\'', '_')
			name = name.replace(' ', '_')
			
			while '__' in name:
				name = name.replace('__', '_')
			
			name = name.rstrip('_')
			
			# Remove Series Episode naming
			#MAYBE read SeriesPlugin config and parse it ??
			m = self.regexp_seriesepisodes.match(name)
			if m:
				print m.group(0)       # The entire match
				print m.group(1)       # The first parenthesized subgroup.
				name = m.group(1)
			
			for begin in begins:
				searchfor = ("%s_%s") % (name, strftime('%y.%m.%d_%H-%M', begin))
				#searchfor = ("%s_%s_%s") % (name.replace(' ', '_'), strftime('%y.%m.%d_%H-%M', localtime(begin)), channel.replace(' ', '_'))
				self.searchs.append( searchfor )
			
			self.searchs.reverse()
			self.downloadList()
		except Exception, e:
			print "[CUTS] searchList exception: " + str(e)

	def downloadList(self, *args):
		if args:
			print "EMC CutlistAT downloadList errorback", args
		if self.searchs:
			searchfor = self.searchs.pop()
			# Remove the last character, ignore the minutes
			downloadUrl = str(getXMLUrl+searchfor[:-1])
			print downloadUrl
			# Download xml file
			getPage(downloadUrl, timeout = 10).addCallback(self.parseList).addErrback(self.downloadList)
		else:
			if not self.cancelled and callable(self.callback):
				self.callback(self.list)
				self.callback = None
	
	def parseList(self, data):
		try:
			# Because getxml.php returns an empty page if no cutlists
			# are available, it is necessary to check filesize
			if data:
				# Parse xml file
				doc = xml.dom.minidom.parseString(data)
				
				# Create a list of cutlists
				for node in doc.getElementsByTagName("cutlist"):
					self.list.append(cutlist(node))
				
				# Get number of available cutlists
				print "Found %s cutlist(s)" % ( len(self.list))
				
				##self.list.reverse()
				#self.downloadBestCutlist()
				self.downloadList()
			
			# No cutlists available
			else:
				print "Found 0 cutlists"
				self.downloadList()
		except Exception, e:
			print "[CUTS] parseList exception: " + str(e)
	
	def downloadBestCutlist(self, *args):
		if args:
			print "EMC CutlistAT downloadCutlist errorback", args
		if id:
			cl = self.list.pop()
			id = cl.id
			if id > 0:
				downloadUrl = str(getFileUrl+id);
				print downloadUrl
				# Download xml file
				getPage(downloadUrl, timeout = 10).addCallback(self.parseCutlist).addErrback(self.downloadCutlist)
			else:
				self.downloadCutlist()
		else:
			self.downloadList()
	
	def downloadCutlist(self, id, callback):
		self.callback = callback
		if id > 0:
			downloadUrl = str(getFileUrl+id);
			print downloadUrl
			# Download xml file
			getPage(downloadUrl, timeout = 10).addCallback(self.parseCutlist).addErrback(self.errback)
		else:
			if not self.cancelled and callable(self.callback):
				self.callback([])
				self.callback = None
	
	def errback(self, *args):
		if args:
			print "EMC CutlistAT downloadCutlist errorback", args
		else:
			if not self.cancelled and callable(self.callback):
				self.callback([])
				self.callback = None
	
	def parseCutlist(self, data):
		try:
			if data:
				print "Cutlist downloaded."
				cutlist = self.convertToPTS(data)
				if cutlist:
					#self.cutlist = cutlist
					
					
					from Components.config import config
					config.plugins.cutlistdownloader.download_counter.value += 1
					if (config.plugins.cutlistdownloader.download_counter.value == 10) \
						or (config.plugins.cutlistdownloader.download_counter.value == 100) \
						or (config.plugins.cutlistdownloader.download_counter.value % 1000 == 0):
						from plugin import ABOUT
						from Screens.MessageBox import MessageBox
						from Tools.Notifications import AddPopup
						about = ABOUT.format( **{'downloads': config.plugins.cutlistdownloader.download_counter.value} )
						AddPopup(
							about,
							MessageBox.TYPE_INFO,
							0,
							'CD_PopUp_ID_About'
						)
					
					
					if not self.cancelled and callable(self.callback):
						
						self.callback(cutlist)
						self.callback = None
				else:
					self.downloadCutlist()
			else:
				self.downloadCutlist()
		except Exception, e:
			print "[CUTS] parseCutlist exception: " + str(e)

	###################################################################
	# Internal

	# readCuts
	def readCuts(self, data):
		segments=list()
		
		if data.find("StartFrame=") > -1:
			withframes=1
		else:
			withframes=0
		if withframes==1:
			startPattern="StartFrame="
			durPattern="DurationFrames="
		else:
			startPattern="Start="
			durPattern="Duration="
		# Read file line by line and look for cutting information
		
		def readline(data):
			for line in data.splitlines():
				yield line
		
		rd = readline(data)
		#try: # Maybe?
		for line in rd:
			if line and line.startswith("[Cut"):
				startFound=False
				durFound=False
				while not startFound or not durFound:
					line=rd.next()
					if line.startswith(startPattern):
						start=float(line.partition("=")[2])
						startFound=True
					if line.startswith(durPattern):
						duration=float(line.partition("=")[2])
						durFound=True
					if line.startswith("[Cut"):
						print "Cutlist format error!!!"
						return
				if withframes==1:
					segments.append( ( start/25, duration/25 ) )
				else:
					segments.append( ( start, duration ) )
		#except StopIteration: pass
		# Return cut positions and durations in seconds as float
		return segments
	
	# Convert and Sync
	def convertToPTS(self, data):
		cutlist = []
		# Read cut information from cutlist file
		segments = self.readCuts(data)   # Returns seconds
		
		if segments:
			e2record_margin  = config.recording.margin_before.value * 60 * 90*1000   # Convert minutes in pts
			cutlistat_offset = config.plugins.cutlistdownloader.offset.value * 90*1000
			
			# Write cut segments
			for segment in segments:
				start = segment[0]
				end = start + segment[1]
				
				# Convert seconds into pts
				start = int( start * 90 * 1000 )
				end   = int( end * 90 * 1000 )
				
				# Sync
				start += cutlistat_offset - e2record_margin
				end   += cutlistat_offset - e2record_margin
				
				from Cutlist import Cutlist
				
				# For player usage
				cutlist.append( (long(start), Cutlist.CUT_TYPE_MARK) )
				cutlist.append( (long(end),   Cutlist.CUT_TYPE_MARK) )
				
				# Only for cutting software
				#cutlist.append( (long(start), Cutlist.CUT_TYPE_IN) )
				#cutlist.append( (long(end),   Cutlist.CUT_TYPE_OUT) )
			
			print cutlist
			return cutlist

	def cancel(self):
		self.cancelled = True
