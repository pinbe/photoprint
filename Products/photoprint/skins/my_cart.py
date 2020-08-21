##parameters=order='', shipping='', set_shipping=''
from Products.CMFCore.utils import getToolByName
from Products.Portfolio.utils import translate
from Products.photoprint.exceptions import SoldOutError
from Products.photoprint.cart import PrintCart
from Products.photoprint.price import Price

def _(message) : return translate(message, context).encode('utf-8')

options = {}
session = context.REQUEST.SESSION
sg = session.get
cart = sg('cart', PrintCart())
utool = getToolByName(context, 'portal_url')
portal_url = utool()
portal = utool.getPortalObject()
uidh = portal.portal_uidhandler
pptool = portal.portal_photo_print
mtool = portal.portal_membership
isAnon = mtool.isAnonymousUser()
form = context.REQUEST.form
nextStep = None

if cart.locked :
    pendingOrder = context.restrictedTraverse(cart.pendingOrderPath)
    return context.setRedirect(pendingOrder, 'object/view', ajax=form.get('ajax'))

if order :
    if isAnon :
        atool = portal.portal_actions
        came_from = '%s/my_cart' % portal_url
        return context.setRedirect(atool, 'customer/login', came_from=came_from, ajax=form.get('ajax'))

if shipping :
    member = mtool.getAuthenticatedMember()
    options['shipping_fullname']    = member.getMemberFullName(nameBefore=0)
    options['shipping_address']     = member.getProperty('billing_address')
    options['shipping_city']        = member.getProperty('billing_city')
    options['shipping_zipcode']     = member.getProperty('billing_zipcode')
    options['shipping_country']     = member.getProperty('country')
    return context.shipping_template(**options)

if set_shipping :
    fg = lambda name : form.get(name,'').strip()
    if context.shipping_set_control(**form) :
        order = pptool.addPrintOrder(cart)
        return context.setRedirect(order, 'object/view', ajax=fg('ajax'))
    else :
        for name in [ 'shipping_fullname'
                    , 'shipping_address'
                    , 'shipping_city'
                    , 'shipping_zipcode'
                    , 'shipping_country'] :
            options[name] = fg(name)
        return context.shipping_template(**options)

if isAnon :
    nextStep = {'name':'order', 'value' : _('Order >>')}
else :
    nextStep = {'name':'shipping', 'value' : _('Shipping >>')}
    

msg = ''

for k, v in form.items() :
    if hasattr(v, 'items') :
        uid, templateId = k.split('_',1)
        if v.has_key('refresh') :
            quantity = v['quantity']
            try :
                quantity = int(quantity)
            except ValueError:
                msg = _('You must enter an integer for quantity (found: %s)') % quantity
            if quantity <= 0 :
                msg = _('You must enter a positive value for quantity (found: %s)') % quantity
            if not msg :
                item = {'cmf_uid'           : uid
                       ,'printing_template' : templateId
                       ,'quantity'          : quantity}
                try :
                    cart.update(context, item)
                except SoldOutError, e :
                    n = e.n
                    if n > 1 :
                        msg = _("Only %d available copies of this photo in this size.") % n
                    elif n == 1 :
                        msg = _("Only one last available copy of this photo in this size.")
                    else :
                        msg = _("No more available copy of this photo and in this size.")
                    

        if v.has_key('delete'):
            cart.remove(context, uid, templateId)

options['empty'] = not cart
infos = []
prices = []
quantityTotal = 0
for item in cart :
    b = uidh.getBrain(item['cmf_uid'])
    poptions = pptool.getPrintingOptionsContainerFor(b.getObject())
    pt = getattr(poptions, item['printing_template'])
    size = b.getThumbnailSize
    d = {'thumbUrl' : '%s/getThumbnail' % b.getURL()
        ,'thumbHeight' : size['height'] / 2
        ,'thumbWidth' : size['width'] / 2
        ,'alt' : ('%s - %s' % (b.Title, b.Description)).strip(' -')
        ,'cmf_uid':b.cmf_uid
        ,'title': pt.title
        ,'description': pt.description
        ,'quantity':item['quantity']
        ,'amount': '%s €' % (pt.price * item['quantity']).taxed
        ,'templateId': pt.getId()
        }
    quantityTotal += item['quantity']
    prices.append(pt.price * item['quantity'])
    infos.append(d)

options['infos'] = infos
if len(prices) == 1:
    pricesTotal = prices[0]
elif len(prices) > 1 :
    pricesTotal = reduce(lambda a, b : a + b, prices)


if prices :
    options['pricesTotal'] = pricesTotal
    options['quantityTotal'] = quantityTotal
    discount = 0
    if context.get('photoprint_discount') :
        discount = context.photoprint_discount(pricesTotal, quantityTotal)
    options['discount'] = discount
    shippingFees = pptool.getShippingFeesFor(price=pricesTotal)
    options['shippingFees'] = shippingFees
    coeff = (100 - discount) / 100.
    options['totalAmount'] = pricesTotal * coeff + shippingFees

breadcrumbs = [
    { 'id'      : 'root'
    , 'title'   : portal.title
    , 'url'     : portal_url},

    {'id'       : 'my_cart'
    ,'title'    : _('My cart')
    , 'url'     : '%s/my_cart' % portal_url}
    ]

options['breadcrumbs'] = breadcrumbs

if msg :
    context.REQUEST.other['portal_status_message'] = msg
options['cartIsOrder'] = False
options['nextStep'] = nextStep
return context.my_cart_template(**options)
