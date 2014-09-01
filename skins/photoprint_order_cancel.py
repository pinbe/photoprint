##parameters=token=None
from Products.photoprint.utils import Message as _
if token :
    context.ppCancel(token)
context.setStatus(False, _('Your payment has been canceled. You can retry later.'))
return context.order_view()