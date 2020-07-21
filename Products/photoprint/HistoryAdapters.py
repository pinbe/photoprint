# coding=utf-8
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
# from Products.Plinn.ContentHistory import ContentHistory
from Products.Plinn.permissions import ViewHistory
from Products.Plinn.interfaces import IContentHistory
from .permissions import ManagePrintOffer
from ExtensionClass import Base
import Acquisition
from zope.interface import implements
from DateTime import DateTime
from base64 import b64decode
from struct import pack, unpack

class PrintOfferHistory(Base, Acquisition.Implicit) :
    security = ClassSecurityInfo()
    implements(IContentHistory)

    security.declareProtected(ViewHistory, 'listEntries')

    def __init__(self, content) :
        self._content = content

    def listEntries(self, first=0, last=20) :
        oid = self._content._p_oid
        db = self._content._p_jar.db()
        # r = db.history(oid, size=last)
        r = db.undoLog(first=first, last=last)

        if r is None :
            # storage doesn't support history
            return ()

        for d in r :
            d['time'] = DateTime(d['time'])
            d['key'] = '.'.join(map(str, unpack(">HHHH", b64decode(d['id']))))

        return r

    security.declareProtected(ViewHistory, 'compare')
    def compare(self, leftkey, rightkey) :
        raise NotImplementedError

    security.declareProtected(ManagePrintOffer, 'restore')
    def restore(self, key) :
        raise NotImplementedError


InitializeClass(PrintOfferHistory)