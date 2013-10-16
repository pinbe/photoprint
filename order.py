# -*- coding: utf-8 -*-
#######################################################################################
#   Plinn - http://plinn.org                                                          #
#   Copyright (C) 2009-2013  Benoît PIN <benoit.pin@ensmp.fr>                         #
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
Print order classes



"""

from Globals import InitializeClass, PersistentMapping, Persistent
from Acquisition import Implicit
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from zope.interface import implements
from zope.component.factory import Factory
from persistent.list import PersistentList
from OFS.SimpleItem import SimpleItem
from ZTUtils import make_query
from DateTime import DateTime
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.permissions import ModifyPortalContent, View, ManagePortal
from Products.CMFCore.utils import getToolByName, getUtilityByInterfaceName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.Plinn.utils import getPreferredLanguages
from interfaces import IPrintOrderTemplate, IPrintOrder
from permissions import ManagePrintOrderTemplate, ManagePrintOrders
from price import Price
from xml.dom.minidom import Document
from tool import COPIES_COUNTERS
from App.config import getConfiguration
try :
    from paypal.interface import PayPalInterface
    paypalAvailable = True
except ImportError :
    paypalAvailable = False
from logging import getLogger
console = getLogger('Products.photoprint.order')


def getPayPalConfig() :
    zopeConf = getConfiguration()
    try :
        conf = zopeConf.product_config['photoprint']
    except KeyError :
        EnvironmentError("No photoprint configuration found in Zope environment.")
    
    ppconf = {'API_ENVIRONMENT'      : conf['paypal_api_environment'],
              'API_USERNAME'         : conf['paypal_username'],
              'API_PASSWORD'         : conf['paypal_password'],
              'API_SIGNATURE'        : conf['paypal_signature']}
    
    return ppconf


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
        self._paypalLog = PersistentList()
    
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
        
            d = {'cmf_uid'          : item['cmf_uid']
                ,'url'              : photo.absolute_url()
                ,'title'            : template.title
                ,'description'      : template.description
                ,'unit_price'       : Price(uPrice._taxed, uPrice._rate)
                ,'quantity'         : quantity
                ,'productReference' : reference
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
        billing = {'name'       : member.getMemberFullName(nameBefore=0)
                  ,'address'    : mg('billing_address')
                  ,'city'       : mg('billing_city')
                  ,'zipcode'    : mg('billing_zipcode')
                  ,'country'    : mg('country')
                  ,'phone'      : mg('phone') }
        self.editBilling(**billing)
        
        sg = lambda name : cart._shippingInfo.get(name, '')
        shipping = {'name'      : sg('shipping_fullname')
                   ,'address'   : sg('shipping_address')
                   ,'city'      : sg('shipping_city')
                   ,'zipcode'   : sg('shipping_zipcode')
                   ,'country'   : sg('shipping_country')}
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


    def _initPayPalInterface(self) :
        config = getPayPalConfig()
        config['API_AUTHENTICATION_MODE'] = '3TOKEN'
        ppi = PayPalInterface(**config)
        return ppi
    
    
    @staticmethod
    def recordifyPPResp(response) :
        d = {}
        d['zopeTime'] = DateTime()
        for k, v in response.raw.iteritems() :
            if len(v) == 1 :
                d[k] = v[0]
            else :
                d[k] = v
        return d
    
    # paypal api
    security.declareProtected(ModifyPortalContent, 'ppSetExpressCheckout')
    def ppSetExpressCheckout(self) :
        utool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IURLTool')
        mtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IMembershipTool')
        portal_url = utool()
        portal = utool.getPortalObject()
        member = mtool.getAuthenticatedMember()
        
        options = {'PAYMENTREQUEST_0_CURRENCYCODE' : 'EUR',
                   'PAYMENTREQUEST_0_PAYMENTACTION' : 'Sale',
                   'RETURNURL' : '%s/photoprint_order_confirm' % self.absolute_url(),
                   'CANCELURL' : '%s/photoprint_order_cancel' % self.absolute_url(),
                   'ALLOWNOTE' : 0, # The buyer is unable to enter a note to the merchant.
                   'HDRIMG' : '%s/logo.gif' % portal_url,
                   'EMAIL' : member.getProperty('email'),
                   'SOLUTIONTYPE' : 'Sole', #  Buyer does not need to create a PayPal account to check out. This is referred to as PayPal Account Optional.
                   'LANDINGPAGE' : 'Billing', # Non-PayPal account
                   'BRANDNAME' : portal.getProperty('title'),
                   'GIFTMESSAGEENABLE' : 0,
                   'GIFTRECEIPTENABLE' : 0,
                   'BUYEREMAILOPTINENABLE' : 0, # Do not enable buyer to provide email address.
                   'NOSHIPPING' : 1, # PayPal does not display shipping address fields whatsoever.
                   'PAYMENTREQUEST_0_SHIPTONAME' : self.billing['name'],
                   'PAYMENTREQUEST_0_SHIPTOSTREET' : self.billing['address'],
                   'PAYMENTREQUEST_0_SHIPTOCITY' : self.billing['city'],
                   'PAYMENTREQUEST_0_SHIPTOZIP' : self.billing['zipcode'],
                   'PAYMENTREQUEST_0_SHIPTOPHONENUM' : self.billing['phone'],
                   }
        
        if len(self.items) > 1 :
            quantitySum = reduce(lambda a, b : a['quantity'] + b['quantity'], self.items)
        else :
            quantitySum = self.items[0]['quantity']
        total = round(self.amountWithFees.getValues()['taxed'], 2)
        
        options['L_PAYMENTREQUEST_0_NAME0'] = 'Commande realis photo ref. %s' % self.getId()
        if quantitySum == 1 :
            options['L_PAYMENTREQUEST_0_DESC0'] = "Commande d'un tirage photographique"
        else :
            options['L_PAYMENTREQUEST_0_DESC0'] = 'Commande de %d tirages photographiques' % quantitySum
        options['L_PAYMENTREQUEST_0_AMT0'] =  total
        options['PAYMENTINFO_0_SHIPPINGAMT'] = round(self.shippingFees.getValues()['taxed'], 2)
        options['PAYMENTREQUEST_0_AMT'] = total

        ppi = self._initPayPalInterface()
        response = ppi.set_express_checkout(**options)
        response = PrintOrder.recordifyPPResp(response)
        self._paypalLog.append(response)
        response['url'] = ppi.generate_express_checkout_redirect_url(response['TOKEN'])
        console.info(options)
        console.info(response)
        return response
        
    security.declarePrivate('ppGetExpressCheckoutDetails')
    def ppGetExpressCheckoutDetails(self, token) :
        ppi = self._initPayPalInterface()
        response = ppi.get_express_checkout_details(TOKEN=token)
        response = PrintOrder.recordifyPPResp(response)
        self._paypalLog.append(response)
        return response
    
    security.declarePrivate('ppDoExpressCheckoutPayment')
    def ppDoExpressCheckoutPayment(self, token, payerid, amt) :
        ppi = self._initPayPalInterface()
        response = ppi.do_express_checkout_payment(PAYMENTREQUEST_0_PAYMENTACTION='Sale',
                                                   PAYMENTREQUEST_0_AMT=amt,
                                                   PAYMENTREQUEST_0_CURRENCYCODE='EUR',
                                                   TOKEN=token,
                                                   PAYERID=payerid)
        response = PrintOrder.recordifyPPResp(response)
        self._paypalLog.append(response)
        return response
    
    security.declareProtected(ModifyPortalContent, 'ppPay')
    def ppPay(self, token, payerid):
        # assure le paiement paypal en une passe :
        # récupération des détails et validation de la transaction.
        
        wtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IWorkflowTool')
        wfstate = wtool.getInfoFor(self, 'review_state', 'order_workflow')
        paid = wfstate == 'paid'
        
        if not paid :
            details = self.ppGetExpressCheckoutDetails(token)

            if payerid != details['PAYERID'] :
                return False

            if details['ACK'] == 'Success' :
                response = self.ppDoExpressCheckoutPayment(token,
                                                           payerid,
                                                           details['AMT'])
                if response['ACK'] == 'Success' and \
                    response['PAYMENTINFO_0_ACK'] == 'Success' and \
                    response['PAYMENTINFO_0_PAYMENTSTATUS'] == 'Completed' :
                    self.paid = (DateTime(), 'paypal')
                    wtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IWorkflowTool')
                    wtool.doActionFor( self
                                     , 'paypal_pay'
                                     , wf_id='order_workflow'
                                     , comments='Paiement par PayPal')
                    return True
            return False
        else :
            return True
    
    security.declareProtected(ModifyPortalContent, 'ppCancel')
    def ppCancel(self, token) :
        details = self.ppGetExpressCheckoutDetails(token)
    
    security.declareProtected(ManagePortal, 'getPPLog')
    def getPPLog(self) :
        return self._paypalLog
        
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
