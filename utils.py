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



"""

from AccessControl import ModuleSecurityInfo
from zope.i18n import translate as i18ntranslate
from zope.i18nmessageid import MessageFactory
from zope.globalrequest import getRequest

security = ModuleSecurityInfo('Products.photoprint.utils')

security.declarePublic('translate')
def translate(msgid, mapping=None, default=None) :
    """ traduction dans le domaine photoprint """
    return i18ntranslate(msgid, domain='photoprint', mapping=mapping, context=getRequest(), default=default)

security.declarePublic('Message')
Message = _ = MessageFactory('photoprint')
