##parameters=**kw
from Products.CMFCore.utils import getToolByName
from Products.photoprint.utils import translate
from Products.CMFDefault.utils import translate as cmf_translate
rtool = getToolByName(context, 'portal_registration')
ptool = getToolByName(context, 'portal_properties')
_ = lambda msg : translate(msg, context)

kg = lambda name : kw.get(name, '').strip()

cmfprops = {'username'	: kg('member_id')
		   ,'email'		: kg('member_email')}

failMessage = rtool.testPropertiesValidity(cmfprops)
if failMessage is not None :
	return context.setStatus(False, cmf_translate(failMessage, context))

mandatoryFields = [
	  ('given_name', _('Please enter a given name.'))
	, ('name', _('Please enter a name.'))
	, ('member_email', _('Please enter an email.'))
	, ('member_id', _('Please enter a member id.'))
	, ('billing_address', _('Please enter a billing address.'))
	, ('billing_city', _('Please enter a city.'))
	, ('billing_zipcode', _('Please enter zip code.'))
	, ('country', _('Please enter a country.'))
	, ('phone', _('Please enter a phone.'))
	, ('accept_gcs', _('Please accept general conditions of sales.'))
	]

for name, failMessage in mandatoryFields :
	value = kg(name)
	if not value :
		return context.setStatus(False, failMessage)


try:
	rtool.addMember( id=kg('member_id'),
					 password=kg('password'),
					 properties={'username'			: kg('member_id')
								,'given_name'		: kg('given_name')
								,'name'				: kg('name')
								,'email'			: kg('member_email')
								,'billing_address'	: kg('billing_address')
								,'billing_city'     : kg('billing_city')
								,'billing_zipcode'	: kg('billing_zipcode')
								,'country'			: kg('country')
								,'phone'			: kg('phone')
								,'accept_gcs'		: kg('accep_gcs')} )
except ValueError, errmsg:
	return context.setStatus(False, _(errmsg))


if kg('send_password') or ptool.getProperty('validate_email') :
	rtool.registeredNotify(kg('member_id'))

return context.setStatus(True, 'Success!')
