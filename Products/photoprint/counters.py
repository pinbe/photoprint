from Acquisition import Implicit
from persistent import Persistent
from persistent.mapping import PersistentMapping
from logging import getLogger
console = getLogger('Products.photoprint.counters')



class CopiesCounters(Persistent, Implicit) :

    def __init__(self) :
        self._mapping = PersistentMapping()

    def getBrowserId(self) :
        sdm = self.session_data_manager
        bim = sdm.getBrowserIdManager()
        browserId = bim.getBrowserId(create=1)
        return browserId

    def _checkBrowserId(self, browserId) :
        sdm = self.session_data_manager
        sd = sdm.getSessionDataByKey(browserId)
        return not not sd

    def __setitem__(self, reference, count) :
        if not self._mapping.has_key(reference) :
            self._mapping[reference] = PersistentMapping()
            self._mapping[reference]['pending'] = PersistentMapping()
            self._mapping[reference]['confirmed'] = 0

        globalCount = self[reference]
        delta = count - globalCount
        bid = self.getBrowserId()
        if not self._mapping[reference]['pending'].has_key(bid) :
            self._mapping[reference]['pending'][bid] = delta
        else :
            self._mapping[reference]['pending'][bid] += delta

    def __getitem__(self, reference) :
        item = self._mapping[reference]
        globalCount = item['confirmed']

        for browserId, count in item['pending'].items() :
            if self._checkBrowserId(browserId) :
                globalCount += count
            else :
                del self._mapping[reference]['pending'][browserId]

        return globalCount

    def get(self, reference, default=0) :
        if self._mapping.has_key(reference) :
            return self[reference]
        else :
            return default

    def getPendingCounter(self, reference) :
        bid = self.getBrowserId()
        if not self._checkBrowserId(bid) :
            console.warn('BrowserId not found: %s' % bid)
            return 0

        count = self._mapping[reference]['pending'].get(bid, None)
        if count is None :
            console.warn('No pending data found for browserId %s' % bid)
            return 0
        else :
            return count

    def confirm(self, reference, quantity) :
        pending = self.getPendingCounter(reference)
        if pending != quantity :
            console.warn('Pending quantity mismatch with the confirmed value: (%d, %d)' % (pending, quantity))

        browserId = self.getBrowserId()
        if self._mapping[reference]['pending'].has_key(browserId) :
            del self._mapping[reference]['pending'][browserId]
        self._mapping[reference]['confirmed'] += quantity

    def cancel(self, reference, quantity) :
        self._mapping[reference]['confirmed'] -= quantity

    def __str__(self) :
        return str(self._mapping)
