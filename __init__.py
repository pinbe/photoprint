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
Photo print product. Used to order photo prints.



"""
from Products.CMFCore import utils as cmfutils
import tool
import utils
import order
import cart
import exceptions


tools = (tool.PhotoPrintTool,)

def initialize(registrar) :
	cmfutils.ToolInit('Photoprint Tool',
					   tools = tools,
					   icon = 'tool.gif'
					   ).initialize(registrar)
