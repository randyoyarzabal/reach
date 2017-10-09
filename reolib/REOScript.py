import os


class REOScript(object):
    """
    This class is a base class for all scripts using reolib.
    """

    SCRIPT_VERSION = '0.0'
    SCRIPT_DATE = ''
    SCRIPT_DESCRIPTION = ''
    SCRIPT_AUTHOR = 'Randy Oyarzabal, Francis Lan - http://reach.rbpsiu.com'
    SCRIPT_SYNTAX_OR_INFO = ''
    SCRIPT_USAGE = ''
    SCRIPT_NAME = ''
    SCRIPT_HELP = ''

    def __init__(self):
        """
        Class constructor.
        """
        pass

    def author(self, show_desc=False, show_help=False):
        """
        Print author information.
        :return: None
        """
        print (
            self.SCRIPT_NAME + " " + self.SCRIPT_VERSION + " (" + self.SCRIPT_DATE + ")\n"
            + self.SCRIPT_AUTHOR + "\n"
        )
        if show_desc:
            print (self.SCRIPT_DESCRIPTION)

        if show_help:
            print (self.SCRIPT_HELP)

    def usage(self):
        """
        Print usage information.
        :return: None
        """
        self.author(show_desc=True)
        print (self.SCRIPT_SYNTAX_OR_INFO)
        print (self.SCRIPT_USAGE)
