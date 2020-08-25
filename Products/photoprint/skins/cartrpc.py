##parameters=req
from Products.Plinn.utils import json_dumps

from Products.photoprint.exceptions import SoldOutError
from Products.photoprint.utils import translate


def _(message) : return translate(message, context).encode('utf-8')

resp, req = context.checkjsonrpc(req)
if resp.has_key('error') :
    return resp

sd = context.session_data_manager.getSessionData(create = 1)
from Products.photoprint.cart import PrintCart
cart = sd.get('cart', PrintCart())

if req['method'] == 'add_to_cart' :
    try :
        cart.append(context, req['params'])
        resp['result'] = {'ok':True}
    except SoldOutError:
        resp['error'] = {
            'code' : -32603, # Internal error
            'message' : _('This item is sold out.')
        }

else :
    resp['error'] = {'code' : -32601,
                     'message' : 'Method not found'}

sd['cart'] = cart
return json_dumps(resp)