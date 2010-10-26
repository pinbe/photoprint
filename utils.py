# -*- coding: utf-8 -*-
############################################################
# Copyright © 2008  Benoît PIN <benoit.pin@ensmp.fr>       #
# Plinn - http://plinn.org                                 #
#                                                          #
# This program is free software; you can redistribute it   #
# and/or modify it under the terms of the Creative Commons #
# "Attribution-Noncommercial 2.0 Generic"                  #
# http://creativecommons.org/licenses/by-nc/2.0/           #
############################################################
"""
Global utilities

$Id: utils.py 651 2009-02-04 15:38:20Z pin $
$URL: http://svn.luxia.fr/svn/labo/projects/zope/photoprint/trunk/utils.py $
"""

from AccessControl import ModuleSecurityInfo
# TODO: trouver une solution…
from zope.i18n import translate as i18ntranslate
from zope.i18nmessageid import MessageFactory

security = ModuleSecurityInfo('Products.photoprint.utils')

security.declarePublic('translate')
def translate(message, context):
	""" Translate i18n message.
	"""
	# GTS = getGlobalTranslationService()
	if isinstance(message, Exception):
		try:
			message = message[0]
		except (TypeError, IndexError):
			pass
	return i18ntranslate(message, domain='photoprint', context=context.REQUEST)

security.declarePublic('Message')
Message = _ = MessageFactory('photoprint')
