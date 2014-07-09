# -*- coding: utf-8 -*-
#######################################################################################
# Copyright © 2009 Benoît Pin <pin@cri.ensmp.fr>                                      #
# Plinn - http://plinn.org                                                            #
#                                                                                     #
#                                                                                     #
#   This program is free software; you can redistribute it and/or                     #
#   modify it under the terms of the GNU General Public License                       #
#   as published by the Free Software Foundation; either version 2                    #
#   of the License, or (at your option) any later version.                            #
#                                                                                     #
#   This program is distributed in the hope that it will be useful,                   #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of                    #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                     #
#   GNU General Public License for more details.                                      #
#                                                                                     #
#   You should have received a copy of the GNU General Public License                 #
#   along with this program; if not, write to the Free Software                       #
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.   #
#######################################################################################
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
