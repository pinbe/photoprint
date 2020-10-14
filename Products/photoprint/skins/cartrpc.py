##parameters=req
from Products.Plinn.utils import json_dumps

from Products.photoprint.exceptions import SoldOutError, CartLockedError
from Products.photoprint.utils import translate
from Products.photoprint.cart import PrintCart
from Products.photoprint.price import Price
from Products.CMFCore.utils import getUtilityByInterfaceName


def _(message, mapping=None) : return translate(message, mapping=mapping).encode('utf-8')


pptool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IPropertiesTool')
VAT = pptool.getProperty('vat_rate', 0.2)

resp, req = context.checkjsonrpc(req)
if resp.has_key('error') :
    return resp

sd = context.session_data_manager.getSessionData(create=1)
cart = sd.get('cart', PrintCart())
uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')


def get_cart_table_data() :
    cart_infos = context.my_cart(infos_only=True)
    lines = []
    for job_infos in cart_infos['infos'] :
        job = job_infos['pjob']
        lines.append([_('price_and_currency', mapping={'price' : (job_infos['unit_price']).taxed}),
                      job.copies,
                      _('price_and_currency', mapping={'price' : (job_infos['unit_price'] * job.copies).taxed})
                      ])
    return {
        'lines' : lines,
        'totals' : {
            'lines_total' : _('price_and_currency', mapping={'price' : (cart_infos['lines_total']).taxed}),
            'tax' : _('price_and_currency', mapping={'price' : (cart_infos['lines_total']).tax}),}
    }


method = req['method']
if method == 'add_to_cart' :
    try :
        pjob = cart.append(req['params'])
        item_data = pjob.data
        b = uidh.getBrain(pjob.cmf_uid)
        size = b.getThumbnailSize
        unit_price_ttc = reduce(lambda a, b : a + b,
                                [fff['price'] for fff in [item_data[k] for k in ('format', 'finish', 'frame')] if fff],
                                0)
        d = {'thumbUrl' : '%s/getThumbnail' % b.getURL(),
             'thumbHeight' : size['height'] / 2,
             'thumbWidth' : size['width'] / 2,
             'alt' : ('%s - %s' % (b.Title, b.Description)).strip(' -'),
             'pjob' : pjob,
             'unit_price' : Price(unit_price_ttc, VAT),
             }

        resp['result'] = {
            'ok' : True,
            'html' : context.my_cart_added_template(infos=[d])
        }
    except SoldOutError :
        resp['error'] = {
            'code' : -32603,  # Internal error
            'message' : _('This item is sold out.')
        }

elif method == 'update_quantity' :
    params = req['params']
    try :
        cart.update_quantity(params['jobid'], params['quantity'])
        resp['result'] = get_cart_table_data()

    except SoldOutError, e :
        n = e.n
        if n > 1 :
            msg = _("Only %d available copies of this photo in this size.") % n
        elif n == 1 :
            msg = _("Only one last available copy of this photo in this size.")
        else :
            msg = _("No more available copy of this photo and in this size.")

        resp['error'] = {
            'code' : -32603,  # Internal error
            'message' : msg,
            'data' : {'quantity' : cart[params['jobid']].copies}
        }
    except ValueError :
        resp['error'] = {
            'code' : -32603,  # Internal error
            'message' : _('Wrong value for quantity.'),
            'data' : {'quantity' : cart[params['jobid']].copies}
        }

elif method == 'delete_job' :
    params = req['params']
    try :
        cart.remove(params['jobid'])
        resp['result'] = get_cart_table_data()
    except CartLockedError, e :
        resp['error'] = {
            'code' : -32603,  # Internal error
            'message' : _("Your cart is locked:\nplease complete your current order first."),
            'data' : {'quantity' : cart[params['jobid']].copies}
        }


else :
    resp['error'] = {'code' : -32601,
                     'message' : 'Method not found'}

sd['cart'] = cart
return json_dumps(resp)
