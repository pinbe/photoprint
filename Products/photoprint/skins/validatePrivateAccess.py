##parameters=**kw
from Products.photoprint.utils import grantAccess
kg = lambda name : kw.get(name,'').strip()

collectionId = kg('collection_id')
if not collectionId :
	return True

else :
	password = kg('collection_password')
	confirm = kg('collection_password_confirm')
	memberId = kg('member_id')
	msg = grantAccess(collectionId, password, confirm, memberId)
	if msg :
		return context.setStatus(False, msg)
	else :
		return True
