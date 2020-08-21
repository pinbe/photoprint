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
"""
Photo print tool. Used to link photo to print orders.



"""
import json

from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Acquisition import aq_base, aq_inner
from Globals import InitializeClass
from OFS.OrderedFolder import OrderedFolder
from Products.CMFCore.utils import UniqueObject, getToolByName, getUtilityByInterfaceName

from Products.photoprint.printoffer import PrintOffer
from permissions import ManagePrintOrderTemplate
from price import Price
from utils import Message as _
from Products.Plinn.utils import makeValidId, getBestTranslationLanguage
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
		for fmt in optionsContainer.printoffer.data['formats'] :
			if fmt['copies'] == 0 or \
				counters.get(fmt['reference'], 0) < fmt['copies'] :
				options.append(fmt)

		return options

	security.declarePublic('getEffectivePrintingOptionsFor')
	@postonly
	def getEffectivePrintingOptionsFor(self, cmf_uid, REQUEST=None):
		uidtool = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
		proptool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IPropertiesTool')
		ob = uidtool.getObject(cmf_uid)
		optionsContainer = getattr(aq_inner(ob), PRINTING_OPTIONS_ID, None)

		ret = None
		if optionsContainer is not None :
			ret = data = optionsContainer.printoffer.data
			counters = self.getCountersFor(ob)
			for fmt in data['formats'] :
				effective_price = fmt['price']
				if fmt['copies'] == 0 : # Édition illimitée du format
					available_copies = True
				else :
					already_sold = counters.get(fmt['reference'], 0)
					available_copies = fmt['copies'] - already_sold
					if available_copies > 0 and \
					   fmt['prices_ranges'] and \
					   already_sold + 1 >= fmt['prices_ranges'][0]['start'] :
						for price_range in fmt['prices_ranges'] :
							if price_range['start'] <= available_copies+1 <= price_range['stop'] :
								effective_price = price_range['price']
								break
				del fmt['prices_ranges']
				fmt['price'] = effective_price
				fmt['available_copies'] = available_copies

			for item in data['formats'] + data['finishes'] + data['frames'] :
				for field in ('label', 'description') :
					if not item.has_key(field) : continue
					field_langs = item[field].keys()
					lang = getBestTranslationLanguage(field_langs, self)
					item[field] = item[field][lang]

		return json.dumps(ret)

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
		offer = PrintOffer()
		self._setObject(offer.id, offer)

	
	def __getitem__(self, k) :
		sd = context.session_data_manager.getSessionData(create = 1)
