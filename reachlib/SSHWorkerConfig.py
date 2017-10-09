import collections
import logging
import pdb

# Configuration Keys
ACCESS_CHECK = 'ACCESS_CHECK'
CONFIG_SECTION = 'TOOL DEFAULTS'
COMMANDS_FILE = 'COMMANDS_FILE'
COMMAND_STRING = 'COMMAND_STRING'
LOCAL_COMMAND = 'LOCAL_COMMAND'
RUN_SUDO_FIRST = 'RUN_SUDO_FIRST'
HALT_ON_STRING = 'HALT_ON_STRING'
COMMAND_SEARCH_STRING = 'COMMAND_SEARCH_STRING'
COMMAND_WAIT_STRING = 'COMMAND_WAIT_STRING'
COMMAND_SEND_STRING = 'COMMAND_SEND_STRING'
CONDITION_STRING = 'CONDITION_STRING'
COMMAND_REPORT_STRING = 'COMMAND_REPORT_STRING'
OPERATION = 'OPERATION'
SHOW_AUTHOR = 'SHOW_AUTHOR'
SHOW_USAGE = 'SHOW_USAGE'
CIPHER = 'CIPHER'
CONFIG_FILE = 'CONFIG_FILE'

# Logging levels
DEBUG = 'DEBUG'
INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'
CRITICAL = 'CRITICAL'

LOG_LEVELS = {
    DEBUG: logging.DEBUG,
    INFO: logging.INFO,
    WARNING: logging.WARNING,
    ERROR: logging.ERROR,
    CRITICAL: logging.CRITICAL,
}

# Delimiters
STRINGS_DELIMITER = '|'

STRINGS_EQUAL = '='
STRINGS_CONTAINS = '~'
STRINGS_MULTI_CONDITION = '&'

# Markers / Variables
COLUMN_VARIABLE = '$HF_'
NOT_FOUND_MARKER = '$NF'
CIPHER_TEXT_MARKER = '$CT='

# Operations
OPERATION_ACCESS = ACCESS_CHECK
OPERATION_BATCH = COMMANDS_FILE
OPERATION_COMMAND = COMMAND_STRING

# User Default Keys
SSH_CONNECTION_TIMEOUT = 'SSH_CONNECTION_TIMEOUT'
SSH_COMMAND_TIMEOUT = 'SSH_COMMAND_TIMEOUT'
SSH_USER_NAME = 'SSH_USER_NAME'
SSH_PASSWORD_CIPHER = 'SSH_PASSWORD_CIPHER'
SSH_PASSWORD = 'SSH_PASSWORD'
SSH_PRIVATE_KEY = 'SSH_PRIVATE_KEY'
HOSTS_INPUT_FILE = 'HOSTS_INPUT_FILE'
KEY_COLUMN = 'KEY_COLUMN'
SHOW_HOST_DURATION = 'SHOW_HOST_DURATION'
HOST_MARKER = 'HOST_MARKER'
DEBUG_FLAG = 'DEBUG_FLAG'
RUN_IN_SIMULATION_MODE = 'RUN_IN_SIMULATION_MODE'
SHOW_CONSOLE_OUTPUT = 'SHOW_CONSOLE_OUTPUT'
LAST_RUN_OUTPUT = 'LAST_RUN_OUTPUT'
NO_DESTRUCTIVE_PROMPT = 'NO_DESTRUCTIVE_PROMPT'
TRUST_HOSTS = 'TRUST_HOSTS'
LOGS_DIRECTORY = 'LOGS_DIRECTORY'
LOG_FILE = 'LOG_FILE'
SSH_LOG_FILE = 'SSH_LOG_FILE'
LOG_LEVEL = 'LOG_LEVEL'
PROMPT_REGEX = 'PROMPT_REGEX'
NEW_PROMPT_REGEX = 'NEW_PROMPT_REGEX'
NEW_PROMPT = 'NEW_PROMPT'

# Destructive commands
DESTRUCTIVE_COMMANDS = ('rm -rf', 'sudo')

# Options type
BOOL_OPTS = ('-o', '-s', '-h', '-g', '-x', '-a', '-v', '-?')
STRING_OPTS = (
    '-b', '-c', '-w', '-i', '-k', '-e', '-r', '-p', '-d', '--config', '--username', '--password', '--private_key',
    '--cipher_text')
NUM_OPTS = ()
COMMAND_OPTS = ('-c', '-w', '-r', '-p', '-d')

# Options dependencies
EXCLUSIVE_OPTS = (ACCESS_CHECK, COMMANDS_FILE, COMMAND_STRING, SHOW_AUTHOR, SHOW_USAGE, CIPHER)

EXCLUSIVE_OPTS_KEYS = ('-a', '-b', '-c', '-v', '-?', '--cipher_text')

BAD_BATCH_OPTS = (SHOW_CONSOLE_OUTPUT, RUN_SUDO_FIRST, HALT_ON_STRING, COMMAND_SEARCH_STRING,
                  COMMAND_WAIT_STRING, COMMAND_SEND_STRING, COMMAND_REPORT_STRING)

BAD_ACCESS_OPTS = (RUN_SUDO_FIRST, HALT_ON_STRING, COMMAND_SEARCH_STRING, COMMAND_REPORT_STRING,
                   COMMAND_WAIT_STRING, COMMAND_SEND_STRING)

BATCH_COMMANDS_COLUMN_ORDER = [COMMAND_STRING, SHOW_CONSOLE_OUTPUT, LOCAL_COMMAND, COMMAND_WAIT_STRING,
                               COMMAND_SEND_STRING,
                               COMMAND_SEARCH_STRING, COMMAND_REPORT_STRING, HALT_ON_STRING]

VALID_YES = ['yes', 'true', 'y']
VALID_NO = ['no', 'false', 'n', '']

VALID_YES_NO = sum([VALID_YES, VALID_NO], [])

# Command-line Switches
SWITCH_KEYS = collections.OrderedDict()
SWITCH_KEYS['-a'] = ACCESS_CHECK
SWITCH_KEYS['-b'] = COMMANDS_FILE
SWITCH_KEYS['-c'] = COMMAND_STRING
SWITCH_KEYS['-x'] = RUN_IN_SIMULATION_MODE
SWITCH_KEYS['-o'] = SHOW_CONSOLE_OUTPUT
SWITCH_KEYS['-s'] = RUN_SUDO_FIRST
SWITCH_KEYS['-h'] = HALT_ON_STRING
SWITCH_KEYS['-i'] = HOSTS_INPUT_FILE
SWITCH_KEYS['-k'] = KEY_COLUMN
SWITCH_KEYS['-d'] = COMMAND_SEARCH_STRING
SWITCH_KEYS['-w'] = COMMAND_WAIT_STRING
SWITCH_KEYS['-p'] = COMMAND_SEND_STRING
SWITCH_KEYS['-e'] = CONDITION_STRING
SWITCH_KEYS['-r'] = COMMAND_REPORT_STRING
SWITCH_KEYS['-g'] = DEBUG_FLAG
SWITCH_KEYS['-v'] = SHOW_AUTHOR
SWITCH_KEYS['-?'] = SHOW_USAGE
SWITCH_KEYS['--config'] = CONFIG_FILE
SWITCH_KEYS['--username'] = SSH_USER_NAME
SWITCH_KEYS['--password'] = SSH_PASSWORD_CIPHER
SWITCH_KEYS['--private_key'] = SSH_PRIVATE_KEY
SWITCH_KEYS['--cipher_text'] = CIPHER

# Reverse of above
SWITCH_VALUE = {}
for key, value in SWITCH_KEYS.iteritems():
    SWITCH_VALUE[value] = key

user_opts = collections.OrderedDict()

# String defaults
STRING_DEFAULTS = (LOGS_DIRECTORY, HOSTS_INPUT_FILE, KEY_COLUMN, HOST_MARKER, SSH_USER_NAME,
                   SSH_PASSWORD_CIPHER, SSH_PRIVATE_KEY, LAST_RUN_OUTPUT, PROMPT_REGEX, LOG_LEVEL)

BOOLEAN_DEFAULTS = (SHOW_HOST_DURATION, SHOW_CONSOLE_OUTPUT, RUN_IN_SIMULATION_MODE, DEBUG_FLAG,
                    NO_DESTRUCTIVE_PROMPT, TRUST_HOSTS)

NUMBER_DEFAULTS = (SSH_CONNECTION_TIMEOUT, SSH_COMMAND_TIMEOUT)

# System user-defined defaults
defaults = collections.OrderedDict()
defaults[LOGS_DIRECTORY] = 'logs'
defaults[SSH_LOG_FILE] = 'reach_ssh_lib.log'
defaults[LOG_FILE] = 'reach_main.log'
defaults[LAST_RUN_OUTPUT] = 'reach_last_run.log'
defaults[LOG_LEVEL] = INFO
defaults[SSH_CONNECTION_TIMEOUT] = 10
defaults[SSH_COMMAND_TIMEOUT] = 20
defaults[SSH_USER_NAME] = ''
defaults[SSH_PASSWORD_CIPHER] = ''
defaults[SSH_PRIVATE_KEY] = ''
defaults[CONFIG_FILE] = 'configs/config.ini'
defaults[HOSTS_INPUT_FILE] = ''
defaults[KEY_COLUMN] = ''
defaults[SHOW_HOST_DURATION] = False
defaults[DEBUG_FLAG] = False
defaults[RUN_IN_SIMULATION_MODE] = False
defaults[SHOW_CONSOLE_OUTPUT] = False
defaults[HOST_MARKER] = ''
defaults[NO_DESTRUCTIVE_PROMPT] = False
defaults[TRUST_HOSTS] = False
defaults[PROMPT_REGEX] = '[$#>]( )?$'
defaults[NEW_PROMPT_REGEX] = '\[REACH\]# $'
defaults[NEW_PROMPT] = '[REACH]# '

config = collections.OrderedDict()
# Pre-define configs so they are ordered
config[LOGS_DIRECTORY] = defaults[LOGS_DIRECTORY]
config[SSH_LOG_FILE] = defaults[SSH_LOG_FILE]
config[LOG_FILE] = defaults[LOG_FILE]
config[LOG_LEVEL] = defaults[LOG_LEVEL]
config[LAST_RUN_OUTPUT] = defaults[LAST_RUN_OUTPUT]
config[CONFIG_FILE] = defaults[CONFIG_FILE]
config[OPERATION] = ''
config[COMMANDS_FILE] = ''
config[COMMAND_STRING] = ''
config[RUN_IN_SIMULATION_MODE] = False
config[SHOW_CONSOLE_OUTPUT] = defaults[SHOW_CONSOLE_OUTPUT]
config[LOCAL_COMMAND] = False
config[RUN_SUDO_FIRST] = False
config[HALT_ON_STRING] = False
config[HOSTS_INPUT_FILE] = ''
config[COMMAND_SEARCH_STRING] = ''
config[COMMAND_WAIT_STRING] = ''
config[COMMAND_SEND_STRING] = ''
config[CONDITION_STRING] = ''
config[COMMAND_REPORT_STRING] = ''
config[DEBUG_FLAG] = defaults[DEBUG_FLAG]
config[RUN_IN_SIMULATION_MODE] = defaults[RUN_IN_SIMULATION_MODE]
config[SSH_CONNECTION_TIMEOUT] = defaults[SSH_CONNECTION_TIMEOUT]
config[SSH_COMMAND_TIMEOUT] = defaults[SSH_COMMAND_TIMEOUT]
config[SSH_USER_NAME] = defaults[SSH_USER_NAME]
config[SSH_PASSWORD_CIPHER] = defaults[SSH_PASSWORD_CIPHER]
config[SSH_PASSWORD] = ''
config[SSH_PRIVATE_KEY] = defaults[SSH_PRIVATE_KEY]
config[HOSTS_INPUT_FILE] = defaults[HOSTS_INPUT_FILE]
config[KEY_COLUMN] = defaults[KEY_COLUMN]
config[SHOW_HOST_DURATION] = defaults[SHOW_HOST_DURATION]
config[NO_DESTRUCTIVE_PROMPT] = defaults[NO_DESTRUCTIVE_PROMPT]
config[TRUST_HOSTS] = defaults[TRUST_HOSTS]
config[PROMPT_REGEX] = defaults[PROMPT_REGEX]
config[NEW_PROMPT_REGEX] = defaults[NEW_PROMPT_REGEX]
config[NEW_PROMPT] = defaults[NEW_PROMPT]

cli_config = collections.OrderedDict()


def set_defaults():
    """
    Set all configs equal to defaults
    :return: None
    """
    for key in defaults:
        config[key] = defaults[key]


def set_cli_to_config():
    """
    Write user defined options to main config
    :return: None
    """
    for key in cli_config:
        config[key] = cli_config[key]


def set_config(switch, switch_val):
    """
    Read commands switches straight to the config
    :param switch: Switch string (i.e. -c -r etc.)
    :param switch_val: Switch value
    :return: None
    """
    if switch in SWITCH_KEYS:
        config[SWITCH_KEYS[switch]] = switch_val


def set_cli_config(switch, switch_val):
    """
    Save command-line switches to a temporary dict
    :param switch: Switch string (i.e. -c -r etc.)
    :param switch_val: Switch value
    :return: None
    """
    if switch in SWITCH_KEYS:
        cli_config[SWITCH_KEYS[switch]] = switch_val


def check_for_vars():
    """
    Check any string variables in STRING_OPTS for any column variables.
    :return: True if variables found, False otherwise.
    """
    retval = False

    # Check if any of the strings have a variable
    for i in COMMAND_OPTS:
        if COLUMN_VARIABLE in config[SWITCH_KEYS[i]]:
            retval = True

    return retval
