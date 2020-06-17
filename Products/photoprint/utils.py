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
from App.config import getConfiguration
from zope.i18n import translate as i18ntranslate
from zope.i18nmessageid import MessageFactory
from zope.globalrequest import getRequest
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.Plinn.utils import _sudo
import transaction


security = ModuleSecurityInfo('Products.photoprint.utils')

security.declarePublic('translate')
def translate(msgid, mapping=None, default=None) :
    """ traduction dans le domaine photoprint """
    return i18ntranslate(msgid, domain='photoprint', mapping=mapping, context=getRequest(), default=default)

security.declarePublic('Message')
Message = _ = MessageFactory('photoprint')

security.declarePublic('grantAccess')
def grantAccess(collectionId, password, confirm, memberId) :
    utool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IURLTool')
    mtool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IMembershipTool')
    portal = utool.getPortalObject()
    
    data = portal.private_collections.data
    lines = filter(None, [l.strip() for l in data.split('\n')])
    assert len(lines) % 3 == 0
    collecInfos = {}
    for i in xrange(0, len(lines), 3) :
        collecInfos[lines[i]] = {'pw' : lines[i+1],
                                 'path' : lines[i+2]}

    if not collecInfos.has_key(collectionId) :
        transaction.abort()
        return _('Wrong private collection identifier.')
    elif password != confirm :
        transaction.abort()
        return _("Collection's password does not match confirmation.")
    else :
        if collecInfos[collectionId]['pw'] != password :
            transaction.abort()
            return _("Wrong collection's password.")
        else :
            collec = portal.unrestrictedTraverse(collecInfos[collectionId]['path'])
            def do() :
                mtool.setLocalRoles(collec, [memberId], 'Reader')
            
            _sudo(do)


def getPayPalConfig() :
    zopeConf = getConfiguration()
    try :
        conf = zopeConf.product_config['photoprint']
    except KeyError :
        EnvironmentError("No photoprint configuration found in Zope environment.")

    ppconf = {'API_ENVIRONMENT' : conf['paypal_api_environment'],
              'API_USERNAME' : conf['paypal_username'],
              'API_PASSWORD' : conf['paypal_password'],
              'API_SIGNATURE' : conf['paypal_signature']}

    return ppconf
