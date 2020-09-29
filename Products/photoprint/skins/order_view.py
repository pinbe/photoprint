##parameters=
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.photoprint.price import Price
from Products.photoprint.cart import PrintCart

uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
wtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IWorkflowTool')
pptool = getUtilityByInterfaceName('Products.photoprint.interfaces.IPhotoPrintTool')
VAT = pptool.getProperty('vat_rate', 0.2)

options = {}

session = context.REQUEST.SESSION
sg = session.get
cart = sg('cart', PrintCart())
wfstate = wtool.getInfoFor(context, 'review_state', 'order_workflow')
options['wfstate'] = wfstate
options['wfhistory'] = wtool.getInfoFor(context, 'review_history', 'order_workflow')
toBePaid = wfstate == 'recorded'

if toBePaid :
    options['checkout'] = context.ppSetExpressCheckout()

if cart.locked and \
        cart.pendingOrderPath == context.getPhysicalPath() :
    options['orderIsCart'] = True
    if wfstate != 'recorded' :
        cart = PrintCart()
        session['cart'] = cart
else :
    options['orderIsCart'] = False

infos = []
for pjob in context.pjobs :
    item_data = pjob.data
    b = uidh.getBrain(pjob.cmf_uid)
    size = b.getThumbnailSize
    unit_price_ttc = reduce(lambda a, b : a + b,
                            [fff['price'] for fff in [item_data[k] for k in ('format', 'finish', 'frame')] if fff], 0)
    d = {'thumbUrl' : '%s/getThumbnail' % b.getURL(),
         'thumbHeight' : size['height'] / 2,
         'thumbWidth' : size['width'] / 2,
         'alt' : ('%s - %s' % (b.Title, b.Description)).strip(' -'),
         'pjob' : pjob,
         'unit_price' : Price(unit_price_ttc, VAT),
         }
    infos.append(d)
options['infos'] = infos
options['lines_total'] = reduce(lambda a, b: a+b, [i['unit_price'] * i['pjob'].copies for i in infos], Price(0))

options['pricesSum'] = context.price
options['discount'] = getattr(context, 'discount', 0)
options['shippingFees'] = shippingFees = context.shippingFees
options['amountWithFees'] = context.amountWithFees

return context.order_view_template(**options)
