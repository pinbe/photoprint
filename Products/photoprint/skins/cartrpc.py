##parameters=req
from Products.Plinn.utils import json_loads, json_dumps
resp, req = context.checkjsonrpc(req)
if resp.has_key('error') :
    return resp

if req['method'] == 'add_to_cart' :
    resp['result'] = 'ok'

else :
    resp['error'] = {'code' : -32601,
                     'message' : 'Method not found'}

return json_dumps(resp)