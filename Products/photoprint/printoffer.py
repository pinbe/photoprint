# coding=utf-8
import re

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from App.Dialogs import MessageDialog
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import implements

from Products.photoprint.interfaces import IPrintOffer
from Products.photoprint.permissions import ManagePrintOffer
import json
from Products.Plinn.utils import getAdapterByInterface


class PrintOffer(SimpleItem) :
    """
    Print offer: format, finish, frame, etc.
    """

    implements(IPrintOffer)

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
            'long_edge' : 0.,
            'copies' : 0,
            'price' : 0.,
            'prices_ranges' : [],
        },
        'finishes' : {
            'reference' : '',
            'label' : {},
            'description' : {},
            'formats_prices' : [],
        },
        'frames' : {
            'reference' : '',
            'label' : {},
            'description' : {},
            'formats_prices' : [],
            'finishes' : [],
        }
    }

    def __init__(self) :
        self.id = 'printoffer'
        self._data = ''
        emtydata = {'formats' : [],
                    'finishes' : [],
                    'frames' : []}
        self.data = emtydata

    @property
    def data(self) :
        return json.loads(self._data)

    @data.setter
    def data(self, value) :
        self._data = json.dumps(value,
                                encoding='utf-8',
                                ensure_ascii=False,
                                indent=2)

    security.declareProtected(ManagePrintOffer, 'edit')
    def edit(self, jsons) :
        self.data = json.loads(jsons)

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
    def json(self, indent=None, revision=None, REQUEST=None) :
        """ json offer data """
        if REQUEST :
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/json; charset=utf-8')

        obj = self
        if revision :
            history = getAdapterByInterface(self, 'Products.Plinn.interfaces.IContentHistory', None)
            entries = history.listEntries(first=-revision, last=-revision + 1)
            if not entries :
                return json.dumps({'error': 'no earlier revision'},
                                  encoding='utf-8',
                                  ensure_ascii=False,
                                  indent=indent)
            obj, date = history.getHistoricalRevisionByKey(entries[0]['key'])

        if indent is None :
            return obj._data
        else :
            return json.dumps(obj.data,
                              encoding='utf-8',
                              ensure_ascii=False,
                              indent=indent)

    security.declareProtected(ManagePrintOffer, 'getTemplate')
    def getTemplate(self, section, indent=None) :
        """ ready to edit new json item """
        return json.dumps(self.TEMPLATES[section],
                          encoding='utf-8',
                          ensure_ascii=False,
                          indent=indent)

    security.declareProtected(ManagePrintOffer, 'removeOfferItem')
    @postonly
    def removeOfferItem(self, section, index, REQUEST=None) :
        """ ready to edit new json item """
        if index < len(self.data[section]) :
            data = self.data
            del data[section][index]
            self.data = data
        return json.dumps({'ack' : True},
                          encoding='utf-8')

    @staticmethod
    def parseI18nString(s) :
        s = s.strip().split('\n')
        s = filter(None, s)
        s = [line.rsplit('@', 1) for line in s]
        s = dict((lang.strip(), value.strip()) for value, lang in s)
        return s

    @staticmethod
    def parseFloat(s) :
        return float(s.replace(',', '.'))

    security.declareProtected(ManagePrintOffer, 'saveOfferItem')
    @postonly
    def saveOfferItem(self, section, index, jsondata, REQUEST=None) :
        try :
            payload = json.loads(jsondata)
        except ValueError :
            return

        if section == 'formats' :
            payload['short_edge'] = PrintOffer.parseFloat(payload['short_edge'])
            payload['long_edge'] = PrintOffer.parseFloat(payload['long_edge'])
            payload['copies'] = int(payload['copies'])
            payload['price'] = PrintOffer.parseFloat(payload['price'])
            payload['label'] = PrintOffer.parseI18nString(payload['label'])

            prices_ranges = []
            for line in filter(None, payload.pop('prices_ranges').strip().split('\n')) :
                start, stop, price = \
                    re.search('^\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*(\d+[\.,]?\d*)\s*$',
                              line.strip()).groups()
                start, stop, price = int(start), int(stop), PrintOffer.parseFloat(price)
                prices_ranges.append({'start' : start,
                                      'stop' : stop,
                                      'price' : price})
            payload['prices_ranges'] = prices_ranges

        elif section in ('finishes', 'frames') :
            payload['label'] = PrintOffer.parseI18nString(payload['label'])
            payload['description'] = PrintOffer.parseI18nString(payload['description'])
            if not payload.has_key('formats_prices') :
                payload['formats_prices'] = []
            for fp in payload['formats_prices'] :
                fp['price'] = PrintOffer.parseFloat(fp['price'])
            # payload['price'] = PrintOffer.parseFloat(payload['price'])

        data = self.data
        if index < len(data[section]) :
            data[section][index] = payload
        else :
            assert len(data[section]) == index
            data[section].append(payload)

        self.data = data
        return json.dumps(self.data[section][index],
                          encoding='utf-8',
                          ensure_ascii=False)

    security.declareProtected(ManagePrintOffer, 'addInLink')
    @postonly
    def addInLink(self, section, index, reference, REQUEST=None) :
        data = self.data
        if section == 'finishes' :
            data[section][index]['formats_prices'] \
                .append({'reference' : reference, 'price' : 0.})

        if section == 'frames' :
            data[section][index]['finishes'] \
                .append(reference)
        self.data = data
        return json.dumps(self.data[section][index],
                          encoding='utf-8',
                          ensure_ascii=False)

    security.declareProtected(ManagePrintOffer, 'removeInLink')
    @postonly
    def removeInLink(self, section, index, reference, REQUEST=None) :
        data = self.data
        if section == 'finishes' :
            fpindex = [fpi['reference'] for fpi in data[section][index]['formats_prices']].index(reference)
            del data[section][index]['formats_prices'][fpindex]

        if section == 'frames' :
            data[section][index]['finishes'].remove(reference)

        self.data = data
        return json.dumps(self.data[section][index],
                          encoding='utf-8',
                          ensure_ascii=False)

    security.declareProtected(ManagePrintOffer, 'restoreRevision')
    @postonly
    def restoreRevision(self, revision, REQUEST=None) :
        history = getAdapterByInterface(self, 'Products.Plinn.interfaces.IContentHistory', None)
        entries = history.listEntries(first=-revision, last=-revision + 1)
        if not entries :
            return json.dumps({'error' : 'revision not found'},
                              encoding='utf-8',
                              ensure_ascii=False)
        rev, date = history.getHistoricalRevisionByKey(entries[0]['key'])
        self._data = rev._data
        return json.dumps({'ok':True}, encoding='utf-8', ensure_ascii=False)


InitializeClass(PrintOffer)
