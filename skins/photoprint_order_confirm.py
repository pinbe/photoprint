##parameters=token=None, PayerID=None
# -*- coding: utf-8 -*-

from Products.photoprint.utils import Message as _
options = {}
if token and PayerID and context.ppPay(token, PayerID) :
    context.setStatus(True, _(u'Your payment has been accepted by PayPal.'))
    # options['current_sell_step'] = 'confirmation'
    return context.order_view()
else :
    context.setStatus(False, _('Your payment has been canceled.<br/>'
                               'You can retry with an other account / credit card by cliking on the PayPal button.<br/>'))

    return context.order_view()
