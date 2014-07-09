# -*- coding: utf-8 -*-
#######################################################################################
# Copyright © 2009 Benoît Pin <pin@cri.ensmp.fr>                                      #
# Plinn - http://plinn.org                                                            #
#                                                                                     #
#                                                                                     #
#   This program is free software; you can redistribute it and/or                     #
#   modify it under the terms of the GNU General Public License                       #
#   as published by the Free Software Foundation; either version 2                    #
#   of the License, or (at your option) any later version.                            #
#                                                                                     #
#   This program is distributed in the hope that it will be useful,                   #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of                    #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                     #
#   GNU General Public License for more details.                                      #
#                                                                                     #
#   You should have received a copy of the GNU General Public License                 #
#   along with this program; if not, write to the Free Software                       #
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.   #
#######################################################################################
""" Cart definition used to store buyable prints

"""
from Globals import InitializeClass, Persistent, PersistentMapping
from Acquisition import Implicit
from AccessControl import ModuleSecurityInfo
from Products.CMFCore.utils import getToolByName
from exceptions import SoldOutError, CartLockedError
from tool import COPIES_COUNTERS
from order import CopiesCounters

from logging import getLogger
console = getLogger('Products.photoprint.cart')

CART_ITEM_KEYS = ['cmf_uid', 'printing_template', 'quantity']

msecurity = ModuleSecurityInfo('Products.photoprint.cart')
msecurity.declarePublic('PrintCart')

class PrintCart(Persistent, Implicit) :
	"""
		items are store like that:
		{<uid>:
			{<template>:quantity
			,...}
		, ...
		}
	"""
	
	__allow_access_to_unprotected_subobjects__ = 1
	
	def __init__(self) :
		self._uids = PersistentMapping()
		self._order = tuple() # products sequence order
		self._shippingInfo = PersistentMapping()
		self._confirmed = False
		self.pendingOrderPath = ''
	
	def setShippingInfo(self, **kw) :
		self._shippingInfo.update(kw)
	
	@property
	def locked(self):
		return self._confirmed
	
	def append(self, context, item) :
		if self.locked :
			raise CartLockedError
		assert isinstance(item, dict)
		keys = item.keys()
		keys.sort()
		assert keys == CART_ITEM_KEYS

		pptool = getToolByName(context, 'portal_photo_print')
		uidh   = getToolByName(context, 'portal_uidhandler')
		
		uid = item['cmf_uid']
		template = item['printing_template']
		quantity = item['quantity']
		
		photo = uidh.getObject(uid)
		pOptions = pptool.getPrintingOptionsContainerFor(photo)
		template = getattr(pOptions, template)
		templateId = template.getId()

		reference = template.productReference
		
		# check / update counters
		if template.maxCopies :
			if not hasattr(photo.aq_base, COPIES_COUNTERS) :
				setattr(photo, COPIES_COUNTERS, CopiesCounters())
			counters = getattr(photo, COPIES_COUNTERS)			
			alreadySold = counters.get(reference)
			
			if (alreadySold + quantity) > template.maxCopies :
				raise SoldOutError(template.maxCopies - alreadySold)
			else :
				counters[reference] = alreadySold + quantity
		
		if not self._uids.has_key(uid) :
			self._uids[uid] = PersistentMapping()
			self._order = self._order + (uid,)
		
		if not self._uids[uid].has_key(templateId) :
			self._uids[uid][templateId] = PersistentMapping()
			self._uids[uid][templateId]['reference'] = reference
			self._uids[uid][templateId]['quantity'] = 0

		self._uids[uid][templateId]['quantity'] += quantity
	
	def update(self, context, item) :
		if self.locked :
			raise CartLockedError
		assert isinstance(item, dict)
		keys = item.keys()
		keys.sort()
		assert keys == CART_ITEM_KEYS

		pptool = getToolByName(context, 'portal_photo_print')
		uidh   = getToolByName(context, 'portal_uidhandler')
		
		uid = item['cmf_uid']
		template = item['printing_template']
		quantity = item['quantity']
		
		photo = uidh.getObject(uid)
		pOptions = pptool.getPrintingOptionsContainerFor(photo)
		template = getattr(pOptions, template)
		templateId = template.getId()
		reference = template.productReference

		currentQuantity = self._uids[uid][templateId]['quantity']
		delta = quantity - currentQuantity
		if template.maxCopies :
			counters = getattr(photo, COPIES_COUNTERS)
			if delta > 0 :
				already = counters[reference]
				if (already + delta) > template.maxCopies :
					raise SoldOutError(template.maxCopies - already)
			counters[reference] += delta

		self._uids[uid][templateId]['quantity'] += delta
	
	def remove(self, context, uid, templateId) :
		if self.locked :
			raise CartLockedError
		pptool = getToolByName(context, 'portal_photo_print')
		uidh   = getToolByName(context, 'portal_uidhandler')
				
		photo = uidh.getObject(uid)
		pOptions = pptool.getPrintingOptionsContainerFor(photo)
		template = getattr(pOptions, templateId)
		reference = template.productReference
		
		quantity = self._uids[uid][templateId]['quantity']
		if template.maxCopies :
			counters = getattr(photo, COPIES_COUNTERS)
			counters[reference] -= quantity
		
		del self._uids[uid][templateId]
		if not self._uids[uid] :
			del self._uids[uid]
			self._order = tuple([u for u in self._order if u != uid])
		
	
	def __iter__(self) :
		for uid in self._order :
			item = {}
			item['cmf_uid'] = uid
			for templateId, rq in self._uids[uid].items() :
				item['printing_template'] = templateId
				item['quantity'] = rq['quantity']
				yield item
	
	def __nonzero__(self) :
		return len(self._order) > 0

