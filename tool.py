# -*- coding: utf-8 -*-
############################################################
# Copyright © 2009 Benoît PIN <pinbe@luxia.fr>             #
# Cliché - http://luxia.fr                                 #
#                                                          #
# This program is free software; you can redistribute it   #
# and/or modify it under the terms of the Creative Commons #
# "Attribution-Noncommercial 2.0 Generic"                  #
# http://creativecommons.org/licenses/by-nc/2.0/           #
############################################################
"""
Photo print tool. Used to link photo to print orders.

$Id: tool.py 1157 2009-06-13 07:14:39Z pin $
$URL: http://svn.luxia.fr/svn/labo/projects/zope/photoprint/trunk/tool.py $
"""

from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Acquisition import aq_base, aq_inner
from Globals import InitializeClass
from OFS.OrderedFolder import OrderedFolder
from Products.CMFCore.utils import UniqueObject, getToolByName
from permissions import ManagePrintOrderTemplate
from price import Price
from utils import Message as _
from Products.Plinn.utils import makeValidId
from zope.component import getUtility
from zope.component.interfaces import IFactory
from DateTime import DateTime
from Products.Plinn.utils import _sudo


PRINTING_OPTIONS_ID = 'printingOptions'
COPIES_COUNTERS = '_copies_counters'
SOLD_OUT = 'SOLD_OUT'


class PhotoPrintTool(UniqueObject, OrderedFolder) :
	"""
	Provide utilities to configure possible printing works
	over photo of the portal.
	"""
	
	id = 'portal_photo_print'
	meta_type = 'Photo print tool'
	
	security = ClassSecurityInfo()
	
	incomingOrderPath = 'commandes'
	no_shipping_threshold = 150
	shipping = 6.0
	shipping_vat = 0.196
	store_name = ''
	_order_counter = 0
	_transaction_id_counter = 0
	
	_properties = OrderedFolder._properties + (
		{'id' : 'incomingOrderPath', 		'type' : 'string',	'mode' : 'w'},
		{'id' : 'no_shipping_threshold',	'type' : 'int',		'mode' : 'w'},
		{'id' : 'shipping',					'type' : 'float',	'mode' : 'w'},
		{'id' : 'shipping_vat', 			'type' : 'float', 	'mode' : 'w'},
		{'id' : 'store_name',	 			'type' : 'string', 	'mode' : 'w'}
		)
	
	
	security.declarePublic('getPrintingOptionsFor')
	def getPrintingOptionsFor(self, ob) :
		"returns printing options for the given ob."
		optionsContainer = getattr(aq_inner(ob), PRINTING_OPTIONS_ID, None)
		if optionsContainer is None :
			return None
		
		counters = self.getCountersFor(ob)
		if counters.get(SOLD_OUT) :
			return None
		
		options = []
		for o in optionsContainer.objectValues() :
			if o.maxCopies == 0 or \
				counters.get(o.productReference, 0) < o.maxCopies :
				options.append(o)
		
		return options
	
	security.declarePublic('getPrintingOptionsContainerFor')
	def getPrintingOptionsContainerFor(self, ob):
		"""getPrintingOptionsContainerFor
		"""
		return getattr(ob, PRINTING_OPTIONS_ID, None)
	
	security.declarePrivate('getCountersFor')
	def getCountersFor(self, ob):
		if hasattr(ob.aq_self, COPIES_COUNTERS) :
			return getattr(ob, COPIES_COUNTERS)
		else :
			return {}
	
	
	security.declareProtected(ManagePrintOrderTemplate, 'createPrintingOptionsContainer')
	def createPrintingOptionsContainer(self, ob):
		container = PrintingOptionsContainer()
		setattr(ob, PRINTING_OPTIONS_ID, container)
		return getattr(ob, PRINTING_OPTIONS_ID)
	
	security.declareProtected(ManagePrintOrderTemplate, 'deletePrintingOptionsContainer')
	def deletePrintingOptionsContainer(self, ob):
		if not self.hasPrintingOptions(ob) :
			raise ValueError( _('No printing options found at %r') % ob.absolute_url() )
		else :
			delattr(ob, PRINTING_OPTIONS_ID)
	
	security.declareProtected(ManagePrintOrderTemplate, 'hasPrintingOptions')
	def hasPrintingOptions(self, ob):
		""" return boolean that instruct if there's printing
			options especially defined on ob 
		"""
		return hasattr(aq_base(ob), PRINTING_OPTIONS_ID)
	
	
	security.declareProtected(ManagePrintOrderTemplate, 'getPrintingOptionsSrc')
	def getPrintingOptionsSrc(self, ob) :
		optionsContainer = getattr(ob, PRINTING_OPTIONS_ID, None)
		if optionsContainer is None :
			return None
		src = optionsContainer.aq_inner.aq_parent
		return src
	
	security.declareProtected(ManagePrintOrderTemplate, 'getPrintOrderOptionsContainerFor')
	def getPrintOrderOptionsContainerFor(self, ob) :
		"""
		returns the printing options container or None.
		"""
		if hasattr(aq_base(ob), PRINTING_OPTIONS_ID) :
			return getattr(ob, PRINTING_OPTIONS_ID)
	
	security.declareProtected(ManagePrintOrderTemplate, 'addPrintOrderTemplate')
	@postonly
	def addPrintOrderTemplate(self
							, ob
							, title=''
							, description=''
							, productReference=''
							, maxCopies=0
							, price=0
							, VATRate=0
							, REQUEST=None):
		
		title, maxCopies, price, VATRate = PhotoPrintTool._ckeckTemplateParams(title, maxCopies, price,  VATRate)
		
		container = getattr(ob, PRINTING_OPTIONS_ID)
		
		id = makeValidId(container, title)
		
		factory = getUtility(IFactory, 'photoprint.order_template')
		orderTemplate = factory( id
							   , title=title
							   , description=description
							   , productReference=productReference
							   , maxCopies=maxCopies
							   , price=price
							   , VATRate=VATRate
							   )
		container._setObject(id, orderTemplate)
		return orderTemplate.__of__(container)
		
	
	security.declareProtected(ManagePrintOrderTemplate, 'editPrintOrderTemplate')
	@postonly
	def editPrintOrderTemplate(self, ob, id, REQUEST=None, **kw):
		container = self.getPrintingOptionsContainerFor(ob)
		orderTemplate = getattr(container, id)

		g = kw.get
		title, description, productReference, maxCopies, price, VATRate = \
			g('title', ''), g('description', ''), g('productReference'), g('maxCopies',0), g('price',0), g('VATRate', 0)
		title, maxCopies, price, VATRate = PhotoPrintTool._ckeckTemplateParams(title, maxCopies, price, VATRate)
		
		orderTemplate.edit( title=title
						  , description=description
						  , productReference=productReference
						  , maxCopies = maxCopies
						  , price=price
						  , VATRate=VATRate)
		
		return orderTemplate
	
	@staticmethod
	def _ckeckTemplateParams(title, maxCopies, price, VATRate) :
		title = title.strip()
		
		if not title :
			raise ValueError(_(u'You must enter a title.'))
		try :
			maxCopies = int(maxCopies)
		except ValueError :
			raise ValueError(_(u'You must enter an integer number\nfor the maximum number of copies.'))
		if maxCopies < 0 :
			raise ValueError(_(u'You must enter a positive value\nfor the maximum number of copies.'))
		try :
			price = float(price.replace(',', '.'))
		except ValueError :
			raise ValueError(_(u'You must enter a numeric value for the price.'))
	
		try :
			VATRate = float(VATRate.replace(',', '.')) / 100
		except ValueError :
			raise ValueError(_(u'You must enter a numeric value for the VAT rate.'))
		
		return title, maxCopies, price, VATRate
	
	security.declarePublic('addPrintOrder')
	def addPrintOrder(self, cart):
		utool = getToolByName(self, 'portal_url')
		portal = utool.getPortalObject()
		ttool = getToolByName(portal, 'portal_types')

		baseContainer = portal.unrestrictedTraverse(self.getProperty('incomingOrderPath'), None)
		if baseContainer is None:
			parts = self.getProperty('incomingOrderPath').split('/')
			baseContainer = portal
			for id in parts :
				if not hasattr(baseContainer.aq_base, id) :
					id = _sudo(lambda:ttool.constructContent('Order Folder', baseContainer, id))
				baseContainer = getattr(baseContainer, id)

		now = DateTime()
		monthId = now.strftime('%Y-%m')
		if not hasattr(baseContainer.aq_base, monthId) :
			monthId = _sudo(lambda:ttool.constructContent('Order Folder', baseContainer, monthId))
		
		container = getattr(baseContainer, monthId)

		self._order_counter += 1
		id = '%s-%d' % (monthId, self._order_counter)
		id = container.invokeFactory('Order', id)
		ob = getattr(container,id)
		ob.loadCart(cart)
		return ob
	
	security.declarePublic('getShippingFeesFor')
	def getShippingFeesFor(self, shippable=None, price=None):
		# returns Fees
		# TODO: use adapters
		# for the moment, shippable objet must provide a 'price' attribute
		
		if shippable and price :
			raise AttributeError("'shippable' and 'price' are mutually exclusive.")
		
		if shippable :
			amount = shippable.price.getValues()['taxed']
		else :
			amount = price.getValues()['taxed']
		
		threshold = self.getProperty('no_shipping_threshold')

		if amount < threshold :
			fees = Price(self.getProperty('shipping')
						, self.getProperty('shipping_vat'))
		else :
			fees = Price(0,0)
		return fees
	
	security.declarePrivate('getNextTransactionId')
	def getNextTransactionId(self):
		trid = self._transaction_id_counter
		trid = (trid + 1) % 1000000
		self._transaction_id_counter = trid
		trid = str(trid).zfill(6)
		return trid


InitializeClass(PhotoPrintTool)


class PrintingOptionsContainer(OrderedFolder) :
	meta_type = 'Printing options container'
	security = ClassSecurityInfo()
	
	def __init__(self) :
		self.id = PRINTING_OPTIONS_ID
	
	def __getitem__(self, k) :
		sd = context.session_data_manager.getSessionData(create = 1)
