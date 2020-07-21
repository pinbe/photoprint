# coding=utf-8
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.Plinn.ContentHistory import ContentHistory
from Products.Plinn.HistoryAdapters import html_ready_diff
from Products.Plinn.permissions import ViewHistory

from .permissions import ManagePrintOffer


class PrintOfferHistory(ContentHistory) :
    security = ClassSecurityInfo()

    security.declareProtected(ViewHistory, 'compare')
    def compare(self, leftkey, rightkey) :
        leftRev, leftDate = self.getHistoricalRevisionByKey(leftkey)
        rightRev, rightDate = self.getHistoricalRevisionByKey(rightkey)

        left = leftRev.json()
        right = rightRev.json()

        infos = {'diff' : html_ready_diff(left, right)
            , 'leftDate' : leftDate
            , 'rightDate' : rightDate
            , 'structure' : False}
        return infos

    security.declareProtected(ManagePrintOffer, 'restore')
    def restore(self, key) :
        raise NotImplementedError


InitializeClass(PrintOfferHistory)