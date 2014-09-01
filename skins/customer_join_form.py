##parameters=add=''
from Products.CMFCore.utils import getToolByName
from Products.Plinn.utils import translate
from ZTUtils import make_query as mq
_ = lambda msg : translate(msg, context)
ptool = getToolByName(script, 'portal_properties')
atool = getToolByName(script, 'portal_actions')
validate_email = ptool.getProperty('validate_email')
options = {}
options['validate_email'] = validate_email

req = context.REQUEST
resp = req.RESPONSE
form = req.form
fg = lambda name : form.get(name,'').strip()


if add and \
	context.validatePassword(**form) and \
	context.customer_add_control(**form) and \
	context.validatePrivateAccess(**form) :
	came_from = fg('came_from')
	if came_from :
		return context.setRedirect(	atool, 'user/logged_in'
								  , came_from = came_from
								  , __ac_name=fg('member_id')
								  , __ac_password=fg('password'))
		#return resp.redirect('%s?%s' % ( came_from, mq(__ac_name=fg('member_id'), __ac_password=fg('password'), noajax='1')) )
	else:
		options['member_id'] = fg('member_id')
		options['password'] = fg('password')
		options['form_action'] = target = atool.getActionInfo('user/logged_in')['url']
		return context.confirm_join_template(**options)

continuationFields = [
	  'given_name'
	, 'name'
	, 'member_email'
	, 'member_id'
	, 'password'
	, 'confirm'
	, 'send_password'
	, 'wedding_id'
	, 'wedding_password'
	, 'wedding_password_confirm'
	, 'billing_address'
	, 'billing_city'
	, 'billing_zipcode'
	, 'country'
	, 'phone'
	, 'accept_gcs']


for name in continuationFields :
	options[name] = fg(name)

# TODO try to be more clever...
if not options['country']:
	options['country'] = 'FR'
options['came_from'] = fg('came_from')
return context.customer_join_template(**options)
