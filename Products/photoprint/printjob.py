# coding=utf-8
import json

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.permissions import ModifyPortalContent, ManagePortal
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from zope.component.factory import Factory

from Products.photoprint.permissions import ManagePrintOrders
from Products.photoprint.price import Price
from Products.photoprint.tool import COPIES_COUNTERS
from Products.photoprint.utils import getPayPalConfig
from Products.Plinn.utils import getBestTranslationLanguage

# from interfaces import IPrintOrder

try :
    from paypal.interface import PayPalInterface
    paypalAvailable = True
except ImportError :
    paypalAvailable = False
from logging import getLogger
console = getLogger('Products.photoprint.order')



class PrintJob(SimpleItem) :
    security = ClassSecurityInfo()

    def __init__(self, id, cmf_uid, data) :
        self.id = id
        self.cmf_uid = cmf_uid
        self.copies = 1
        self._data = ''
        self.data = data


    @property
    def data(self) :
        d = json.loads(self._data)
        for fff in [d[k] for k in ('format', 'finish', 'frame')] :
            if not fff : continue
            for field in ('label', 'description') :
                if not fff.has_key(field) : continue
                field_langs = fff[field].keys()
                lang = getBestTranslationLanguage(field_langs)
                fff[field] = fff[field][lang]
        return d

    @property
    def price(self) :
        d = self.data
        price = 0.
        for name in ('format', 'finish', 'frame') :
            opt = d.get(name)
            if not opt:
                continue
            price += opt['price']
        return price * self.copies

    @data.setter
    def data(self, value) :
        self._data = json.dumps(value, encoding='utf-8', ensure_ascii=False)

    @property
    def json(self) :
        return {'id': self.id,
                'cmf_uid': self.cmf_uid,
                'copies': self.copies,
                'data': self.data
                }

InitializeClass(PrintJob)
PrintJobFactory = Factory(PrintJob)


class PrintOrder(PortalContent, DefaultDublinCoreImpl) :
    # implements(IPrintOrder)
    security = ClassSecurityInfo()

    def __init__(self, id) :
        DefaultDublinCoreImpl.__init__(self)
        self.id = id
        self.pjobs = tuple()
        # billing and shipping addresses
        self.billing = PersistentMapping()
        self.shipping = PersistentMapping()
        self.shippingFees = Price(0, 0)
        self._paypalLog = PersistentList()


    @property
    def price(self) :
        pptool = getUtilityByInterfaceName('Products.photoprint.interfaces.IPhotoPrintTool')
        VAT = pptool.getProperty('vat_rate', 0.2)
        return reduce(lambda a, b: a+b, [Price(pjob.price, VAT) for pjob in self.pjobs], Price(0, VAT))

    @property
    def amountWithFees(self) :
        return self.price + self.shippingFees

    @property
    def quantity(self) :
        return reduce(lambda a,b:a+b, map(lambda pjob: pjob.copies, self.pjobs), 0)

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
    def loadCart(self, cart) :
        pptool = getUtilityByInterfaceName('Products.photoprint.interfaces.IPhotoPrintTool')
        uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
        mtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IMembershipTool')
        utool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IURLTool')

        pjobs = []
        for pjob in cart :
            pjobs.append(pjob._getCopy(self))
            photo = uidh.getObject(pjob.cmf_uid)
            # confirm counters
            fmt = pjob.data['format']
            if fmt['copies'] :
                counters = pptool.getCountersFor(photo)
                counters.confirm(fmt['reference'], pjob.copies)

        self.pjobs = tuple(pjobs)
        discount_script = getattr(utool.getPortalObject(), 'photoprint_discount', None)
        if discount_script :
            self.discount = discount_script(self.price, self.quantity)

        member = mtool.getAuthenticatedMember()
        mg = lambda name : member.getProperty(name, '')
        billing = {'name' : member.getMemberFullName(nameBefore=0)
            , 'address' : mg('billing_address')
            , 'city' : mg('billing_city')
            , 'zipcode' : mg('billing_zipcode')
            , 'country' : mg('country')
            , 'phone' : mg('phone')}
        self.editBilling(**billing)

        sg = lambda name : cart._shippingInfo.get(name, '')
        shipping = {'name' : sg('shipping_fullname')
            , 'address' : sg('shipping_address')
            , 'city' : sg('shipping_city')
            , 'zipcode' : sg('shipping_zipcode')
            , 'country' : sg('shipping_country')}
        self.editShipping(**shipping)

        self.shippingFees = pptool.getShippingFeesFor(shippable=self)

        cart._confirmed = True
        cart.pendingOrderPath = self.getPhysicalPath()

    security.declareProtected(ManagePrintOrders, 'resetCopiesCounters')
    def resetCopiesCounters(self) :
        pptool = getUtilityByInterfaceName('Products.photoprint.interfaces.IPhotoPrintTool')
        uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')

        for pjob in self.pjobs :
            photo = uidh.getObject(pjob.cmf_uid)
            counters = pptool.getCountersFor(photo)
            format = pjob.data['format']
            if format['copies'] > 0 : # eg: if limited edition
                counters.cancel(format['reference'], pjob.copies)

        # for item in self.items :
        #     photo = uidh.getObject(item['cmf_uid'])
        #     counters = getattr(photo, COPIES_COUNTERS, None)
        #     if counters :
        #         counters.cancel(item['productReference'],
        #                         item['quantity'])

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
                   'ALLOWNOTE' : 0,  # The buyer is unable to enter a note to the merchant.
                   'HDRIMG' : '%s/logo.gif' % portal_url,
                   'EMAIL' : member.getProperty('email'),
                   'SOLUTIONTYPE' : 'Sole',
                   # Buyer does not need to create a PayPal account to check out. This is referred to as PayPal Account Optional.
                   'LANDINGPAGE' : 'Billing',  # Non-PayPal account
                   'BRANDNAME' : portal.getProperty('title'),
                   'GIFTMESSAGEENABLE' : 0,
                   'GIFTRECEIPTENABLE' : 0,
                   'BUYEREMAILOPTINENABLE' : 0,  # Do not enable buyer to provide email address.
                   'NOSHIPPING' : 1,  # PayPal does not display shipping address fields whatsoever.
                   'PAYMENTREQUEST_0_SHIPTONAME' : self.billing['name'],
                   'PAYMENTREQUEST_0_SHIPTOSTREET' : self.billing['address'],
                   'PAYMENTREQUEST_0_SHIPTOCITY' : self.billing['city'],
                   'PAYMENTREQUEST_0_SHIPTOZIP' : self.billing['zipcode'],
                   'PAYMENTREQUEST_0_SHIPTOPHONENUM' : self.billing['phone'],
                   }

        # if len(self.pjobs) > 1 :
        #     quantitySum = reduce(lambda a, b : a + b, [item['quantity'] for item in self.items])
        # else :
        #     quantitySum = self.pjobs[0]['quantity']

        quantitySum = reduce(lambda a, b : a + b, [pjob.copies for pjob in self.pjobs], 0)

        total = round(self.amountWithFees.getValues()['taxed'], 2)

        options['L_PAYMENTREQUEST_0_NAME0'] = 'Commande photo ref. %s' % self.getId()
        if quantitySum == 1 :
            options['L_PAYMENTREQUEST_0_DESC0'] = "Commande d'un tirage photographique"
        else :
            options['L_PAYMENTREQUEST_0_DESC0'] = 'Commande de %d tirages photographiques' % quantitySum
        options['L_PAYMENTREQUEST_0_AMT0'] = total
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
    def ppPay(self, token, payerid) :
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
                    wtool.doActionFor(self
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
        return {'quantity' : self.quantity,
                'price' : self.price}


InitializeClass(PrintOrder)
PrintOrderFactory = Factory(PrintOrder)
