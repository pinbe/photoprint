##parameters=
from Products.CMFCore.utils import getToolByName
from Products.Portfolio.utils import translate
from Products.photoprint.exceptions import SoldOutError, CartLockedError
def _(message) : return translate(message, context).encode('utf-8')

form = context.REQUEST.form
ajax = form.get('ajax')
if ajax :
	context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;;charset=utf-8')

atool = getToolByName(context, 'portal_actions')

quantity = form.get('quantity')

msg = ''
try :
	quantity = int(quantity)
except ValueError :
	msg = _('You must enter an integer for quantity (found: %s)') % quantity

if quantity <= 0 :
	msg = _('You must enter a positive value for quantity (found: %s)') % quantity

if msg :
	if ajax :
		return "<error>%s</error>" % msg
	else :
		context.setStatus(False, msg)
		return context.setRedirect(atool, 'user/panier')

sd = context.session_data_manager.getSessionData(create = 1)

from Products.CMFCore.utils import getToolByName
uidh = getToolByName(context, 'portal_uidhandler')
item = {'cmf_uid':form['cmf_uid']
	   ,'printing_template':form['printing_template']
	   ,'quantity':quantity
	   }
photo = uidh.getBrain(item['cmf_uid'])

from Products.photoprint.cart import PrintCart
cart = sd.get('cart', PrintCart())
try :
	cart.append(context, item)
except SoldOutError, e :
	n = e.n
	if n > 1 :
		msg = _("Only %d available copies of this photo in this size.") % n
	elif n == 1 :
		msg = _("Only one last available copy of this photo in this size.")
	else :
		msg = _("No more available copy of this photo in this size.")
	
	if ajax :
		return "<error>%s</error>" % msg
	else :
		context.setStatus(False, msg)
		return context.setRedirect(atool, 'user/panier')

except CartLockedError :
	msg = _("Your cart is locked:\nplease complete your current order first.")
	if ajax :
		return "<error>%s</error>" % msg
	else :
		context.setStatus(False, msg)
		return context.setRedirect(atool, 'user/panier')
	
sd['cart'] = cart

if ajax :
	return '<confirm duration="2">%s</confirm>' % _('Added to cart.')
else :
	context.setStatus(False, _('Added to cart.'))
	return context.setRedirect(atool, 'user/panier')
