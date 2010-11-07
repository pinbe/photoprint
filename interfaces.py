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
