# coding=utf-8
import re

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from App.Dialogs import MessageDialog
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from json.decoder import JSONArray, WHITESPACE, WHITESPACE_STR
from Products.photoprint.permissions import ManagePrintOffer
import json
from json import scanner

class _JSONPersistentEncoder(json.JSONEncoder) :
    def default(self, o) :
        if type(o) is PersistentMapping :
            return dict(o)
        elif type(o) is PersistentList :
            return list(o)
        else :
            return json.JSONEncoder.default(self, o)

class _JsonPersistentDecoder(json.JSONDecoder) :

    @staticmethod
    def JSONArray(s_and_end, scan_once, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
        values, end = JSONArray(s_and_end, scan_once, _w, _ws)
        return PersistentList(values), end

    def __init__(self, encoding=None, object_hook=None, parse_float=None,
                 parse_int=None, parse_constant=None, strict=True,
                 object_pairs_hook=None):
        json.JSONDecoder.__init__(self,
                                  encoding='utf-8',
                                  object_hook=lambda d: PersistentMapping(d))
        # Unlike 'object_hook', array decoding is not hookable from json.JSONDecoder constructor…
        self.parse_array= _JsonPersistentDecoder.JSONArray
        # It's necessary to use pyton implementation (py_make_scanner)
        # because c implementation will not use our custom array decoder.
        self.scan_once = scanner.py_make_scanner(self)

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

    TEMPLATES = {
        'formats' : {
            'reference' : '',
            'label' : {},
            'short_edge' : 0.,
            'long_edge': 0.,
            'copies' : 0.,
            'price' : 0.,
            'prices_ranges' : [],
        },
        'finishes' : {
            'reference' : '',
            'label' : {},
            'description' : {},
            'price' : 0.,
            'formats' : [],
        },
        'frames' : {
            'reference' : '',
            'label' : {},
            'description' : {},
            'price' : 0.,
            'finishes': [],
        }
    }

    def __init__(self) :
        self.id = 'printoffer'
        self.data = PersistentMapping({'formats':PersistentList(),
                                       'finishes': PersistentList(),
                                       'frames': PersistentList()})


    security.declareProtected(ManagePrintOffer, 'edit')
    def edit(self, jsons) :
        self.data = json.loads(jsons, cls=_JsonPersistentDecoder)

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
    def json(self, indent=None, REQUEST=None) :
        """ json offer data """
        if REQUEST :
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/json; charset=utf-8')
        return json.dumps(self.data,
                          encoding='utf-8',
                          ensure_ascii=False,
                          cls=_JSONPersistentEncoder,
                          indent=indent)

    security.declareProtected(ManagePrintOffer, 'getTemplate')
    def getTemplate(self, section, indent=None) :
        """ ready to edit new json item """
        return json.dumps(self.TEMPLATES[section],
                          encoding='utf-8',
                          cls=_JSONPersistentEncoder,
                          indent=indent)

    security.declareProtected(ManagePrintOffer, 'removeOfferItem')
    @postonly
    def removeOfferItem(self, section, index, REQUEST=None) :
        """ ready to edit new json item """
        if index < len(self.data[section]) :
            del self.data[section][index]
        return json.dumps({'ack':True},
                          encoding='utf-8')

    @staticmethod
    def parseI18nString(s) :
        s = s.strip().split('\n')
        s = filter(None, s)
        s = [line.rsplit('@', 1) for line in s]
        s = PersistentMapping((lang.strip(), value.strip()) for value, lang in s)
        return s

    @staticmethod
    def parseFloat(s) :
        return float(s.replace(',', '.'))

    security.declareProtected(ManagePrintOffer, 'saveOfferItem')
    @postonly
    def saveOfferItem(self, section, index, jsondata, REQUEST=None) :
        try :
            payload = json.loads(jsondata, cls=_JsonPersistentDecoder)
        except ValueError :
            return

        if section == 'formats' :
            payload['short_edge'] = PrintOffer.parseFloat(payload['short_edge'])
            payload['long_edge'] = PrintOffer.parseFloat(payload['long_edge'])
            payload['copies'] = int(payload['copies'])
            payload['price'] = PrintOffer.parseFloat(payload['price'])
            payload['label'] = PrintOffer.parseI18nString(payload['label'])

            prices_ranges = PersistentList()
            for line in filter(None, payload.pop('prices_ranges').strip().split('\n')) :
                start, stop, price = \
                    re.search('^\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*(\d+[\.,]?\d*)\s*$',
                              line.strip()).groups()
                start, stop, price = int(start), int(stop), PrintOffer.parseFloat(price)
                prices_ranges.append(PersistentMapping({'start':start,
                                                        'stop': stop,
                                                        'price' : price}))
            payload['prices_ranges'] = prices_ranges

        elif section in ('finishes', 'frames') :
            payload['label'] = PrintOffer.parseI18nString(payload['label'])
            payload['description'] = PrintOffer.parseI18nString(payload['description'])
            payload['price'] = PrintOffer.parseFloat(payload['price'])


        if index < len(self.data[section]) :
            self.data[section][index] = payload
        else :
            assert len(self.data[section]) == index
            self.data[section].append(payload)

        return json.dumps(self.data[section][index],
                          encoding='utf-8',
                          cls=_JSONPersistentEncoder)

    security.declareProtected(ManagePrintOffer, 'addInLink')
    @postonly
    def addInLink(self, section, index, reference, REQUEST=None) :
        if section == 'finishes' :
            self.data[section][index]['formats'].append(reference)

        return json.dumps({'ack':True},
                          encoding='utf-8')



InitializeClass(PrintOffer)
