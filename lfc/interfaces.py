# zope imports
from zope.interface import Interface


class IBaseContent(Interface):
    """
    Interface to mark BaseContent types.
    """
    pass

class IChildren(Interface):
    """
    Provides methods for children related methods.
    """
    pass

class ITabs(Interface):
    """
    Provides methods for tabs related methods.
    """
    def has_comments_tab():
        """Returns True if the comments tab should be displayed.
        """
        pass

    def has_seo_tab():
        """Returns True if the seo tab should be displayed.
        """
        pass
