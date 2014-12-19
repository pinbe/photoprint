##parameters=
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.exceptions import zExceptions_Unauthorized
uidh = getToolByName(context, 'portal_uidhandler')
options = {}

infos = []
for item in context.items :
	try :
		b = uidh.getBrain(item['cmf_uid'])
	except : # TODO: catch only UniqueIdError (not public yet:)
		raise zExceptions_Unauthorized
	size = b.getThumbnailSize
	d = {'thumbUrl'		: '%s/getThumbnail' % b.getURL()
		,'thumbHeight'	: size['height'] / 2
		,'thumbWidth'	: size['width'] / 2
		,'alt'			: ('%s - %s' % (b.Title, b.Description)).strip(' -')
		,'title'		: item['title']
		,'description'	: item['description']
		,'unit_price'	: item['unit_price']
		,'quantity'		: item['quantity']
		,'total'		: item['unit_price'] * item['quantity']
		,'url'			: b.getURL()
		,'id'			: b.getId
		}
	infos.append(d)

options['infos'] = infos
if traverse_subpath and traverse_subpath[-1] == 'xml' :
	channel_info = {'title' :'Commande %s' % context.getId()
					,'url' : context.absolute_url() 
					,'description'	:'' # TODO mettre l'identification client
					, }
					
	options['channel_info'] = channel_info
	options['listItemInfos'] = infos
	return context.order_printing_list_template_xml(**options)
else :
	return context.order_printing_list_template(**options)