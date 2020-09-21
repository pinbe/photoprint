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

CART_ITEM_KEYS = ['cmf_uid', 'printing_template', 'quantity']

msecurity = ModuleSecurityInfo('Products.photoprint.cart')
msecurity.declarePublic('PrintCart')


class PrintCart(Persistent, Implicit) :
    """
        items are store like that:
        {<uid>:
            {<template>:quantity
            ,...}
        , ...
        }
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


    # def update(self, context, item) :
    #     if self.locked :
    #         raise CartLockedError
    #     assert isinstance(item, dict)
    #     keys = item.keys()
    #     keys.sort()
    #     assert keys == CART_ITEM_KEYS
    #
    #     pptool = getToolByName(context, 'portal_photo_print')
    #     uidh = getToolByName(context, 'portal_uidhandler')
    #
    #     uid = item['cmf_uid']
    #     template = item['printing_template']
    #     quantity = item['quantity']
    #
    #     photo = uidh.getObject(uid)
    #     pOptions = pptool.getPrintingOptionsContainerFor(photo)
    #     template = getattr(pOptions, template)
    #     templateId = template.getId()
    #     reference = template.productReference
    #
    #     currentQuantity = self._orders[uid][templateId]['quantity']
    #     delta = quantity - currentQuantity
    #     if template.maxCopies :
    #         counters = getattr(photo, COPIES_COUNTERS)
    #         if delta > 0 :
    #             already = counters[reference]
    #             if (already + delta) > template.maxCopies :
    #                 raise SoldOutError(template.maxCopies - already)
    #         counters[reference] += delta
    #
    #     self._orders[uid][templateId]['quantity'] += delta
    #
    # def remove(self, context, uid, templateId) :
    #     if self.locked :
    #         raise CartLockedError
    #     pptool = getToolByName(context, 'portal_photo_print')
    #     uidh = getToolByName(context, 'portal_uidhandler')
    #
    #     photo = uidh.getObject(uid)
    #     pOptions = pptool.getPrintingOptionsContainerFor(photo)
    #     template = getattr(pOptions, templateId)
    #     reference = template.productReference
    #
    #     quantity = self._orders[uid][templateId]['quantity']
    #     if template.maxCopies :
    #         counters = getattr(photo, COPIES_COUNTERS)
    #         counters[reference] -= quantity
    #
    #     del self._orders[uid][templateId]
    #     if not self._orders[uid] :
    #         del self._orders[uid]
    #         self._sequence_order = tuple([u for u in self._sequence_order if u != uid])

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
