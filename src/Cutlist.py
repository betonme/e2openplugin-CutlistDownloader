#!/usr/bin/python
# encoding: utf-8
#
# CutList
# Copyright (C) 2012 betonme
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#

import os
import struct
from bisect import insort

from Components.config import *


# E2 Cutlist class
# Description
# http://git.opendreambox.org/?p=enigma2.git;a=blob;f=doc/FILEFORMAT
class Cutlist():

	# InfoBarCueSheetSupport types
	CUT_TYPE_IN = 0
	CUT_TYPE_OUT = 1
	CUT_TYPE_MARK = 2
	CUT_TYPE_LAST = 3
	# Additional custom EMC specific types
	# Has to be remove before starting a player
	CUT_TYPE_SAVEDLAST = 4
	
	# Toggle Types
	CUT_TOGGLE_START = 0
	CUT_TOGGLE_RESUME = 1
	CUT_TOGGLE_FINISHED = 2
	CUT_TOGGLE_START_FOR_PLAY = 3
	CUT_TOGGLE_FOR_PLAY = 4
	
	# Additional cutlist information
	#		cutlist[x][0] = pts   = long long
	#		cutlist[x][1] = what  = long
	
	# Constants
	ENABLE_RESUME_SUPPORT = True
	MOVIE_FINISHED = 0xFFFFFFFFFFFFFFFF
	
	INSORT_SCOPE = 45000  # 0.5 seconds * 90 * 1000

	def __init__(self, service=None):
		path = service and service.getPath()
		
		#name = None
		if path:
			if path.endswith(".iso"):
				#LATER No support yet
				#if not self.iso:
				#	self.iso = IsoSupport(path)
				#name = self.iso and self.iso.getIsoName()
				#if name and len(name):
				#	path = "/home/root/dvd-" + name
				pass
			elif os.path.isdir(path):
				path += "/dvd"
			path += ".cuts"
		
		self.cut_file = path
		print path
		self.cut_list = []
		
		self.__readCutFile()
		print self.cut_list
		
	def __ptsToSeconds(self, pts):
		# Cut files are using the presentation time stamp time format
		# pts has a resolution of 90kHz
		return pts / 90 / 1000

	def __secondsToPts(self, seconds):
		return int(seconds * 90 * 1000)


	##############################################################################
	## Get Set Functions
	def getCutList(self):
		return self.cut_list

	def getCutListLast(self):
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					return pts
		return 0

	def getPreviousMark(self, current):
		current = current - 5*90*1000
		if self.cut_list:
			for (pts, what) in reversed(self.cut_list):
				if pts < current:
					return pts
			else:
				return 0 

	def getNextMark(self, current):
		current = current + 5*90*1000
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if current < pts:
					return pts
			else:
				return -1 # End

	def setCutList(self, cut_list):
		self.cut_list = cut_list

	def save(self):
		print "SAVE Cutlist", self.cut_list
		self.__writeCutFile()


	##############################################################################
	## Modify Functions
	## Use remove and insort to guarantee the cut list is sorted

	def removeWhats(self, whats):
		# All Marks will be removed
		# All others items will stay
		print "removeWhats", whats
		print self.cut_list
		if self.cut_list:
			for cp in self.cut_list[:]:
				if cp[1] in whats:
					self.cut_list.remove(cp)
		self.__writeCutFile()
		print self.cut_list

	def toggleMarker(self):
		tmplist = self.cut_list
		self.cut_list = []
		nextInOut = Cutlist.CUT_TYPE_IN
		for pts, what in tmplist:
			if what == Cutlist.CUT_TYPE_IN or what == Cutlist.CUT_TYPE_OUT:
				what = Cutlist.CUT_TYPE_MARK
			elif what == Cutlist.CUT_TYPE_MARK:
				what = nextInOut
				if nextInOut == Cutlist.CUT_TYPE_IN:
					nextInOut = Cutlist.CUT_TYPE_OUT
				else:
					nextInOut = Cutlist.CUT_TYPE_IN
			self.cut_list.append( (pts,what) )

	def updateCutList(self, cutlist):
		if cutlist:
			for pts, what in cutlist:
				self.__insort(pts, what)
			self.__writeCutFile()

	def __insort(self, pts, what):
		if self.cut_list:
			for (clpts, clwhat) in self.cut_list[:]:
				if clwhat == what:
					if clpts-self.INSORT_SCOPE < pts < clpts+self.INSORT_SCOPE:
						# Found a conflicting entry, replace it to avoid doubles and short jumps
						self.cut_list.remove( (clpts, clwhat) )
			insort(self.cut_list, (pts, what))
		else:
			insort(self.cut_list, (pts, what))


	##############################################################################
	## File IO Functions
	def __readCutFile(self, update=False):
		data = ""
		path = self.cut_file
		if path and os.path.exists(path):
			if not update:
				# No update clear all
				self.cut_list = []
			
			# Read data from file
			# OE1.6 with Pyton 2.6
			#with open(path, 'rb') as f: data = f.read()	
			f = None
			try:
				f = open(path, 'rb')
				data = f.read()
			except Exception, e:
				print "[CUTS] Exception in __readCutFile: " + str(e)
			finally:
				if f is not None:
					f.close()
					
			# Parse and unpack data
			if data:
				pos = 0
				while pos+12 <= len(data):
					# Unpack
					(pts, what) = struct.unpack('>QI', data[pos:pos+12])
					self.__insort(long(pts), what)
					# Next cutlist entry
					pos += 12
		else:
			# No path or no file clear all
			self.cut_list = []

	def __writeCutFile(self):
		data = ""
		path = self.cut_file
		if path:
			
			# Generate and pack data
			if self.cut_list:
				for (pts, what) in self.cut_list:
					data += struct.pack('>QI', pts, what)
			
			# Write data to file
			# OE1.6 with Pyton 2.6
			#with open(path, 'wb') as f: f.write(data)
			f = None
			try:
				f = open(path, 'wb')
				if data:
					f.write(data)
			except Exception, e:
				print "[CUTS] Exception in __writeCutFile: " + str(e)
			finally:
				if f is not None:
					f.close()
