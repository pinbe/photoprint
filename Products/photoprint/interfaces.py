from zope.interface import Interface, Attribute


class IPrintOffer(Interface):
    """
    Print offer description
    """

    data = Attribute(""" JSON data""")


class IPhotoPrintTool(Interface) :
    """
    PhotoPrintTool interface
    """