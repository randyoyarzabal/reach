import pdb
import sys
import logging
from REOUtility import REOUtility


class REODelimitedFile(object):
    """
    This class is an abstraction of a delimited file and implements and iterator.
    Iterator automatically ignores white spaces as well as return a dict if headers
    are defined, or a list of values otherwise.
    """

    def __init__(self, file_src='', delimiter=",", has_header=False, logger=None):
        """
        Class constructor
        :param file_src: Source file
        :param delimiter: Delimiter character(s)
        :param has_header: True if headers exist, False otherwise
        """
        self.delimiter = delimiter
        """Delimiter character used. Default is a comma."""

        self.file_name = file_src
        """File path of delimited file"""

        self.infile = None
        """File handle for delimited file"""

        self.current_row = None
        """Current row (list of dict) being processed"""

        self.has_header = has_header
        """Header existence indicator flag"""

        self.row_count = 0
        """Number of rows in file"""

        self.header_list = None
        """Header row as a list"""

        self.logger = logger
        """Optional logger (from logging module) for this class """

        try:
            self.infile = open(self.file_name, 'r')
        except KeyboardInterrupt:
            REOUtility.key_interrupt()
        except:
            self.log(logging.ERROR, "Aborting...File: " + self.file_name + " not found.", True)
            sys.exit(1)

        if self.has_header:
            self.header_list = self.infile.next().split(self.delimiter)
            # Strip any leading/trailing spaces from headers
            self.header_list = [header.strip() for header in self.header_list]

        # Count hosts once right away
        self.row_count = 1 if not self.header_list else 0
        for i in self.infile:
            self.row_count += 1

    def __iter__(self):
        """
        Iterator over lines in the file
        :return: self instance
        """
        self.infile.seek(0)
        if self.header_list:
            self.infile.next()
        return self

    def __len__(self):
        """
        Return the number of rows
        :return: Number of rows
        """
        return self.row_count

    def next(self):
        """
        Get the next row in the file.
        :return:  If headers exist, a dict, a list otherwise.
        """
        # Move read head past blank lines and implicitly stops iteration when EOL is reached.
        rowdata = self.infile.next()
        while not rowdata.strip():
            rowdata = self.infile.next()

        # Strip any leading/trailing spaces from data fields
        host_values = [val.strip() for val in rowdata.split(self.delimiter)]

        if self.header_list:
            # Headers found return row as a dict
            self.current_row = dict(zip(self.header_list, host_values))
        else:
            # No headers found, return row as a list
            self.current_row = host_values
        return self.current_row

    def get_row_val(self, row=None, col_idx=0, name=''):
        """
        Get host row value by index or name
        :param row: Row being affected
        :param col_idx: index
        :param name: column name
        :return: row value
        """
        col_name = ''

        try:
            if name == '':
                col_name = self.header_list[col_idx]
            else:
                col_name = name
            if not row:
                row = self.current_row
        except:
            self.log(logging.ERROR, "Invalid file key column: \'" + col_name + "\' or column index: " + str(
                col_idx) + ". Check input file.", True)
            sys.exit(2)

        return row[col_name]

    def log(self, level, message, print_to_screen=False):
        """
        Logging mechanism if defined.
        :param print_to_screen: True to print message to screen as well
        :param level: Log level
        :param message: Message
        :return:
        """
        if print_to_screen:
            print message
        if self.logger:
            self.logger.log(level, message)

    def __del__(self):
        """
        Class destructor. Close the file.
        :return:
        """
        if self.infile:
            self.infile.close()
