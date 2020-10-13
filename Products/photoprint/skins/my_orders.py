##parameters=b_start=0, key='created', reverse=False
from Products.CMFCore.utils import getToolByName
from Products.Plinn.PloneMisc import Batch
from Products.photoprint.utils import Message as _

wtool = getToolByName(context, 'portal_workflow')
ctool = getToolByName(context, 'portal_catalog')
mtool = getToolByName(context, 'portal_membership')
utool = getToolByName(context, 'portal_url')
portal = utool.getPortalObject()
portal_url = utool()
member = mtool.getAuthenticatedMember()
options = {}

columns = ({'key' : 'created',
            'title' : _('Date'),
            'width' : None,
            'colspan' : None}
           , {'key' : 'id',
              'title' : _('Reference'),
              'width' : None,
              'colspan' : None}
           , {'key' : 'quantity',
              'title' : _('Prints'),
              'width' : None,
              'colspan' : None}
           , {'key' : 'amount',
              'title' : _('Amount'),
              'width' : None,
              'colspan' : None}
           , {'key' : 'state',
              'title' : _('State'),
              'width' : None,
              'colspan' : None}
           )

target = context.absolute_url()

for column in columns :
    column['url'] = None
    column['images'] = None

options['columns'] = columns

orders = ctool(portal_type='Order', listCreators=member.getId(), sort_on='created', sort_order='reverse')


def beforeGetItem(item) :
    item = item.getObject()
    info = {}
    info['url'] = item.absolute_url()
    info['created'] = item.created()
    info['reference'] = item.getId()
    info['quantity'] = item.quantity
    info['amount'] = item.amountWithFees
    info['state'] = _('order-wfstate-%s' % wtool.getInfoFor(item, 'review_state', wf_id='order_workflow'))
    return info


orders = Batch(orders, context.default_batch_size, b_start, orphan=0, quantumleap=1, before_getitem=beforeGetItem)
options['orders'] = orders

breadcrumbs = [
    {'id' : 'root'
        , 'title' : portal.title
        , 'url' : portal_url},

    {'id' : 'my_orders'
        , 'title' : _('My orders')
        , 'url' : '%s/my_orders' % portal_url}
]

options['breadcrumbs'] = breadcrumbs

return context.my_orders_template(**options)
