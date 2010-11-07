#!/usr/bin/env python
# -*- coding: utf-8 -*-
####################################################
# Copyright © 2009 Luxia SAS. All rights reserved. #
#                                                  #
# Contributors:                                    #
#  - Benoît Pin <pinbe@luxia.fr>                   #
####################################################
"""
Downloads RSS based order description and make a local human readable file tree
to facilitate printing tasks.



"""


from urllib2 import HTTPBasicAuthHandler
from urllib2 import build_opener
from urllib2 import urlopen
from xml.dom.minidom import parseString
from xml.dom import Node
from os import mkdir, chdir
from os.path import abspath, join, expanduser, exists
from getpass import getpass

ELEMENT_NODE = Node.ELEMENT_NODE

def getHttpOpener(url, login, password) :
	auth_handler = HTTPBasicAuthHandler()
	host = '/'.join(url.split('/', 3)[:3])
	auth_handler.add_password('Zope', host, login, password)
	opener = build_opener(auth_handler)
	return opener

def getXml(url, opener) :
	url = '%s?disable_cookie_login__=1' % url
	xml = opener.open(url).read()
	return xml

def genFileTree(url, login, password, dest) :
	opener = getHttpOpener(url, login, password)
	xml = getXml(url, opener)
	d = parseString(xml)
	doc = d.documentElement
	
	channel = doc.getElementsByTagName('channel')[0]
	orderName = getContentOf(channel, 'title')

	chdir(dest)
	mkdir(orderName)
	
	for item in iterElementChildsByTagName(d.documentElement, 'item') :
		ppTitle = getContentOf(item, 'pp:title')
		ppQuantity = getContentOf(item, 'pp:quantity')

		printTypePath = join(orderName, ppTitle)
		printQuantityPath = join(orderName, ppTitle, ppQuantity)
		
		if not exists(printTypePath) :
			mkdir(printTypePath)
			infoFile = open(join(printTypePath, 'info.txt'), 'w')
			infoFile.write(getContentOf(item, 'pp:title'))
			infoFile.write('\n\n')
			infoFile.write(getContentOf(item, 'pp:description'))
			infoFile.close()
		
		if not exists(printQuantityPath) :
			mkdir(printQuantityPath)

		hdUrl = '%s?disable_cookie_login__=1' % getContentOf(item, 'link')
		localFileName = getContentOf(item, 'title')
		print localFileName
		localFile = open(join(printQuantityPath, localFileName), 'w')
		localFile.write(opener.open(hdUrl).read())
		localFile.close()

def iterElementChildsByTagName(parent, tagName) :
	child  = parent.firstChild
	while child :
		if child.nodeType == ELEMENT_NODE and child.tagName == tagName :
			yield child
		child = child.nextSibling

def getContentOf(parent, tagName) :
	child  = parent.firstChild
	while child :
		if child.nodeType == ELEMENT_NODE and child.tagName == tagName :
			return child.firstChild.nodeValue.encode('utf-8')
		child = child.nextSibling
	
	raise ValueError("%r tag not found" % tagName)
			

def main() :
	url = raw_input('url flux xml de la commande : ')
	login = raw_input('login : ')
	password = getpass('mot de passe : ')
	dest = raw_input('cible [~/Desktop]')
	if not dest :
		dest = expanduser('~/Desktop')
	
	genFileTree(url, login, password, dest)

if __name__ == '__main__' :
	main()


