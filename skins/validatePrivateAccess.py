##parameters=**kw
kg = lambda name : kw.get(name,'').strip()

weddingId = kg('wedding_id')
if not weddingId :
	return True

else :
	password = kg('wedding_password')
	confirm = kg('wedding_password_confirm')
	memberId = kg('member_id')
	msg = context.grantAccess(context, weddingId, password, confirm, memberId)
	if msg :
		return context.setStatus(False, msg)
	else :
		return True
