##parameters=addTemplate='', edit='', deleteOptionContainer='', createOptionsContainer=''
from Products.CMFCore.utils import getToolByName
from Products.photoprint.utils import translate as _

utool = getToolByName(context, 'portal_url')
pptool = getToolByName(context, 'portal_photo_print')
form = context.REQUEST.form.copy()

if addTemplate:
	context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;;charset=utf-8')
	fg = form.get

	try :
		orderTemplate = pptool.addPrintOrderTemplate( context
													, title=fg('title')
													, description=fg('description')
													, productReference=fg('productReference')
													, maxCopies=fg('maxCopies')
													, price=fg('price')
													, VATRate=fg('VATRate')
													)
		templateOptions = {}
		templateOptions['o'] = orderTemplate
		classRowName = 'odd'
		if context.printingOptions.getObjectPosition(orderTemplate.getId()) % 2 == 0 :
			classRowName = 'even'
		templateOptions['classRowName'] = classRowName
		templateOptions['portal_url'] = utool()
		widget = context.get_photo_print_order_template(**templateOptions).encode('utf-8').strip()
		return '<computedField type="added">%s</computedField>' % widget
		
	except ValueError, e:
		return '<error>%s</error>' % _(e)

elif edit:
	context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml;;charset=utf-8');
	id = form.pop('id')
	try :
		orderTemplate = pptool.editPrintOrderTemplate(context, id, **form)

		templateOptions = {}
		templateOptions['o'] = orderTemplate
		classRowName = 'odd'
		if context.printingOptions.getObjectPosition(orderTemplate.getId()) % 2 == 0 :
			classRowName = 'even'
		templateOptions['classRowName'] = classRowName
		templateOptions['portal_url'] = utool()
		widget = context.get_photo_print_order_template(**templateOptions).encode('utf-8').strip()
		return '<computedField type="edited">%s</computedField>' % widget
	except ValueError, e :
		return '<error>%s</error>' % _(e)

elif createOptionsContainer :
	pptool.createPrintingOptionsContainer(context)
	context.setStatus(True, _('Printing options added.'))

elif deleteOptionContainer :	
	pptool.deletePrintingOptionsContainer(context)
	context.setStatus(True, _('Printing options deleted.'))


options = {}
options['pptool'] = pptool
options['hasPO'] = pptool.hasPrintingOptions(context)
pOptionsSrc = pptool.getPrintingOptionsSrc(context)
if pOptionsSrc :
	pourl = pOptionsSrc.getActionInfo('object/printing_settings')['url']
else :
	pourl = None
options['pourl'] = pourl

return context.photoprint_templates_edit_template(**options)
