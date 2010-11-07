""" photoprint exceptions



"""
from AccessControl import ModuleSecurityInfo

security = ModuleSecurityInfo('Products.photoprint.exceptions')

security.declarePublic('SoldOutError')
class SoldOutError(Exception):
	"Item is sold out"
	
	__allow_access_to_unprotected_subobjects__ = 1
	
	def __init__(self, n=0):
		self.n = n

security.declarePublic('CartLockedError')
class CartLockedError(Exception) :
	"Operation is not permitted due to cart lock"