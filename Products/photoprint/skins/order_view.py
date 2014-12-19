##parameters=
from Products.CMFCore.utils import getToolByName
from Products.photoprint.price import Price
from Products.photoprint.cart import PrintCart
uidh = getToolByName(context, 'portal_uidhandler')
wtool = getToolByName(context, 'portal_workflow')

options = {}

quantity = 0
prices = []
infos = []

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

for item in context.items :
	d = {'title'		: item['title']
		,'description'	: item['description']
		,'unit_price'	: item['unit_price']
		,'quantity'		: item['quantity']
		,'total'		: item['unit_price'] * item['quantity']
		}

	b = uidh.queryBrain(item['cmf_uid'])
	if b :
		size = b.getThumbnailSize
		thumbInfo = {'thumbUrl'		: '%s/getThumbnail' % b.getURL()
					,'thumbHeight'	: size['height'] / 2
					,'thumbWidth'	: size['width'] / 2
					,'alt'			: ('%s - %s' % (b.Title, b.Description)).strip(' -')
					}
		d.update(thumbInfo)
	quantity += d['quantity']
	prices.append(d['total'])
	infos.append(d)

options['infos'] = infos
options['quantity'] = quantity
options['pricesSum'] = context.price
options['discount'] = getattr(context, 'discount', 0)
options['shippingFees'] = shippingFees = context.shippingFees
options['total'] = context.amountWithFees

return context.order_view_template(**options)