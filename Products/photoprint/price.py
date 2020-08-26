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
"""
Pricing types



"""

from Globals import Persistent
from AccessControl import ModuleSecurityInfo
from utils import Message as _
from utils import translate
from zope.globalrequest import getRequest

msecurity = ModuleSecurityInfo('Products.photoprint.price')
msecurity.declarePublic('Price')

class Price(object, Persistent) :
    """
    Price of an object which have VAT tax.
    """
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, taxedPrice, rate=0) :
        """price is initialized with taxed value"""
        self._rate = float(rate)
        self._setTaxed(taxedPrice)

    @property
    def rate(self):
        return self._localeStrNum(self._rate)

    def _setTaxed(self, value) :
        self._taxed = value
        self._price = value / (1 + self._rate)
    
    @property
    def taxed(self) :
        return self._localeStrNum(self._taxed)

    @property
    def value(self) :
        return self._localeStrNum(self._price)

    @property
    def tax(self) :
        tax = self._rate * self._price
        return self._localeStrNum(tax)

    @property
    def vat(self) :
        "returns vat rate in percent"
        vat = self._rate * 100
        return self._localeStrNum(vat)

    def _localeStrNum(self, n) :
        i = int(n)
        if i == n :
            return str(i)
        else :
            n = str(round(n, 2))
            i, d = n.split('.')
            ds = _(u'${i}.${d}', mapping={'i':i, 'd':d}, default=n)
            return  translate(ds).encode('utf-8')

    def getValues(self) :
        values = {'value':self._price,
                  'taxed': self._taxed,
                  'rate':self._rate}
        return values

    def __add__(self, other) :
        taxed = self._taxed + other._taxed
        value = self._price + other._price
        rate = (taxed - value ) / float(value)
        return Price(taxed, rate)

    def __div__(self, other) :
        return Price(self._taxed / other, self._rate)

    def __mul__(self, other) :
        return Price(self._taxed * other, self._rate)

    def __repr__(self):
        return '%s with VAT' % self.taxed
