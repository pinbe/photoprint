# coding=utf-8
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from App.Dialogs import MessageDialog
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from persistent.mapping import PersistentMapping

from Products.photoprint.permissions import ManagePrintOffer
import json

class _JSONPersistentMappingEncoder(json.JSONEncoder) :
    def default(self, o) :
        if type(o) is PersistentMapping :
            return dict(o)
        else :
            return json.JSONEncoder.default(self, o)

class PrintOffer(SimpleItem) :
    """
    Print offer: format, finish, frame, etc.
    """

    security = ClassSecurityInfo()
    manage_options = (
        {'label' : 'Data',
         'action' : 'manage_data'},
    ) + SimpleItem.manage_options


    security.declareProtected(ManagePrintOffer, 'manage_data')
    manage_data = PageTemplateFile('www/manage_data',
                                   globals(),
                                   __name__='manage_data')

    def __init__(self) :
        self.id = 'printoffer'
        self.data = PersistentMapping()


    security.declareProtected(ManagePrintOffer, 'edit')
    def edit(self, jsons) :
        self.data = json.loads(jsons,
                               encoding='utf-8',
                               object_hook=lambda d : PersistentMapping(d))

    security.declareProtected(ManagePrintOffer, 'manage_editJSON')
    @postonly
    def manage_editJSON(self, jsoncode, REQUEST=None) :
        self.edit(jsoncode)
        return MessageDialog(
                title='Saved',
                message='Print offer JSON have been updated.',
                action='manage_data'
        )


    security.declarePublic('json')
    def json(self, indent=None) :
        """ json offer data """
        return json.dumps(self.data, cls=_JSONPersistentMappingEncoder, indent=indent)

InitializeClass(PrintOffer)
