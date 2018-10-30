#!/usr/bin/env python

import ConfigParser
import errno
import getopt
import os
import re
import sys

from reachlib import *
from reolib import *


class Reach(REOScript):
    """
    Main tool driver class.
    """

    def __init__(self):
        """
        Class constructor.
        """
        super(self.__class__, self).__init__()
        self.sshworker = None
        """Main worker instance"""

        self.util = REOUtility()
        """Utility instance"""

        self.logger = None
        """Optional logger (from logging module) instance"""

        self.main_config = ConfigParser.SafeConfigParser(allow_no_value=True)
        """Config main_config instance"""

        self.full_path = os.path.realpath(__file__)
        """Full path of running script"""

        self.dir_path = os.path.dirname(self.full_path)
        """Directory only of running script"""

        self.SCRIPT_NAME = os.path.basename(self.full_path)
        self.SCRIPT_VERSION = 'Pre-Release v1.0.4-dev (GitHub)'
        self.SCRIPT_DATE = '01-Nov-2018'
        self.SCRIPT_DESCRIPTION = "Automation tool for executing remote commands on multiple devices/hosts via SSH."
        self.SCRIPT_SYNTAX_OR_INFO = "Git Repository: https://github.com/randyoyarzabal/reach"
        self.SCRIPT_HELP = "Help/usage: reach.py -?"
        self.SCRIPT_USAGE = """
Synopsis:
    ./reach.py -?
    ./reach.py -v
    ./reach.py -a
    ./reach.py --cipher_text
    ./reach.py --host_fields
    ./reach.py -b commands_file [-x] [-d] ...
    ./reach.py -c command [-s search_string [-r report_string]] [-w wait_string -p response_string] ...

    Optionally, for any mode:
    ./reach.py [--config=<config_file>] [-i inventory_file] [-k column_key] [-x] [-d]

Help / Usage:
    -? : This help screen
    -v : Display version information only

Operation Modes:
    -a : Access Check only
    -b <commands file> : Run Batch Commands (comma separated file, see template for format/options)
    -c <command> : Run Command

Optional for Command (-c) Mode: 
    **Note that for Batch (-b) Mode, these are internally defined in the commands file.**
    -o : Show command console output (ignored in batch (-b option) mode)
    -u : Run command as root (run 'sudo su -' first), supports password-less sudo only
    -h : Halt looping through hosts when first done string (-s) is found
    -s <search_string> : Search string in output (For example: 'Complete' or 'Nothing|Complete|$NF')
       -r <report_string> : [Optional with same length as -s] Matching string to print to screen when -s match
          For example: 'Installed|Not Installed'
    -w <wait_string> : Wait string
       -p <response_string> : [Required with same length as -w] Send a string when -w string is found

Optional for all modes:
    --config=<config_file> Override the default config.ini (located in the configs directory)
    --username=<ssh_user> : Force user string instead of what is configured.
    --password=<ssh_cipher-text password> : Force cipher-text password instead of what is configured.
    --private_key=<ssh_rsa_key> : Force private RSA key file instead of what is configured.
    -i <inventory_file> : Inventory (hosts) file (comma separated, define header key with -k)
      -k <key_column> : [Required with -i] Column header of keys
    -f <filter> : Filter hosts to process. Operators are supported: = equal, ! not equal, | or, ~ contains, & and.
        Note: Reach does not support mixed (& and |) in this release yet.
        Example conditions: 'Build=WHC0122' , 'Build!WHC0122', 'Build=WHC0122&Host~app, 'Build=WHC0122|Host~app|Host~dom'
    -x : SIMULATION Mode (no connection/commands invoked)
    -d : DEBUG Mode

Special Variables or Markers:
    Variables/markers:
        $HF_# : Reference to the host file where # is the column number.
        $NF : Signal that the search string is not found in -s e.g. '-s search_string|$NF'
        $CT=<cipher text> : Used for sending passwords to the terminal like changing passwords or sending 
            Cisco ASA passwords in "enable" mode. Used in -p, or as host column data; can then be referenced 
            as $HF_# as described below ($HF_# support). 
            *See related option: --cipher_text option.*
   
    The following support $HF_#:
        Command-line options:
            -s, -r, -w, -p, --username=, --password=, --private_key=

        Configuration options:
            SSH_USER_NAME, SSH_PASSWORD_CIPHER, SSH_PRIVATE_KEY_FILE, HOST_DISPLAY_FORMAT

Special keystrokes for use in -p:
    ENTER_KEY : '\\n'
    RETURN_KEY : '\\r'
    TAB_KEY : '\\t'
    SPACE_KEY : ' '
    
Special modes:
    --cipher_text : generate cipher text from a password for use in SSH_PASSWORD_CIPHER or $CT=<cipher_text> (-p)
    --host_fields : return a list of column headers (with $HF_#) from the host file

Examples:
    - Run 'yum -y install gdb' as root, look for the strings: 'Nothing' or 'Complete', then display
        'Installed' or 'Not Installed' on the screen. Process hosts matching 'Build' column = 'WHC038'
    ./reach.py -c 'yum -y install gdb' -u -s 'Nothing|Complete' -r 'Installed|Not Installed' -f 'Build=WHC038'
              -------------------------------------------------------------------------------
    - Run 'sh ip route 10.143.92.134', look for the strings: 'bond0.' or 'bond0', then display
        'Found in: $HF_1' ($HF_1 is the first column of the inventory) or 'Not Here' then halt the hosts loop
    ./reach.py -c "sh ip route 10.143.92.134" -s 'bond0.|bond0' -r 'Found in: $HF_1|Not Here' -h
              -------------------------------------------------------------------------------
    - Check access against all hosts in the inventory file
    ./reach.py -a
              -------------------------------------------------------------------------------
    - Force read a different inventory file making sure to define the header key for the IP to use
    ./reach.py -i 'vga_inventory.csv' -a -k 'Public IP'
              -------------------------------------------------------------------------------
    - Run a series of commands defined in a file (see template for proper format)
    ./reach.py -b 'vga_backups.csv'
              -------------------------------------------------------------------------------
    - Change password for a user (run this in simulation mode for an explanation)
    ./reach.py -c 'passwd testuser' -w 'New|Retype' -p 'mypass3|mypass3' -s 'successfully' -r 'Changed password successfully!'
    Remember that -p supports $CT=<cipher text> to obfuscate the password. So it would be: -p '$CT=xxxxx|$CT=xxxxx'

Tips:
    - Always be sure to run in SIMULATION mode first to see what the script is about to do!
    - Use the -r option in conjunction with -s to substitute results, optionally use: grep and sed to limit output.
        Example: Search all hosts where 'vyatta' is found in the zones list. (Assumes you have access to all servers in file)
        ./reach.py -c 'show zone-policy zone' -s 'vyatta|$NF' -r 'yes|no' | grep -E 'yes|no' | sed -e 's/^[ \t-]*//'
           You may then paste the output as a new column in your inventory file.
        """

    def read_switches(self, argv):
        """
        Read command-line switches.
        :param argv: Argument list
        :return: None
        """
        opts = None
        try:
            opts, args = getopt.getopt(argv, 'ab:c:xdvof:i:k:uhs:w:p:r:?',
                                       ["config=", "username=", "password=", "private_key=", "cipher_text",
                                        "host_fields"])
        except KeyboardInterrupt:
            REOUtility.key_interrupt()
        except getopt.GetoptError as e:
            print "Invalid argument: %s" % str(e)
            self.author(show_help=True)
            sys.exit(2)
        if len(opts) == 0 or len(args) > 0:
            print "Invalid argument(s) combination passed."
            self.author(show_desc=True, show_help=True)
            sys.exit(2)

        for opt, arg in opts:
            # Optional switches
            if opt in BOOL_OPTS:
                set_cli_config(opt, True)
                user_opts[opt] = True
            if opt in STRING_OPTS:
                if SWITCH_KEYS[opt] == FILTER_STRING and FILTER_STRING in cli_config.keys():
                    concat_condition = cli_config[FILTER_STRING] + "&" + arg
                    set_cli_config(opt, concat_condition)
                    user_opts[opt] = concat_condition
                else:
                    set_cli_config(opt, arg)
                    user_opts[opt] = arg
            if opt in NUM_OPTS:
                set_cli_config(opt, float(arg))
                user_opts[opt] = float(arg)

    def check_prerequisites(self):
        """
        Check tool pre-conditions and raise an exception if a problem is found.
        :return: None
        """
        # Required switch, only allow one of these
        operations = [option for option in cli_config if option in EXCLUSIVE_OPTS]

        if len(operations) == 0:
            self.author(show_help=True)
            sys.exit(2)
        elif len(operations) > 1:
            raise ValueError("One of these options is required: " + str(EXCLUSIVE_OPTS_KEYS) + " (but only one!)")

        config[OPERATION] = operations[0]

        # Special operations
        if config[OPERATION] == SHOW_AUTHOR:
            self.author(show_desc=False, show_help=False)
            print 'Change History:\n'
            with open(self.dir_path + '/CHANGES.txt', 'r') as fin:
                print fin.read()
            sys.exit(2)

        if config[OPERATION] == SHOW_USAGE:
            self.usage()
            sys.exit(2)

        if config[OPERATION] == CIPHER:
            self.author()
            input_pass = REOUtility.prompt_user_password(user_prompt=False, desc="Convert to cipher text ==>")
            print ("\nWarning: this cipher text form is only useful in Reach.  It is by no means secure.\n"
                   "It is simply meant to conceal/obfuscate and prevent passwords from being displayed in clear-text.\n"
                   "It is useful in the SSH_PASSWORD_CIPHER config or as $CT=<cipher_text> with the -p option.\n")
            if config[CIPHER_KEY_FILE]:
                print "The cipher-key file: %s was used. " % config[CIPHER_KEY_FILE]
                cipher_key = REOUtility.get_string_from_file(config[CIPHER_KEY_FILE])
            else:
                print "Warning: using built-in cipher-key.  It is recommended to set 'CIPHER_KEY_FILE' config."
                cipher_key = REOUtility.CIPHER_KEY
            print "Note that decryption of the text below will only work with the cipher key it is encrypted with."
            print "\nCipher text: '" + REOUtility.encrypt_str(input_pass[1], cipher_key) + "'"
            sys.exit(0)

        if config[SSH_AGENT_ONLY]:
            if not config[SSH_USER_NAME]:
                raise ValueError("'SSH_USER_NAME' must be set if 'SSH_AGENT_ONLY' is True")

        # Forbidden opts when using -b
        if config[OPERATION] == OPERATION_BATCH:
            conflicting_opts = set(BAD_BATCH_OPTS) & set(cli_config.keys())
            conflicting_opts_keys = [SWITCH_VALUE[opt] for opt in conflicting_opts]
            if len(conflicting_opts) > 0:
                raise ValueError("Option(s) " + ", ".join(
                    conflicting_opts_keys) + " not allowed in batch (-b) mode! Specify the option in the commands file.")

        # Forbidden opts when using -a
        if config[OPERATION] == OPERATION_ACCESS:
            conflicting_opts = set(BAD_ACCESS_OPTS) & set(cli_config.keys())
            conflicting_opts_keys = [SWITCH_VALUE[opt] for opt in conflicting_opts]
            if len(conflicting_opts) > 0:
                raise ValueError("Option(s) " + ", ".join(
                    conflicting_opts_keys) + " not allowed in access (-a) mode!")

        # Check HOSTS_IMPUT_FILE
        if config[HOSTS_INVENTORY_FILE] == '':
            raise IOError("HOSTS_INPUT_FILE must be defined either in " +
                          config[CONFIG_FILE] + " or with option '" +
                          SWITCH_VALUE[HOSTS_INVENTORY_FILE] + "'.")

        # Files existence detection
        # CONFIG_FILE already checked
        if COLUMN_VARIABLE in config[SSH_PRIVATE_KEY_FILE]:
            keys_with_files = [BATCH_FILE, HOSTS_INVENTORY_FILE, CIPHER_KEY_FILE]
        else:
            keys_with_files = [BATCH_FILE, SSH_PRIVATE_KEY_FILE, HOSTS_INVENTORY_FILE, CIPHER_KEY_FILE]
        keys_with_files = [key for key in keys_with_files if config[key]]
        for file_key in keys_with_files:
            if not os.path.isfile(config[file_key]):
                raise IOError(config[file_key] + " doesn't exist.")

        # -k must be used with -i
        if HOSTS_INVENTORY_FILE in cli_config.keys():
            if IP_OR_HOST_COLUMN not in cli_config.keys():
                raise ValueError("'" + SWITCH_VALUE[HOSTS_INVENTORY_FILE] + "' can only be used in conjunction with '" +
                                 SWITCH_VALUE[IP_OR_HOST_COLUMN] + "'.")
        # Check hosts file
        hosts_file = REODelimitedFile(config[HOSTS_INVENTORY_FILE], has_header=True)
        max_column = len(hosts_file.header_list)
        if config[IP_OR_HOST_COLUMN] not in hosts_file.header_list:
            raise ValueError("Column '" + config[IP_OR_HOST_COLUMN] + "' cannot be found in hosts file.")
        if config[FILTER_STRING]:
            if STRINGS_MULTI_CONDITION in config[FILTER_STRING] and STRINGS_DELIMITER in config[FILTER_STRING]:
                raise ValueError(
                    "Filter cannot contain both '" + STRINGS_MULTI_CONDITION + "' and '" + STRINGS_DELIMITER + "'")
            conditions = re.split("[" + STRINGS_MULTI_CONDITION + STRINGS_DELIMITER + "]",
                                  config[FILTER_STRING])
            conditions = [{'cond': cond, 'splits': re.split("[~=!]", cond)} for cond in conditions]
            for cond in conditions:
                if len(cond['splits']) != 2:
                    raise ValueError(
                        "Filter '" + cond['cond'] + "' invalid, please specify '~', '=', or '!' for each filter.")
                if cond['splits'][0] not in hosts_file.header_list:
                    raise ValueError("Column '" + cond['splits'][0] + "' cannot be found in hosts file.")

        del hosts_file

        # List of commands read from file
        commands = []

        # This if/elif statement creates the commands array that will contain
        # the list of commands to be executed. Then each command will be
        # checked for validity
        if config[OPERATION] == OPERATION_BATCH:
            commands_file = REODelimitedFile(config[BATCH_FILE])
            row = 0
            for command in commands_file:
                row += 1
                if row == 1:
                    continue
                temp = {}
                for i in range(len(command)):
                    temp[BATCH_COMMANDS_COLUMN_ORDER[i]] = command[i]
                commands.append(temp)
            del commands_file
        elif config[OPERATION] == OPERATION_COMMAND:
            temp = {}
            for var_name in BATCH_COMMANDS_COLUMN_ORDER:
                temp[var_name] = str(config[var_name]).strip() if var_name in config else ''
            commands.append(temp)

        # Check whether each command is valid
        for command in commands:
            if command[COMMAND_STRING] == '':
                raise ValueError("Command cannot be empty.")
            if command[SHOW_CONSOLE_OUTPUT].lower() not in VALID_YES_NO:
                raise ValueError("'" + SWITCH_VALUE[
                    SHOW_CONSOLE_OUTPUT] + "' must be 'yes', 'no' or be left empty (meaning no).")
            if command[LOCAL_COMMAND].lower() not in VALID_YES_NO:
                raise ValueError(
                    "'" + SWITCH_VALUE[LOCAL_COMMAND] + "' must be 'yes', 'no' or be left empty (meaning no).")
            if command[HALT_ON_STRING].lower() not in VALID_YES_NO:
                raise ValueError(
                    "'" + SWITCH_VALUE[HALT_ON_STRING] + "' must be 'yes', 'no' or be left empty (meaning no).")

            temp = {}
            temp[COMMAND_WAIT_STRING] = len(command[COMMAND_WAIT_STRING].split(STRINGS_DELIMITER)) if command[
                                                                                                          COMMAND_WAIT_STRING] != '' else 0
            temp[COMMAND_SEND_STRING] = len(command[COMMAND_SEND_STRING].split(STRINGS_DELIMITER)) if command[
                                                                                                          COMMAND_SEND_STRING] != '' else 0
            temp[COMMAND_FIND_STRING] = len(command[COMMAND_FIND_STRING].split(STRINGS_DELIMITER)) if command[
                                                                                                          COMMAND_FIND_STRING] != '' else 0
            temp[COMMAND_REPORT_STRING] = len(command[COMMAND_REPORT_STRING].split(STRINGS_DELIMITER)) if command[
                                                                                                              COMMAND_REPORT_STRING] != '' else 0
            if temp[COMMAND_WAIT_STRING] != temp[COMMAND_SEND_STRING]:
                raise ValueError("Option '" + SWITCH_VALUE[
                    COMMAND_SEND_STRING] + "' must be used in conjunction with option '" +
                                 SWITCH_VALUE[COMMAND_WAIT_STRING] + "' with the same length.")
            if temp[COMMAND_REPORT_STRING] > 0 and temp[COMMAND_FIND_STRING] == 0:
                raise ValueError("Option '" + SWITCH_VALUE[
                    COMMAND_REPORT_STRING] + "' cannot be used without option '" +
                                 SWITCH_VALUE[COMMAND_FIND_STRING] + "'.")
            if temp[COMMAND_REPORT_STRING] > 0 and (temp[COMMAND_FIND_STRING] != temp[COMMAND_REPORT_STRING]):
                raise ValueError("When option '" + SWITCH_VALUE[
                    COMMAND_REPORT_STRING] + "' is used in conjunction with option '" +
                                 SWITCH_VALUE[COMMAND_FIND_STRING] + "', they must have the same length.")
            if command[HALT_ON_STRING].lower() in ['yes', 'true'] and command[COMMAND_FIND_STRING] == '':
                raise ValueError(
                    "Option '" + SWITCH_VALUE[HALT_ON_STRING] + "' must be used in conjunction with option '" +
                    SWITCH_VALUE[COMMAND_FIND_STRING] + "'.")

            command_raw = ','.join(command.values())
            hvars = re.findall(re.escape(COLUMN_VARIABLE) + '\d*', command_raw)
            for hvar in hvars:
                if int(hvar.split("_")[1]) > max_column:
                    raise ValueError(
                        "Host File Column variable '" + hvar + "' must be between 1 and " + str(max_column) + ".")

    def run_util(self, argv):
        """
        Main driver method.
        :param argv: Argument list
        :return: None
        """
        # Read switches first, into temp dict and get the config file if any
        self.read_switches(argv)

        # Read our current path
        config[CONFIG_FILE] = self.dir_path + "/" + config[CONFIG_FILE]

        # Parse config file as defaults
        config_file = cli_config[CONFIG_FILE] if (CONFIG_FILE in cli_config) else config[CONFIG_FILE]

        if not os.path.isfile(config_file):
            print("Aborted...Config File defined: " + config_file + " doesn't exist.")
            sys.exit(1)

        # Override system defaults with user defaults
        self.main_config.read(config_file)
        config_defaults = REOUtility.get_parser_config(CONFIG_SECTION, self.main_config)
        for conf in config_defaults:
            if conf in STRING_DEFAULTS:

                defaults[conf] = self.main_config.get(CONFIG_SECTION, conf)

            elif conf in BOOLEAN_DEFAULTS:
                defaults[conf] = self.main_config.getboolean(CONFIG_SECTION, conf)

            elif conf in NUMBER_DEFAULTS:
                defaults[conf] = self.main_config.getfloat(CONFIG_SECTION, conf)

        # Prepend our current dir to default log directory if not defined by user
        if LOGS_DIRECTORY not in config_defaults:
            defaults[LOGS_DIRECTORY] = self.dir_path + "/" + defaults[LOGS_DIRECTORY]

        # Apply system defaults
        set_defaults()

        # Apply command line switches
        set_cli_to_config()

        # Set a slash if not already there
        if not config[LOGS_DIRECTORY].endswith('/'):
            config[LOGS_DIRECTORY] += '/'

        # Create logs directory if non existent
        if not os.path.isdir(config[LOGS_DIRECTORY]):
            try:
                os.makedirs(os.path.dirname(config[LOGS_DIRECTORY]))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    print "Unable to create log directory defined: " + config[LOGS_DIRECTORY]
                    sys.exit(1)

        # Set logging file and level
        self.logger = REOUtility.get_logger(config[LOGS_DIRECTORY] + config[LOG_FILE],
                                            LOG_LEVELS[config[LOG_LEVEL]])
        self.util.toggle_debug(config[DEBUG_FLAG])

        self.log(logging.INFO, "Reach Process Started", False)

        try:
            self.check_prerequisites()

        except Exception as error:
            print("Aborted..." + error.message)
            print "Use: 'reach.py -?' for usage/help."
            sys.exit(1)

        self.author()

        if config[OPERATION] == OPERATION_ACCESS:
            print ("== | Operation: Access Check" + self.get_simulation_str() + " | ==\n")
            self.log(logging.INFO, "Access Mode Started", False)
            self.sshworker = CheckAccessWorker(logger=self.logger)
            self.sshworker.SHOW_HOST_DURATION = False  # Force to false, this is never needed in this mode
        if config[OPERATION] == OPERATION_BATCH:
            print ("== | Operation: Run Batch Commands from File" + self.get_simulation_str() + " | ==\n")
            self.sshworker = RunBatchCommandsWorker(config[BATCH_FILE], logger=self.logger)
            self.log(logging.INFO, "Batch Mode Started", False)
            self.log(logging.INFO, "Processing batch file: " + config[BATCH_FILE], False)
        if config[OPERATION] == OPERATION_COMMAND:
            print ("== | Operation: Run Command" + self.get_simulation_str() + " | ==\n")
            self.log(logging.INFO, "Command Mode Started", False)
            self.sshworker = RunCommandWorker(logger=self.logger)
            self.sshworker.str_vars_exist = check_for_vars()
        if config[OPERATION] == HOST_FIELDS:
            self.sshworker = CheckAccessWorker(logger=self.logger)
            print ("This is a list of the available column names in " + config[HOSTS_INVENTORY_FILE] + " along with \n"
                                                                                                       "  the corresponding $HF_# that can be used as command-line options or in the config.\n")
            self.sshworker.display_host_fields()
            sys.exit(0)

        # Process hosts
        self.sshworker.hosts_worker()  # Loop through hosts

        self.log(logging.INFO, "Reach Process Ended", False)

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
        if self.util.debug and level == logging.DEBUG:
            self.util.print_debug(message)
        if self.logger:
            self.logger.log(level, message)

    @classmethod
    def get_simulation_str(cls):
        return ' - SIMULATION MODE ONLY' if config[SIMULATION_MODE] else ''


def main(argv):
    myscript = Reach()
    myscript.run_util(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
