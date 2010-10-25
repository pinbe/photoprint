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
Print order classes

$Id: order.py 1357 2009-09-07 16:06:05Z pin $
$URL: http://svn.luxia.fr/svn/labo/projects/zope/photoprint/trunk/order.py $
"""

from Globals import InitializeClass, PersistentMapping, Persistent
from Acquisition import Implicit
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from zope.interface import implements
from zope.component.factory import Factory
from OFS.SimpleItem import SimpleItem
from ZTUtils import make_query
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.permissions import ModifyPortalContent, View
from Products.CMFCore.utils import getToolByName, getUtilityByInterfaceName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.Plinn.utils import getPreferredLanguages
from interfaces import IPrintOrderTemplate, IPrintOrder
from permissions import ManagePrintOrderTemplate, ManagePrintOrders
from price import Price
from utils import Message as _
from utils import translate
from xml.dom.minidom import Document
from tool import COPIES_COUNTERS
from App.config import getConfiguration
try :
	from Products.cyberplus import CyberplusConfig
	from Products.cyberplus import CyberplusRequester
	from Products.cyberplus import CyberplusResponder
	from Products.cyberplus import LANGUAGE_VALUES as CYBERPLUS_LANGUAGES
except ImportError:
	pass
from logging import getLogger
console = getLogger('Products.photoprint.order')


def _getCyberplusConfig() :
	zopeConf = getConfiguration()
	try :
		conf = zopeConf.product_config['cyberplus']
	except KeyError :
		EnvironmentError("No cyberplus configuration found in Zope environment.")
	
	merchant_id = conf['merchant_id']
	bin_path = conf['bin_path']
	path_file = conf['path_file']
	merchant_country = conf['merchant_country']
	
	config = CyberplusConfig(merchant_id,
							 bin_path,
							 path_file,
				 			 merchant_country=merchant_country)
	return config


class PrintOrderTemplate(SimpleItem) :
	"""
	predefined print order
	"""
	implements(IPrintOrderTemplate)
	
	security = ClassSecurityInfo()
	
	def __init__(self
				, id
				, title=''
				, description=''
				, productReference=''
				, maxCopies=0
				, price=0
				, VATRate=0) :
		self.id = id
		self.title = title
		self.description = description
		self.productReference = productReference
		self.maxCopies = maxCopies # 0 means unlimited
		self.price = Price(price, VATRate)
	
	security.declareProtected(ManagePrintOrderTemplate, 'edit')
	def edit( self
			, title=''
			, description=''
			, productReference=''
			, maxCopies=0
			, price=0
			, VATRate=0 ) :
		self.title = title
		self.description = description
		self.productReference = productReference
		self.maxCopies = maxCopies
		self.price = Price(price, VATRate)
	
	security.declareProtected(ManagePrintOrderTemplate, 'formWidgetData')
	def formWidgetData(self, REQUEST=None, RESPONSE=None):
		"""formWidgetData documentation
		"""
		d = Document()
		d.encoding = 'utf-8'
		root = d.createElement('formdata')
		d.appendChild(root)
		
		def gua(name) :
			return str(getattr(self, name, '')).decode('utf-8')
		
		id = d.createElement('id')
		id.appendChild(d.createTextNode(self.getId()))
		root.appendChild(id)
		
		title = d.createElement('title')
		title.appendChild(d.createTextNode(gua('title')))
		root.appendChild(title)
		
		description = d.createElement('description')
		description.appendChild(d.createTextNode(gua('description')))
		root.appendChild(description)
		
		productReference = d.createElement('productReference')
		productReference.appendChild(d.createTextNode(gua('productReference')))
		root.appendChild(productReference)
		
		maxCopies = d.createElement('maxCopies')
		maxCopies.appendChild(d.createTextNode(str(self.maxCopies)))
		root.appendChild(maxCopies)
		
		price = d.createElement('price')
		price.appendChild(d.createTextNode(str(self.price.taxed)))
		root.appendChild(price)
		
		vatrate = d.createElement('VATRate')
		vatrate.appendChild(d.createTextNode(str(self.price.vat)))
		root.appendChild(vatrate)

		if RESPONSE is not None :
			RESPONSE.setHeader('content-type', 'text/xml; charset=utf-8')
			
			manager = getToolByName(self, 'caching_policy_manager', None)
			if manager is not None:
				view_name = 'formWidgetData'
				headers = manager.getHTTPCachingHeaders(
								  self, view_name, {}
								  )
				
				for key, value in headers:
					if key == 'ETag':
						RESPONSE.setHeader(key, value, literal=1)
					else:
						RESPONSE.setHeader(key, value)
				if headers:
					RESPONSE.setHeader('X-Cache-Headers-Set-By',
									   'CachingPolicyManager: %s' %
									   '/'.join(manager.getPhysicalPath()))
		
		
		return d.toxml('utf-8')

		
InitializeClass(PrintOrderTemplate)
PrintOrderTemplateFactory = Factory(PrintOrderTemplate)

class PrintOrder(PortalContent, DefaultDublinCoreImpl) :
	
	implements(IPrintOrder)
	security = ClassSecurityInfo()
	
	def __init__( self, id) :
		DefaultDublinCoreImpl.__init__(self)
		self.id = id
		self.items = []
		self.quantity = 0
		self.price = Price(0, 0)
		# billing and shipping addresses
		self.billing = PersistentMapping()
		self.shipping = PersistentMapping()
		self.shippingFees = Price(0,0)
		self._paymentResponse = PersistentMapping()
	
	@property
	def amountWithFees(self) :
		return self.price + self.shippingFees
	
	
	security.declareProtected(ModifyPortalContent, 'editBilling')
	def editBilling(self
					, name
					, address
					, city
					, zipcode
					, country
					, phone) :
		self.billing['name'] = name
		self.billing['address'] = address
		self.billing['city'] = city
		self.billing['zipcode'] = zipcode
		self.billing['country'] = country
		self.billing['phone'] = phone
	
	security.declareProtected(ModifyPortalContent, 'editShipping')
	def editShipping(self, name, address, city, zipcode, country) :
		self.shipping['name'] = name
		self.shipping['address'] = address
		self.shipping['city'] = city
		self.shipping['zipcode'] = zipcode
		self.shipping['country'] = country
	
	security.declarePrivate('loadCart')
	def loadCart(self, cart):
		pptool = getToolByName(self, 'portal_photo_print')
		uidh = getToolByName(self, 'portal_uidhandler')
		mtool = getToolByName(self, 'portal_membership')
		
		items = []
		for item in cart :
			photo = uidh.getObject(item['cmf_uid'])
			pOptions = pptool.getPrintingOptionsContainerFor(photo)
			template = getattr(pOptions, item['printing_template'])

			reference = template.productReference
			quantity = item['quantity']
			uPrice = template.price
			self.quantity += quantity
		
			d = {'cmf_uid'			: item['cmf_uid']
				,'url'				: photo.absolute_url()
				,'title'			: template.title
				,'description'		: template.description
				,'unit_price'		: Price(uPrice._taxed, uPrice._rate)
				,'quantity'			: quantity
				,'productReference'	: reference
				}
			items.append(d)
			self.price += uPrice * quantity
			# confirm counters
			if template.maxCopies :
				counters = getattr(photo, COPIES_COUNTERS)
				counters.confirm(reference, quantity)
				
		self.items = tuple(items)

		member = mtool.getAuthenticatedMember()
		mg = lambda name : member.getProperty(name, '')
		billing = {'name' 		: member.getMemberFullName(nameBefore=0)
				  ,'address'	: mg('billing_address')
				  ,'city'		: mg('billing_city')
				  ,'zipcode'	: mg('billing_zipcode')
				  ,'country'	: mg('country')
				  ,'phone'		: mg('phone') }
		self.editBilling(**billing)
		
		sg = lambda name : cart._shippingInfo.get(name, '')
		shipping = {'name' 		: sg('shipping_fullname')
				   ,'address'	: sg('shipping_address')
				   ,'city'		: sg('shipping_city')
				   ,'zipcode'	: sg('shipping_zipcode')
				   ,'country'	: sg('shipping_country')}
		self.editShipping(**shipping)
		
		self.shippingFees = pptool.getShippingFeesFor(shippable=self)
		
		cart._confirmed = True
		cart.pendingOrderPath = self.getPhysicalPath()
	
	security.declareProtected(ManagePrintOrders, 'resetCopiesCounters')
	def resetCopiesCounters(self) :
		pptool = getToolByName(self, 'portal_photo_print')
		uidh = getToolByName(self, 'portal_uidhandler')
		
		for item in self.items :
			photo = uidh.getObject(item['cmf_uid'])
			counters = getattr(photo, COPIES_COUNTERS, None)
			if counters :
				counters.cancel(item['productReference'],
								item['quantity'])
	
	security.declareProtected(View, 'getPaymentRequest')
	def getPaymentRequest(self) :
		config = _getCyberplusConfig()
		requester = CyberplusRequester(config)
		hereurl = self.absolute_url()
		amount = self.price + self.shippingFees
		amount = amount.getValues()['taxed']
		amount = amount * 100
		amount = str(int(round(amount, 0)))
		pptool = getToolByName(self, 'portal_photo_print')
		transaction_id = pptool.getNextTransactionId()
		
		userLanguages = getPreferredLanguages(self)
		for pref in userLanguages :
			lang = pref.split('-')[0]
			if lang in CYBERPLUS_LANGUAGES :
				break
		else :
			lang = 'en'
		
		options = {  'amount': amount
					,'cancel_return_url'		: '%s/paymentCancelHandler' % hereurl
					,'normal_return_url'		: '%s/paymentManualResponseHandler' % hereurl
					,'automatic_response_url'	:'%s/paymentAutoResponseHandler' % hereurl
					,'transaction_id'			: transaction_id
					,'order_id' 				: self.getId()
					,'language'					: lang
				   }
		req = requester.generateRequest(options)
		return req
	
	def _decodeCyberplusResponse(self, form) :
		config = _getCyberplusConfig()
		responder = CyberplusResponder(config)
		response = responder.getResponse(form)
		return response
	
	def _compareWithAutoResponse(self, manu) :
		keys = manu.keys()
		auto = self._paymentResponse
		autoKeys = auto.keys()
		if len(keys) != len(autoKeys) :
			console.warn('Manual has not the same keys.\nauto: %r\nmanual: %r' % \
				(sorted(autoKeys), sorted(keys)))
		else :
			for k, v in manu.items() :
				if not auto.has_key(k) :
					console.warn('%r field only found in manual response.' % k)
				else :
					if v != auto[k] :
						console.warn('data mismatch for %r\nauto: %r\nmanual: %r' % (k, auto[k], v))
	
	def _checkOrderId(self, response) :
		expected = self.getId()
		assert expected == response['order_id'], \
			"Cyberplus response transaction_id doesn't match the order object:\n" \
			"expected: %s\n" \
			"found: %s" % (expected, response['transaction_id'])
	
	def _executeOrderWfTransition(self, response) :
		if CyberplusResponder.transactionAccepted(response) :
			wfaction = 'auto_accept_payment'
		elif CyberplusResponder.transactionRefused(response) :
			self.resetCopiesCounters()
			wfaction = 'auto_refuse_payment'
		elif CyberplusResponder.transactionCanceled(response) :
			wfaction = 'auto_cancel_order'
		else :
			# transaction failed
			wfaction = 'auto_transaction_failed'

		wtool = getToolByName(self, 'portal_workflow')
		wf = wtool.getWorkflowById('order_workflow')
		tdef = wf.transitions.get(wfaction)
		wf._changeStateOf(self, tdef)
		wtool._reindexWorkflowVariables(self)
	
	security.declarePublic('paymentAutoResponseHandler')
	@postonly
	def paymentAutoResponseHandler(self, REQUEST) :
		"""\
		Handle cyberplus payment auto response.
		"""
		response = self._decodeCyberplusResponse(REQUEST.form)
		self._checkOrderId(response)
		self._paymentResponse.update(response)
		self._executeOrderWfTransition(response)
	
	@postonly
	def paymentManualResponseHandler(self, REQUEST) :
		"""\
		Handle cyberplus payment manual response.
		"""
		response = self._decodeCyberplusResponse(REQUEST.form)
		self._checkOrderId(response)
		
		autoResponse = self._paymentResponse
		if not autoResponse :
			console.warn('Manual response handled before auto response at %s' % '/'.join(self.getPhysicalPath()))
			self._paymentResponse.update(response)
			self._executeOrderWfTransition(response)
		else :
			self._compareWithAutoResponse(response)
			
		url = '%s?%s' % (self.absolute_url(),
						make_query(portal_status_message=translate('Your payment is complete.', self).encode('utf-8'))
						)
		return REQUEST.RESPONSE.redirect(url)
	
	@postonly
	def paymentCancelHandler(self, REQUEST) :
		"""\
		Handle cyberplus cancel response.
		This handler can be invoqued in two cases:
		- the user cancel the payment form
		- the payment transaction has been refused
		"""
		response = self._decodeCyberplusResponse(REQUEST.form)
		self._checkOrderId(response)
		
		if self._paymentResponse :
			# normaly, it happens when the transaction is refused by cyberplus.
			self._compareWithAutoResponse(response)

		
		if CyberplusResponder.transactionRefused(response) :
			if not self._paymentResponse :
				console.warn('Manual response handled before auto response at %s' % '/'.join(self.getPhysicalPath()))
				self._paymentResponse.update(response)
				self._executeOrderWfTransition(response)
			
			msg = 'Your payment has been refused.'

		else :
			self._executeOrderWfTransition(response)
			msg = 'Your payment has been canceled. You will be able to pay later.'

		url = '%s?%s' % (self.absolute_url(),
						make_query(portal_status_message= \
						translate(msg, self).encode('utf-8'))
						)
		return REQUEST.RESPONSE.redirect(url)
		
	
	def getCustomerSummary(self) :
		' '
		return {'quantity':self.quantity,
				'price':self.price}
			
	
InitializeClass(PrintOrder)
PrintOrderFactory = Factory(PrintOrder)


class CopiesCounters(Persistent, Implicit) :

	def __init__(self):
		self._mapping = PersistentMapping()
	
	def getBrowserId(self):
		sdm = self.session_data_manager
		bim = sdm.getBrowserIdManager()
		browserId = bim.getBrowserId(create=1)
		return browserId
	
	def _checkBrowserId(self, browserId) :
		sdm = self.session_data_manager
		sd = sdm.getSessionDataByKey(browserId)
		return not not sd
	
	def __setitem__(self, reference, count) :
		if not self._mapping.has_key(reference):
			self._mapping[reference] = PersistentMapping()
			self._mapping[reference]['pending'] = PersistentMapping()
			self._mapping[reference]['confirmed'] = 0
		
		globalCount = self[reference]
		delta = count - globalCount
		bid = self.getBrowserId()
		if not self._mapping[reference]['pending'].has_key(bid) :
			self._mapping[reference]['pending'][bid] = delta
		else :
			self._mapping[reference]['pending'][bid] += delta
		
	
	def __getitem__(self, reference) :
		item = self._mapping[reference]
		globalCount = item['confirmed']
		
		for browserId, count in item['pending'].items() :
			if self._checkBrowserId(browserId) :
				globalCount += count
			else :
				del self._mapping[reference]['pending'][browserId]

		return globalCount
	
	def get(self, reference, default=0) :
		if self._mapping.has_key(reference) :
			return self[reference]
		else :
			return default
	
	def getPendingCounter(self, reference) :
		bid = self.getBrowserId()
		if not self._checkBrowserId(bid) :
			console.warn('BrowserId not found: %s' % bid)
			return 0

		count = self._mapping[reference]['pending'].get(bid, None)
		if count is None :
			console.warn('No pending data found for browserId %s' % bid)
			return 0
		else :
			return count
	
	def confirm(self, reference, quantity) :
		pending = self.getPendingCounter(reference)
		if pending != quantity :
			console.warn('Pending quantity mismatch with the confirmed value: (%d, %d)' % (pending, quantity))

		browserId = self.getBrowserId()
		if self._mapping[reference]['pending'].has_key(browserId) :
			del self._mapping[reference]['pending'][browserId]
		self._mapping[reference]['confirmed'] += quantity
	
	def cancel(self, reference, quantity) :
		self._mapping[reference]['confirmed'] -= quantity
	
	def __str__(self):
		return str(self._mapping)
