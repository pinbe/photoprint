##parameters=req
from Products.Plinn.utils import json_dumps

from Products.photoprint.exceptions import SoldOutError
from Products.photoprint.utils import translate

def _(message, mapping=None) : return translate(message, mapping=mapping).encode('utf-8')

resp, req = context.checkjsonrpc(req)
if resp.has_key('error') :
    return resp

sd = context.session_data_manager.getSessionData(create = 1)
from Products.photoprint.cart import PrintCart
cart = sd.get('cart', PrintCart())

method = req['method']
if method == 'add_to_cart' :
    try :
        cart.append(req['params'])
        resp['result'] = {'ok':True}
    except SoldOutError:
        resp['error'] = {
            'code' : -32603, # Internal error
            'message' : _('This item is sold out.')
        }

elif method == 'update_quantity' :
    params = req['params']
    try :
        cart.update_quantity(params['jobid'], params['quantity'])
        cart_infos = context.my_cart(infos_only = True)
        lines = []
        for job_infos in cart_infos['infos'] :
            job = job_infos['pjob']
            lines.append([_('price_and_currency', mapping={'price' : (job_infos['unit_price']).taxed}),
                          job.copies,
                          _('price_and_currency', mapping={'price' : (job_infos['unit_price'] * job.copies).taxed})
                          ])
        resp['result'] = {
            'lines' : lines,
            'totals' : {
                'lines_total' : _('price_and_currency', mapping={'price' : (cart_infos['lines_total']).taxed}),
                'tax' : _('price_and_currency', mapping={'price' : (cart_infos['lines_total']).tax}),
            }
        }

    except SoldOutError, e :
        n = e.n
        if n > 1 :
            msg = _("Only %d available copies of this photo in this size.") % n
        elif n == 1 :
            msg = _("Only one last available copy of this photo in this size.")
        else :
            msg = _("No more available copy of this photo and in this size.")

        resp['error'] = {
            'code' : -32603, # Internal error
            'message' : msg,
            'data' : {'quantity' : cart[params['jobid']].copies}
        }
    except ValueError :
        resp['error'] = {
            'code' : -32603,  # Internal error
            'message' : _('Wrong value for quantity.'),
            'data' : {'quantity' : cart[params['jobid']].copies}
        }

else :
    resp['error'] = {'code' : -32601,
                     'message' : 'Method not found'}

sd['cart'] = cart
return json_dumps(resp)