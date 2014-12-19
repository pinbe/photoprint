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
Printable objects interfaces



"""

from zope.interface import Interface, Attribute

class IPrintingSupport(Interface) :
	"""
	Used to describe physical printing support
	"""
	
	title = Attribute("Support title")
	description = Attribute("support description - HTML format")
	manufacturer = Attribute("Manufacturer name")
	surfaceWeight = Attribute("Surface weight. SI unit (kg/m**2)")
	category = Attribute("Category of support (glossy, mate...)")
	availableSize = Attribute("Paper sheet or roll paper available for this support")
	

class IPrintableSheet(Interface) :
	"""
	Printable sheet description
	"""
	
	width = Attribute("Physical support width")
	height = Attribute("Physical support height")
	formatName = Attribute("Format name if exists")
	deviceMargins = Attribute("Mapping of margins indexed by device model.")
	
	sizeUnits = Attribute("Measurement units for all sizing attributes")
	
	price = Attribute("Public price of the printed sheet")
	manufacturerReference = Attribute("Manufacturer reference")
	
	
class IPrintableRoll(Interface):
	"""
	Printable roll description
	"""
	width = Attribute("Roll width")
	maxLength = Attribute("Roll length")
	formatName = Attribute("Format name if exists")
	deviceMargins = Attribute("Mapping of margins (top and bottom) indexed by device model.")
	
	sizeUnits = Attribute("Measurement units for all sizing attributes")
	
	pricePerLength = Attribute("Public price of the printed support per length unit (ie. €/m)")
	manufacturerReference = Attribute("Manufacturer reference")

class IPrintOrderTemplate(Interface):
	"""
	predefined print order, suggested by the seller.
	"""
	
	title = Attribute("order name")
	description = Attribute("order description")
	
	price = Attribute("Public price of the order")

class IPrintOrder(Interface) :
	"""
	the general purpose print order
	"""
