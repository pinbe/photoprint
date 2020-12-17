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
""" Cart definition used to store buyable prints

"""
from logging import getLogger

from AccessControl import ModuleSecurityInfo
from Acquisition import Implicit
from Globals import Persistent, PersistentMapping
from Products.CMFCore.utils import getUtilityByInterfaceName

from Products.photoprint.printjob import PrintJob
from counters import CopiesCounters
from exceptions import SoldOutError, CartLockedError
from tool import COPIES_COUNTERS

console = getLogger('Products.photoprint.cart')
msecurity = ModuleSecurityInfo('Products.photoprint.cart')
msecurity.declarePublic('PrintCart')


class PrintCart(Persistent, Implicit) :
    """ Print Cart
    """

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self) :
        self._orders = PersistentMapping()
        self._sequence_order = tuple()
        self._shippingInfo = PersistentMapping()
        self._confirmed = False
        self.pendingOrderPath = ''

    def setShippingInfo(self, **kw) :
        self._shippingInfo.update(kw)

    @property
    def locked(self) :
        return self._confirmed

    def append(self, item) :
        if self.locked :
            raise CartLockedError

        pptool = getUtilityByInterfaceName('Products.photoprint.interfaces.IPhotoPrintTool')
        reified_order = pptool.reifyPrintOrder(item)

        order_id = '_'.join((item['cmf_uid'],
                    reified_order['format']['reference'],
                    reified_order['finish']['reference'],
                    reified_order['frame']['reference'] if reified_order['frame'] else '',
                    ))

        if reified_order['format']['copies'] > 0 :  # Édition limitée
            format_reference = reified_order['format']['reference']
            uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
            photo = uidh.getObject(item['cmf_uid'])
            if not hasattr(photo.aq_base, COPIES_COUNTERS) :
                setattr(photo, COPIES_COUNTERS, CopiesCounters())
            counters = getattr(photo, COPIES_COUNTERS)
            alreadySold = counters.get(format_reference)

            if (alreadySold + 1) > reified_order['format']['copies'] :
                raise SoldOutError(reified_order['format']['copies'] - alreadySold)
            else :
                counters[format_reference] = alreadySold + 1

        if not self._orders.has_key(order_id) :
            self._orders[order_id] = PrintJob(order_id, item['cmf_uid'], reified_order)
            self._sequence_order = self._sequence_order + (order_id,)
        else :
            self._orders[order_id].copies += 1

        return self._orders[order_id]


    def update_quantity(self, jobid, quantity) :
        if self.locked :
            raise CartLockedError

        if type(quantity) != int or \
            quantity <= 0 :
            raise ValueError()

        job = self._orders[jobid]
        reified_order = job.data

        if reified_order['format']['copies'] > 0 : # Édition limitée
            currentQuantity = job.copies
            delta = quantity - currentQuantity
            uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
            photo = uidh.getObject(job.cmf_uid)
            counters = getattr(photo, COPIES_COUNTERS)
            format_reference = reified_order['format']['reference']
            if delta > 0 :
                alreadySold = counters[format_reference]
                if (alreadySold + delta) > reified_order['format']['copies'] :
                    raise SoldOutError(reified_order['format']['copies'] - alreadySold)
            counters[format_reference] += delta

        job.copies = quantity

    def remove(self, jobid) :
        if self.locked :
            raise CartLockedError

        job = self._orders[jobid]
        reified_order = job.data

        if reified_order['format']['copies'] > 0 : # Édition limitée
            job = self._orders[jobid]
            reified_order = job.data

            if reified_order['format']['copies'] > 0 :  # Édition limitée
                uidh = getUtilityByInterfaceName('Products.CMFUid.interfaces.IUniqueIdHandler')
                photo = uidh.getObject(job.cmf_uid)
                counters = getattr(photo, COPIES_COUNTERS)
                format_reference = reified_order['format']['reference']
                counters[format_reference] -= job.copies

        del self._orders[jobid]
        sequence = list(self._sequence_order)
        sequence.remove(jobid)
        self._sequence_order = tuple(sequence)

    def __iter__(self) :
        for order_id in self._sequence_order :
            yield self._orders[order_id]

    def __nonzero__(self) :
        return len(self._sequence_order) > 0

    def __getitem__(self, item) :
        if hasattr(self, item) :
            return getattr(self, item)
        else :
            return self._orders[item]

    def __len__(self) :
        return reduce(lambda a,b: a+b, [order.copies for order in self._orders.values()], 0)
