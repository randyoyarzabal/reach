import base64
import datetime
import getpass
import json
import logging
import re
import socket
import subprocess
import traceback
from logging.handlers import RotatingFileHandler
import random
import string
import base64, hashlib
from Crypto import Random
from Crypto.Cipher import AES


class PasswordBlur:
    """
    Class for obfuscating passwords from clear-text to an encrypted string.
    Based on code from StackOverflow: https://stackoverflow.com/a/21928790
    """

    def __init__(self, cipher_key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(cipher_key.encode()).digest()

    def encrypt(self, clear_txt):
        clear_txt = self._pad(clear_txt)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        ret_val = base64.b64encode(iv + cipher.encrypt(clear_txt.encode()))
        return ret_val.decode('utf-8')

    def decrypt(self, blur_txt):
        blur_txt = base64.b64decode(blur_txt.encode('utf-8'))
        iv = blur_txt[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(blur_txt[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


class REOUtility:
    """
    This class is a collection of utility methods static and otherwise.
    """

    CIPHER_KEY = '#$a%9_(1fsa!@WxfjZU<><!@#$W^_;-!'

    def __init__(self, d=False):
        """
        Class constructor
        :param d: True to turn on debugging, False otherwise
        """

        self.debug = d
        """Debug flag"""

        self.last_command = None
        """Last command run using run_os_command()"""

        self.last_command_output = None
        """Last command output from using run_os_command()"""

        self.last_command_error = None
        """Last command error from using run_os_command()"""

        self.starttime = datetime.datetime.utcnow()
        """Start time recorded since this class was instantiated"""

        self.timer_start = self.starttime
        """Individual start time used for stop_timer() """

    def get_current_duration(self):
        """
        Return current duration since last get.
        :return: Duration
        """
        end_time = datetime.datetime.utcnow()
        return end_time - self.starttime

    def start_timer(self):
        """
        Set the start timer for later calculation
        :return: None
        """
        self.timer_start = datetime.datetime.utcnow()

    def stop_timer(self):
        """
        Stop the timer and return the duration since start time.
        :return: Duration
        """
        end_time = datetime.datetime.utcnow()
        return end_time - self.timer_start

    def get_last_command(self):
        """
        Get last system command run from run_os_command()
        :return: Last command string.
        """
        return self.last_command

    def get_last_command_output(self):
        """
        Get the last command's output.
        :return: Command output
        """
        return self.last_command_output

    def get_last_command_error(self):
        """
        Get the last command's error.
        :return: Command output
        """
        return self.last_command_error

    def toggle_debug(self, d):
        """
        Set the debug flag.
        :param d: Debug flag
        :return: None
        """
        self.debug = d

    def print_debug(self, s, desc=None):
        """
        Print formatted debug string
        :param s: String to print
        :param desc: Descriptive text about string to print
        :return: None
        """
        if self.debug:
            if desc:
                print(("[ DEBUG ] " + desc + ': ==>' + str(s) + '<=='))
            else:
                print(("[ DEBUG ] " + s))

    @classmethod
    def is_valid_ipv4_address(cls, address):
        """
        Check if address is a valid IPV4 IP address format
        :param address: IP address
        :return: True if valid, False otherwise
        """
        try:
            socket.inet_pton(socket.AF_INET, address)
        except KeyboardInterrupt:
            REOUtility.key_interrupt()
        except AttributeError:  # no inet_pton here, sorry
            try:
                socket.inet_aton(address)
            except KeyboardInterrupt:
                REOUtility.key_interrupt()
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error:  # not a valid address
            return False

        return True

    @classmethod
    def is_valid_ipv6_address(cls, address):
        """
        Check if address is a valid IPV6 IP address format
        :param address: IP address
        :return: True if valid, False otherwise
        """
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except KeyboardInterrupt:
            REOUtility.key_interrupt()
        except socket.error:  # not a valid address
            return False
        return True

    @classmethod
    def print_stack(cls):
        """
        Print the stack trace.
        :return: None
        """
        traceback.print_stack()

    @classmethod
    def key_interrupt(cls):
        """
        Display keyboard interrupt message
        :return: None
        """
        print("\n\nAw shucks, Ctrl-C detected. Exiting...\n")
        quit()

    def run_os_command(self, c):
        """
        Execute a system command
        :param c: Command to execute
        :return: Output of command
        """
        self.print_debug(c, 'Command')
        temp = subprocess.Popen([c], stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT, )
        (output, errput) = temp.communicate()
        temp.wait()
        self.print_debug(output, 'Output')
        self.last_command = c
        self.last_command_output = output.strip()
        if errput:
            self.last_command_error = errput.strip()
        return self.last_command_output

    @classmethod
    def is_number(cls, s):
        """
        Check if string is a valid number.
        :param s: String to check
        :return: True if is a number, False otherwise
        """
        return re.match(r"[-+]?\d+", s) is not None

    @classmethod
    def query_yes_no(cls, question, default=None):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        """ Code copied from:
        http://code.activestate.com/recipes/577058
        with minor modifications
        """

        valid = {"yes": True, "y": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("Invalid default answer: '%s'" % default)

        while True:
            print(question + prompt, end=' ')
            choice = input().lower()
            if default is not None and choice == '':
                print("")  # Display blank line
                return valid[default]
            elif choice in valid:
                print("")  # Display blank line
                return valid[choice]
            else:
                print("Please respond with 'yes' or 'no' (or 'y' or 'n')")

    @classmethod
    def encrypt_str(cls, i_str, cipher_key=None):
        """
        Change text to cipher text. Not meant to be secure but at least prevent opportunity
        theft of sensitive text such as passwords.
        :param i_str: String to encrypt
        :param cipher_key: Cipher to use
        :return: Encrypted string
        """
        if not cipher_key:
            cipher = REOUtility.CIPHER_KEY
        else:
            cipher = cipher_key

        pass_blur = PasswordBlur(cipher)
        return pass_blur.encrypt(i_str)

    @classmethod
    def decrypt_str(cls, e_str, cipher_key=None):
        """
        Decrypt string. Only works if strng was encrypted by this class
        :param e_str: Encrypted string
        :param cipher_key: Cipher to use
        :return: Decrypted string
        """
        if not cipher_key:
            cipher = REOUtility.CIPHER_KEY
        else:
            cipher = cipher_key

        pass_blur = PasswordBlur(cipher)
        return pass_blur.decrypt(e_str)

    @classmethod
    def escape_string(cls, e_str):
        """
        Escape special characters in string
        :param e_str: String to process
        :return: Escaped string
        """
        return json.dumps(e_str)

    @classmethod
    def ip_lookup(cls, fqdn):
        """
        Look-up IP address of a valid FQDN
        :param fqdn: Host to look-up
        :return: IP Address
        """
        ip = 'None'
        try:
            ip = socket.gethostbyname(fqdn)
        except:
            pass

        return ip

    @classmethod
    def fqdn_lookup(cls, ip):
        """
        Look-up FQDN given a valid IP
        :param ip: IP address to look-up
        :return: FQDN
        """
        fqdn = 'None'
        if REOUtility.is_valid_ipv4_address(ip):
            try:
                fqdn = socket.gethostbyaddr(ip)[0]
            except:
                pass

        return fqdn

    @classmethod
    def trim_quotes(cls, q_str):
        """
        This is primarily used for strings quoted in Excel.  If double quotes encountered, replace
        with one, and trim outer quotes.
        :param q_str: String to process
        :return: Processed string
        """
        retval = q_str
        double_quotes = "\"\""
        if double_quotes in q_str:
            retval = q_str.replace(double_quotes, '"')
            if retval.startswith('"'):
                retval = retval[1:]  # Remove first character
            if retval.endswith('"'):
                retval = retval[:-1]  # Remove last character
        return retval

    @classmethod
    def prompt_user_password(cls, user_prompt=True, password_prompt=True, desc=''):
        """
        Prompt for username and password.
        :return: None
        """
        username = ''
        password = ''
        if user_prompt:
            while not username:
                print(desc + " User Name: ", end=' ')
                username = input()

        if password_prompt:
            pwdprompt = lambda: (getpass.getpass(prompt=desc + ' Password: '), getpass.getpass('Retype password: '))

            p1, p2 = pwdprompt()
            while p1 != p2:
                print('Passwords do not match. Try again')
                p1, p2 = pwdprompt()
            password = p1

        return username, password

    @classmethod
    def get_logger(cls, log_file, level, module_info=False):
        """
        Get/create a logger instance.
        :param module_info: True to set the module info in the file, False otherwise
        :param log_file: Log file.
        :param level:  Logger level (verbosity)
        :return: Logger instance
        """
        if module_info:
            log_formatter = logging.Formatter("%(asctime)s,%(levelname)s,%(funcName)s(%(lineno)d),%(message)s",
                                              "%Y-%m-%d %H:%M:%S")
        else:
            log_formatter = logging.Formatter("%(asctime)s,%(levelname)s,%(message)s",
                                              "%Y-%m-%d %H:%M:%S")

        my_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024,
                                         backupCount=10, encoding=None, delay=0)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(level)
        app_log = logging.getLogger("logger")
        app_log.setLevel(level)
        app_log.addHandler(my_handler)
        return app_log

    @classmethod
    def get_string_from_file(cls, f):
        """
        Read a single line from file.
        :param f: Input file
        :return: None
        """
        infile = open(f, 'r')
        lines = infile.readlines()

        for line in lines:
            tpwd = line.strip()
            if not tpwd:
                continue
            else:
                break  # found the password

        infile.close()
        return tpwd

    @classmethod
    def get_parser_config(cls, section, parser):
        """
        Get a section from a config main_config
        :param section: Section header
        :param parser: Parser to get from
        :return: Dict contained in configuration section
        """
        dict1 = {}
        options = parser.options(section)
        for option in options:
            option = option.upper()
            try:
                dict1[option] = parser.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print(("exception on %s!" % option))
                dict1[option] = None
        return dict1
