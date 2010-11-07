# -*- coding: utf-8 -*-
############################################################
# Copyright © 2009 Benoît PIN <pinbe@luxia.fr>             #
# Cliché - http://luxia.fr                                 #
#                                                          #
# This program is free software; you can redistribute it   #
# and/or modify it under the terms of the Creative Commons #
# "Attribution-Noncommercial 2.0 Generic"                  #
# http://creativecommons.org/licenses/by-nc/2.0/           #
############################################################
"""
photoprint specific permissions



"""

from AccessControl import ModuleSecurityInfo
from Products.CMFCore.permissions import setDefaultRoles

security = ModuleSecurityInfo('Products.photoprint.permissions')

ManagePrintOrderTemplate = "Manage print order template"
security.declarePublic('ManagePrintOrderTemplate')
setDefaultRoles(ManagePrintOrderTemplate, ('Manager',))

AddPrintOrder =  "Add print order"
security.declarePublic('AddPrintOrder')
setDefaultRoles(AddPrintOrder, ('Authenticated', 'Manager',))

ListPrintOrders = "List print orders"
security.declarePublic('ListPrintOrders')
setDefaultRoles(ListPrintOrders, ('Manager',))

ManagePrintOrders = "Manage print orders"
security.declarePublic('ManagePrintOrders')
setDefaultRoles(ManagePrintOrders, ('Manager',))
