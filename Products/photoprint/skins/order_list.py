##parameters=b_start=0, key='created', reverse=False
from Products.CMFCore.utils import getToolByName
from Products.Plinn.PloneMisc import Batch
from Products.photoprint.utils import Message as _
from ZTUtils import make_query

wtool = getToolByName(context, 'portal_workflow')
mtool = getToolByName(context, 'portal_membership')
options = {}
folders = context.contentValues({'portal_type':'Order Folder'})
options['folders'] = folders

columns = ( {'key': 'created',
			 'title': _('Date'),
			 'width': None,
			 'colspan': None}
			, {'key': 'customer',
			 'title': _('Customer'),
			 'width': None,
			 'colspan': None}
			, {'key': 'id',
			 'title': _('Reference'),
			 'width': None,
			 'colspan': None}
			, {'key': 'quantity',
			 'title': _('Prints'),
			 'width': None,
			 'colspan': None}
			, {'key': 'amount',
			 'title': _('Amount'),
			 'width': None,
			 'colspan': None }
			, {'key': 'state',
			 'title': _('State'),
			 'width': None,
			 'colspan': None }
			)

target = context.absolute_url()

for column in columns :
	images = []
	if key == column['key']:
		if reverse :
			toggleImg = getattr(context, 'arrowDown.gif')
			alt = _('descending sort')
		else :
			toggleImg = getattr(context, 'arrowUp.gif')
			alt = _('ascending sort')
		query = make_query(key=column['key'], reverse = not reverse)
		images.append( {'src' : toggleImg.absolute_url(), 'alt' : alt} )
	else :
		query = make_query(key=column['key'], reverse = reverse)
	
	column['url'] = '%s?%s' % (target, query)
	column['images'] = images

options['columns'] = columns

def getReviewState(item) :
	return wtool.getInfoFor(item, 'review_state', wf_id='order_workflow')

sortFuncs = {'created'	: lambda a, b : cmp(a.created(), b.created())
			,'customer'	: lambda a, b : cmp(a.Creator(), b.Creator())
			,'id'		: lambda a, b : cmp(a.getId(), b.getId())
			,'quantity'	: lambda a, b : cmp(a.quantity, b.quantity)
			,'amount'	: lambda a, b : cmp(a.amountWithFees.getValues()['taxed'], b.amountWithFees.getValues()['taxed'])
			,'state'	: lambda a, b : cmp(getReviewState(a), getReviewState(b))}

orders = context.contentValues({'portal_type':'Order'})
step = reverse and -1 or 1
orders.sort(sortFuncs[key])
orders = orders[::step]
options['key'] = key
options['reverse'] = reverse

def beforeGetItem(item) :
	info = {}
	info['url'] = item.absolute_url()
	info['created'] = item.created()
	info['reference'] = item.getId()
	info['quantity'] = item.quantity
	info['price'] = item.amountWithFees
	info['state'] = wtool.getInfoFor(item, 'review_state', wf_id='order_workflow')
	customer = mtool.getMemberById(item.Creator())
	if customer :
		info['customer'] = customer.getMemberFullName()
	else :
		info['customer'] = item.Creator()
	return info
	
orders = Batch(orders, context.default_batch_size, b_start, orphan=0, quantumleap=1, before_getitem=beforeGetItem)
options['orders'] = orders

return context.order_list_template(**options)
