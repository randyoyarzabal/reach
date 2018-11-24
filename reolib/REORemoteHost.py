import logging
import os
import re
import time

import paramiko
from paramiko.ssh_exception import *

from .REOUtility import REOUtility


class REORemoteHost(object):
    """
    This class is wrapper for remote hosts currently implemented using paramiko for SSH
    which could in the future implemented as any type of host, SSH, telnet etc.
    """
    SERVER_STATUS_NO_ACCESS = 'Authentication failed. Check user/pass or key/passphrase.'
    SERVER_STATUS_UNKNOWN_HOST = 'Not in known_hosts. Connect manually first, or set SSH_TRUST_HOSTS = True.'
    SERVER_STATUS_HOST_CHANGED = 'Host key changed. Connect manually first, or set SSH_TRUST_HOSTS = True.'
    SERVER_STATUS_UNABLE_TO_REACH = 'Unable to reach server. Check IP/Hostname, logs or Debug (-d)'
    SERVER_STATUS_SSH_ERROR = 'Unknown SSH error occurred. Check the logs.'
    SERVER_STATUS_SSH_BLOCKED = 'SSH connection to server may be blocked.'
    SERVER_STATUS_SSH_KEY_MISSING = 'Missing private key file.'
    SERVER_STATUS_CONNECTED = 'Connected'
    SERVER_STATUS_ERROR_PROMPT = 'Unable to detect initial prompt'
    STRINGS_DELIMITER = '|'
    NOT_FOUND_MARKER = '$NF'
    DEFAULT_PROMPT_REGEX = '[$#>]( )?$'
    DEFAULT_NEW_PROMPT_REGEX = '\[REACH\]# $'
    DEFAULT_NEW_PROMPT = '[REACH]# '
    PROMPT_DETECTION_TIMEOUT = 10
    PROMPT_SET_TIMEOUT = 5

    # Key markers
    ENTER_KEY = '$ENTER_KEY'
    RETURN_KEY = '$RETURN_KEY'
    TAB_KEY = '$TAB_KEY'
    SPACE_KEY = '$SPACE_KEY'
    CIPHER_TEXT_MARKER = '$CT='

    KEY_STROKE = {ENTER_KEY: '\n', RETURN_KEY: '\r', TAB_KEY: '\t', SPACE_KEY: ' '}
    """Dictionary of key strokes and their corresponding real character(s)"""

    KEY_STROKE_DISPLAY = {ENTER_KEY: '<ENTER KEY>', RETURN_KEY: '<RETURN KEY>', TAB_KEY: '<TAB KEY>',
                          SPACE_KEY: '<SPACE KEY>'}
    """Dictionary of key strokes and their corresponding screen display text"""

    def __init__(self, host, prompt_regex=DEFAULT_PROMPT_REGEX, new_prompt_regex=DEFAULT_NEW_PROMPT_REGEX,
                 new_prompt=DEFAULT_NEW_PROMPT, usr=None, pwd=None, logger=None):
        """
        Class constructor
        :param host: IP address of host
        :param usr: User name
        :param pwd: Password
        """
        self.host = host
        """IP Address or Hostname"""

        self.usr = usr
        """User Name"""

        self.pwd = pwd
        """Password"""

        self.client = None
        """Virtual SSH client connection"""

        self.util = REOUtility()
        """Utility instance"""

        self.cipher_key = None
        """Cipher key used for encrypt/decrypt of host password and $CT= values"""

        self.connect_status_string = ''
        """Connection status string"""

        self.key_file = None
        """RSA private key file"""

        self.shell = None
        """Virtual shell session"""

        self.connected = False
        """Connection flag"""

        self.console_output_buffer = ''
        """String container of console output buffer being processed"""

        self.search_string_isfound = ''
        """Search string found flag"""

        self.cmd_timeout = 0
        """SSH command timeout value"""

        self.str_vars_exist = False
        """String variable existence flag"""

        self.ssh_lib_log = ''
        """Paramiko logger instance"""

        self.logger = logger
        """Optional logger (from logging module) for this class"""

        self.original_prompt_regex = prompt_regex
        """Regex of the initial prompt at login"""

        self.new_prompt_regex = new_prompt_regex
        """Regex of the personalized prompt to be set"""

        self.new_prompt = new_prompt
        """Personalized prompt to be set"""

        self.expected_prompt_regex = prompt_regex
        """Regex of the prompt used to detect command completion"""

    def connect_host(self, set_prompt=True, u=None, p=None, f=None, conn_timeout=10, cmd_timeout=5, trust_hosts=False,
                     agent_only=False):
        """
        Establish connection with host
        :param set_prompt: Set a personalized prompt
        :param u: User name
        :param p: Password
        :param f: File containing password
        :param conn_timeout: Connection time-out
        :param cmd_timeout: Command time-out
        :param trust_hosts: True to blindly trust hosts, False to use system known_hosts
        :return: True if successfully connected, False otherwise
        """
        self.connected = False
        if self.util.debug:
            print(' ')
        self.log(logging.DEBUG, "Connecting to: " + self.host, False)
        if u: self.usr = u
        if f: self.key_file = f
        if p: self.pwd = p

        self.cmd_timeout = cmd_timeout
        self.client = paramiko.SSHClient()

        if trust_hosts:
            # Blindly trust hosts
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            # Load system "known_hosts" file
            self.client.load_system_host_keys()

        paramiko.util.log_to_file(self.ssh_lib_log)

        self.log(logging.DEBUG, "CONNECTION_TIMEOUT " + str(conn_timeout), False)

        self.log(logging.DEBUG, "COMMAND_TIMEOUT " + str(cmd_timeout), False)

        self.log(logging.DEBUG, "User Name: " + self.usr, False)

        # Try agent authentication
        self.connected = self.__connect("Trying agent authentication.", self.host, self.usr, timeout=conn_timeout,
                                        allow_agent=True, look_for_keys=True)

        if not agent_only:

            # Try user-defined private-key authentication
            if not self.connected:
                self.connected = self.__connect("Trying private key file: " + self.key_file, self.host, self.usr,
                                                timeout=conn_timeout, private_key_file=self.key_file, password=self.pwd,
                                                allow_agent=False, look_for_keys=False)

            # Try user/password authentication
            if not self.connected:
                self.connected = self.__connect("Trying user('%s')/password(********): " % self.usr, self.host,
                                                self.usr, password=self.pwd, timeout=conn_timeout,
                                                allow_agent=False, look_for_keys=False)

        if self.connected:
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(cmd_timeout)
            self.connect_status_string = self.SERVER_STATUS_CONNECTED
            if not self.detect_initial_prompt():
                self.connect_status_string = self.SERVER_STATUS_ERROR_PROMPT
                self.log(logging.DEBUG, self.connect_status_string, False)
                return False
            if set_prompt:
                # Variable output not used, but may be in the future
                prompt_set, output = self.set_prompt()
                if not prompt_set:
                    # Continue with old prompt for now and not fail
                    self.connect_status_string = self.SERVER_STATUS_CONNECTED
            self.log(logging.DEBUG, self.connect_status_string, False)

        return self.connected

    def __connect(self, msg, host, username, password=None, timeout=5, private_key_file=None, allow_agent=False,
                  look_for_keys=False):
        """
        Helper method to facilitate various authentication methods and handling exceptions accordingly.
        :param msg: message to display to screen
        :param host: host or ip
        :param username:
        :param password:
        :param timeout: connection timeout
        :param private_key_file: location of private key
        :param allow_agent:
        :param look_for_keys:
        :return: True if successfully connected, False otherwise.
        """
        connected = False
        try:
            self.log(logging.DEBUG, msg, False)
            if private_key_file:
                try:
                    self.log(logging.DEBUG, "Decrypting private key...", False)
                    if not os.path.isfile(private_key_file):
                        raise AuthenticationException(self.SERVER_STATUS_SSH_KEY_MISSING)
                    private_key = paramiko.RSAKey.from_private_key_file(filename=private_key_file, password=password)
                    self.client.connect(host, username=username, timeout=timeout, pkey=private_key,
                                        allow_agent=allow_agent, look_for_keys=look_for_keys)
                    connected = True
                except Exception as e:
                    raise AuthenticationException(e)
            if not connected:
                self.client.connect(host, username=username, password=password, timeout=timeout,
                                    allow_agent=allow_agent, look_for_keys=look_for_keys)
            self.log(logging.DEBUG, "Success", False)
            connected = True
            return connected
        except KeyboardInterrupt:
            self.util.key_interrupt()
        except BadHostKeyException as e:
            self.connect_status_string = self.SERVER_STATUS_HOST_CHANGED
            self.log(logging.DEBUG, self.connect_status_string, False)
        except AuthenticationException as e:
            err_str = str(e)
            if self.SERVER_STATUS_SSH_KEY_MISSING in err_str:
                self.connect_status_string = self.SERVER_STATUS_SSH_KEY_MISSING
            else:
                self.connect_status_string = self.SERVER_STATUS_NO_ACCESS
                self.log(logging.DEBUG, self.connect_status_string, False)
            self.log(logging.DEBUG, err_str, False)
        except SSHException as e:
            err_str = str(e)
            if 'known_hosts' in err_str:
                self.connect_status_string = self.SERVER_STATUS_UNKNOWN_HOST
            elif 'No existing session' in err_str:
                self.connect_status_string = self.SERVER_STATUS_SSH_BLOCKED
            else:
                self.connect_status_string = err_str
            self.log(logging.DEBUG, self.connect_status_string, False)
        except Exception as e:
            self.connect_status_string = self.SERVER_STATUS_UNABLE_TO_REACH
            self.log(logging.DEBUG, self.connect_status_string, False)
            self.log(logging.DEBUG, str(e), False)

    def set_password_from_file(self, f):
        """
        Read and set the password from a file.
        :param f: Password file
        :return: None
        """
        infile = open(f, 'r')
        lines = infile.readlines()

        for line in lines:
            tpwd = line.strip()
            if not tpwd:
                continue
            else:
                self.pwd = tpwd
                break  # found the password

        infile.close()

    def detect_initial_prompt(self):
        """
        Detect initial prompt
        :return: True/False for success/failure
        """
        self.log(logging.DEBUG, "Detect initial prompt start", False)
        self.shell.settimeout(self.PROMPT_DETECTION_TIMEOUT)
        match = None
        output = ''
        while match is None:
            try:
                output += self.shell.recv(1024).decode("utf-8")
                match = re.search(self.original_prompt_regex, output)
            except KeyboardInterrupt:
                self.util.key_interrupt()
            except socket.timeout:
                self.shell.settimeout(self.cmd_timeout)
                return False
            except:
                return False
                # self.util.print_stack()
        self.shell.settimeout(self.cmd_timeout)
        self.log(logging.DEBUG, "Detect initial prompt success", False)
        return True

    def set_prompt(self):
        """
        Try to set the prompt to a personalized one.
        :return: True/False for success/failure, output
        """
        self.log(logging.DEBUG, "Set prompt start", False)
        # Setting the timeout for the shell to a lower value for this function only
        self.shell.settimeout(self.PROMPT_SET_TIMEOUT)
        self.shell.send("PS1=$PS1'" + self.new_prompt + "'\n")  # In case of sh-style
        output = ''
        matches = []
        while len(matches) != 2:
            try:
                output += str(self.shell.recv(2048))
                matches = re.findall(self.new_prompt_regex[:-1], output)
            except KeyboardInterrupt:
                self.util.key_interrupt()
            except socket.timeout:
                self.shell.settimeout(self.cmd_timeout)
                self.expected_prompt_regex = self.original_prompt_regex
                return False, output
            except:
                self.util.print_stack()
        self.shell.settimeout(self.cmd_timeout)
        self.expected_prompt_regex = self.new_prompt_regex
        self.log(logging.DEBUG, "Set prompt success", False)

        return True, output

    def send_cmd_wait_respond(self, command, search_string='', wait_string='', response_string='', last_run_log=None):
        """
        This method will send a command to the server and search for a "search" string.
        It can optionally, wait for subsequent strings and send a response string.
        :param last_run_log: Log file for results of the last run
        :param command: Command to send
        :param search_string: Search string(s)
        :param wait_string: String(s) to expect
        :param response_string: String(s) to use as a response for wait_strings
        :param cipher_key: 32 character cipher string for decrypting any $CT= values
        :return: Output of command, error_msg (or '')
        """
        # Check for wait conditions
        will_wait_respond = False
        wait_response_pair = {}
        search_strings = None
        wait_strings = None
        response_strings = None
        response_display = None
        search_strings_display = None
        self.console_output_buffer = ''
        self.search_string_isfound = ''

        if search_string:
            search_strings = search_string.split(self.STRINGS_DELIMITER)

            # Remove not found marker from search_strings list
            if self.NOT_FOUND_MARKER in search_strings:
                search_strings.remove(self.NOT_FOUND_MARKER)

            search_strings_display = '\'' + "\' or \'".join(search_strings) + '\''

            if self.str_vars_exist:
                print(("  - Waiting for string(s): " + search_strings_display))

        if wait_string:
            wait_strings = wait_string.split(self.STRINGS_DELIMITER)
            wait_strings_display = '\'' + "\',\'".join(wait_strings) + '\''
            self.log(logging.DEBUG, "Wait String: " + wait_string, False)
            if self.str_vars_exist:
                print(("    - Waiting for string(s) in sequence: " + wait_strings_display))

            if response_string:
                response_strings = response_string.split(self.STRINGS_DELIMITER)
                # Replace key stroke markers with real chars and create a display-only list
                response_display = response_strings[:]  # Create a copy of the response list
                for i, rs in enumerate(response_strings):
                    for key in self.KEY_STROKE:
                        response_strings[i] = response_strings[i].replace(key, self.KEY_STROKE[key])
                        response_display[i] = response_display[i].replace(key, self.KEY_STROKE_DISPLAY[key])

                    # Allow sending password in cipher text (Format: $CT=<cipher text>),
                    # useful for sudo requiring passwords or Cisco ASA 'enable' passwords
                    cipher_text = re.search(re.escape(self.CIPHER_TEXT_MARKER) + '([^|]*)', rs)
                    if cipher_text is not None:
                        response_strings[i] = response_strings[i].replace(cipher_text.group(0),
                                                                          REOUtility.decrypt_str(cipher_text.group(1),
                                                                                                 self.cipher_key))
                        response_display[i] = response_display[i].replace(cipher_text.group(0), '**********')
            wait_response_pair = list(zip(wait_strings, response_strings, response_display))
            if len(wait_response_pair) > 0:
                will_wait_respond = True

        # Send the command to the host
        self.shell.send(command + "\n")

        command_completed = False
        error_msg = ''
        output_last = ''
        buffer_index = 0
        if self.__detect_special_commands(command):
            self.expected_prompt_regex = self.original_prompt_regex
        if self.__detect_sudo(command):
            self.expected_prompt_regex = self.original_prompt_regex

        while not command_completed:
            # Continuously read output lines until wait strings are found or timeout reached
            try:
                self.log(logging.DEBUG, "Expected prompt regex: " + self.expected_prompt_regex, False)
                self.console_output_buffer += self.shell.recv(1024).decode("utf-8")
                if buffer_index == 0:
                    temp = self.console_output_buffer.replace(' \r', '').split(command, 1)
                    if len(temp) < 2:
                        continue
                    output_last = temp[1]
                else:
                    output_last = self.console_output_buffer[buffer_index:]
                command_completed = (re.search(self.expected_prompt_regex, output_last) is not None)
                if command_completed:
                    break

            except KeyboardInterrupt:
                self.util.key_interrupt()
            except socket.timeout:
                self.util.print_debug("Timeout, console_output_buffer: " +
                                      self.console_output_buffer)
                if will_wait_respond:
                    # If wait_strings not all consumed and the shell timed out,
                    # it may mean that the wait strings are incorrect
                    print(("  - Wait string(s) not found and command timeout. Timeout value: " + str(self.cmd_timeout)))
                    last_run_log.write("Not Found\n")
                self.log(logging.ERROR, 'Command timeout. No more commands will be sent to this host.', False)
                error_msg = 'Command timeout. No more commands will be sent to this host.'
                break

            # command not completed, check for wait strings
            if will_wait_respond:
                # Look for wait_string keywords in the output and send response
                for (wait, response, response_display) in wait_response_pair:
                    self.log(logging.DEBUG, "Looking for wait key: " + wait, False)
                    if wait in output_last:
                        # Check if wait is a special key stroke character(s)
                        key_stroke_isfound = True in [self.KEY_STROKE[ks] in response for ks in self.KEY_STROKE]

                        # This is stripping the space when sending
                        # $SPACE_KEY (or any other special char keystroke)
                        if key_stroke_isfound:
                            rstring = response
                        else:
                            rstring = response.strip()

                        self.log(logging.DEBUG, "Found wait key: " + wait, False)
                        print(("    - Found \'" + wait + "\'"))
                        self.log(logging.DEBUG, "Sending response: " + rstring, False)
                        print(("    - Sent response \'" + response_display + "\'"))

                        if key_stroke_isfound:
                            self.shell.send(rstring)
                        else:
                            self.shell.send(rstring + "\n")

                        wait_response_pair.remove((wait, response, response_display))
                        buffer_index = len(self.console_output_buffer)
                        break  # Found a match in output

        # end of while not command_completed

        if search_strings:
            # Look for search strings
            for search_key in search_strings:
                if search_key == self.NOT_FOUND_MARKER: continue  # Ignore "not found" marker
                self.log(logging.DEBUG, "Looking for search key: " + search_key, False)
                self.util.print_debug("Current output: " + self.console_output_buffer)
                if search_key in self.console_output_buffer.replace(' \r', '').split(command, 1)[1]:
                    self.log(logging.DEBUG, "Found search key: " + search_key, False)
                    self.search_string_isfound = search_key
                    break
            else:  # if for loop terminates without breaking (ie, no search_string found)
                if self.NOT_FOUND_MARKER not in search_string:
                    print(("  - Search string(s) " + search_strings_display + " not found."))
                    last_run_log.write("Not Found: " + search_strings_display + "\n")
                if self.NOT_FOUND_MARKER in search_string:
                    self.search_string_isfound = self.NOT_FOUND_MARKER
                else:
                    self.search_string_isfound = ''  # Exited on timeout, not a wait keyword
        if len(wait_response_pair) > 0:
            keys_not_found = ", ".join(
                ["'" + pair[0] + "'" for pair in wait_response_pair if pair[0] not in self.console_output_buffer])
            keys_found = ", ".join(
                ["'" + pair[0] + "'" for pair in wait_response_pair if pair[0] in self.console_output_buffer])
            if keys_not_found != '':
                self.log(logging.DEBUG, "Wait keys not found: " + keys_not_found, False)
                print(("  - Wait strings not found: " + keys_not_found + ""))
            if keys_found != '':
                self.log(logging.DEBUG,
                         "Wait keys found but response not sent because prompt immediately returned: " + keys_found,
                         False)
                print((
                        "  - Wait strings found but response not sent because prompt immediately returned: " + keys_found + ""))

        if self.__detect_sudo(command):
            prompt_set, output = self.set_prompt()
            # self.console_buffer += output
            if not prompt_set:
                # error_msg = "Unable to set personalized prompt in su mode"
                pass

        self.util.print_debug("Output:\n" + self.console_output_buffer.replace(' \r', ''))

        return re.sub(self.new_prompt_regex, '', self.console_output_buffer).replace(' \r', ''), error_msg

    def __detect_special_commands(self, command):
        """
        Detect if a special command is used
        :param command: Command to test
        """
        # TODO: Better detect special commands (use devices.ini)
        return re.match('conf$', command) is not None

    def __detect_sudo(self, command):
        """
        Detect if command is using sudo
        :param command: Command to test
        :return: True if command contains sudo, False otherwise
        """
        # TODO: Better detect sudo root equivalent commands
        return re.match('(sudo (root|su).*)$', command) is not None

    def log(self, level, message, print_to_screen=False):
        """
        Logging mechanism if defined.
        :param print_to_screen: True to print message to screen as well
        :param level: Log level
        :param message: Message
        :return:
        """
        if print_to_screen:
            print(message)
        if self.util.debug and level == logging.DEBUG:
            self.util.print_debug(message)
        if self.logger:
            self.logger.log(level, message)

    def close(self):
        """
        Close the connection to host if open.
        :return: None
        """
        if self.connected:
            self.connected = False
            self.client.close()

    def __del__(self):
        """
        Class destructor. Close the connection.
        :return:
        """
        closed = False
        if self.connected:
            self.client.close()
            closed = True
        if closed:
            self.log(logging.DEBUG, 'Connection to ' + self.host + ' closed', False)
