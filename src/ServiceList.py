# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Components)
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from Screens.MessageBox import MessageBox
from skin import parseColor, parseFont
from Tools.BoundFunction import boundFunction
from Tools.Notifications import AddPopup

# Plugin internal
from Cutlist import Cutlist
from CutlistAT import CutlistAT


class ServiceList(MenuList):
	"""Defines a simple Component to show Service name"""

	def __init__(self, list):
		MenuList.__init__(self, list, enableWrapAround=False, content=eListboxPythonMultiContent)
		
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(25)

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	#
	# | <Name of Service> | <Number of Cutlists> |
	#
	def buildListboxEntry(self, service, listlength):
		size = self.l.getItemSize()
		height = size.height()
		
		res = [ service ]
		
		start = 10
		end   = int(size.width() / 8 * 7)
		if service is not None:
			name = service.getName()
		else:
			name = ''
		res.append( MultiContentEntryText(pos=(start, 0), size=(end, height), font=0, flags=RT_HALIGN_LEFT, text=str(name)) )
		
		start = end + 20
		end   = size.width() - 10
		res.append( MultiContentEntryText(pos=(start, 0), size=(end, height), font=0, flags=RT_HALIGN_LEFT, text=str(listlength)) )
		
		return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def getServices(self):
		return [ l[0] for l in self.list ]

	def getIndexOfService(self, service):
		if service:
			idx = 0
			for x in self.list:
				if x[0] == service:
					return idx
				idx += 1
		return -1
	
	def getServiceOfIndex(self, index):
		return self.list[index] and self.list[index][0]

	def setList(self, list):
		self.l.setList( list )

	def invalidateCurrent(self):
		self.l.invalidateEntry(self.getCurrentIndex())

	def invalidateService(self, service):
		idx = self.getIndexOfService(service)
		if idx < 0: return
		self.l.invalidateEntry( idx ) # force redraw of the item

	def updateService(self, service, value):
		# Update entry in list... so next time we don't need to recalc
		idx = self.getIndexOfService(service)
		if idx >= 0:
			x = self.list[idx]
			if x[1] != value:
				l = list(x)
				l[1] = value
				self.list[idx] = tuple(l)
				self.l.invalidateEntry( idx ) # force redraw of the item

	def moveToService(self, service):
		if service is None:
			return
		idx = 0
		for x in self.list:
			if x[0] == service:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

