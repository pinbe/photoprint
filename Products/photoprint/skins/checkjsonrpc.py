##parameters=req
from Products.Plinn.utils import json_loads
resp = {'jsonrpc': '2.0'}
try :
    req = json_loads(req)
except :
    resp.update({'error' : -32700,
                 'message' : 'Parse error'})

if not (req.get('jsonrpc') == '2.0' and req.has_key('method') and req.has_key('id')) :
    resp.update({'error' : -32600,
                 'message' : 'Invalid Request',})

resp['id'] = req.get('id')

return resp, req
