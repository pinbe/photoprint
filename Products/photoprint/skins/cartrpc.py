##parameters=req
from Products.Plinn.utils import json_dumps
resp, req = context.checkjsonrpc(req)
if resp.has_key('error') :
    return resp

sd = context.session_data_manager.getSessionData(create = 1)
from Products.photoprint.cart import PrintCart
cart = sd.get('cart', PrintCart())

if req['method'] == 'add_to_cart' :
    cart.append(context, req['params'])
    resp['result'] = 'ok'

else :
    resp['error'] = {'code' : -32601,
                     'message' : 'Method not found'}

return json_dumps(resp)