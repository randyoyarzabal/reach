import re
import sys

from reachlib.SSHWorkerConfig import *
from reolib.REODelimitedFile import REODelimitedFile
from reolib.REORemoteHost import REORemoteHost
from reolib.REOUtility import REOUtility


class BaseREOSSHWorker(object):
    """
    This class is a semi-abstract class defining basic tasks for an SSH activity.
    Logging on, iterating through the hosts file, and processing it.  How the hosts are processed
    is defined in the work() method that concrete classes need to implement.
    """

    def __init__(self, logger=None):
        """
        Class constructor
        """
        self.rhost = None
        """SSH Host"""

        self.host_or_ip = ''
        """Current Hostname or IP being processed"""

        self.current_host = None
        """Current host being processed"""

        self.hosts = REODelimitedFile(config[HOSTS_INVENTORY_FILE], ',', has_header=True)
        """Main hosts file for processing"""

        self.util = REOUtility(config[DEBUG_FLAG])
        """Utility instance"""

        self.last_run_log = open(config[LOGS_DIRECTORY] + config[LAST_RUN_OUTPUT], 'w')
        """File containing results strings only for the last run"""

        self.command_string = ''
        """Command string (vars replaced)"""

        self.search_string = ''
        """Search string delimited (vars replaced)"""

        self.report_string = ''
        """Report (for search) delimited (vars replaced) string"""

        self.wait_string = ''
        """Wait string delimited (vars replaced)"""

        self.response_string = ''
        """Send/put string delimited (vars replaced)"""

        self.search_strings = None
        """Search strings (vars replaced) list"""

        self.report_strings = None
        """Report/put strings (vars replaced) list"""

        self.wait_strings = None
        """Wait strings list (vars replaced) list"""

        self.response_strings = None
        """Send/put strings list (vars replaced) list"""

        self.response_strings_display = None
        """Send string for screen display list"""

        self.str_vars_exist = False
        """String vars existence flag"""

        self.destr_cmds_exist = False
        """Destructive commands flag"""

        self.phost_count = 0  # Processed hosts
        """Number of processed hosts"""

        self.logger = logger
        """Optional logger (from logging module) instance"""

    def hosts_worker(self):
        """
        The is the main entry point for an instance of the concrete class.
        :return: None
        """

        self.phost_count = 0  # Processed hosts

        self.show_header_confirmation()

        log_str = ("# This file is only relevant/useful for a single command (-c) with a (-s or -r) defined.\n"
                   "# It is meant to be pasted in a new column spreadsheet of the hosts file.\n")

        if config[FILTER_STRING]:
            log_str += "# Filtered results: " + config[FILTER_STRING] + "\n"
            self.log(logging.WARNING, "Filtered results: " + config[FILTER_STRING], False)

        self.last_run_log.write(log_str)

        for host in self.hosts:
            self.current_host = host
            self.host_or_ip = self.hosts.get_row_val(name=config[IP_OR_HOST_COLUMN])

            if config[FILTER_STRING]:
                try:
                    # TODO: Handle complex conditions with mixed & and |
                    if STRINGS_MULTI_CONDITION in config[FILTER_STRING]:
                        conditions = config[FILTER_STRING].split(STRINGS_MULTI_CONDITION)
                        alltrue = True
                    elif STRINGS_DELIMITER in config[FILTER_STRING]:
                        conditions = config[FILTER_STRING].split(STRINGS_DELIMITER)
                        alltrue = False
                    else:
                        conditions = [config[FILTER_STRING]]

                    conditions_values = map(lambda condition: self.__eval_condition(condition), conditions)
                    skip_host = not reduce(lambda x, y: x & y if alltrue else x | y, conditions_values)

                    if skip_host:
                        self.log(logging.DEBUG, self.host_or_ip + ' - does not meet filter: ' + config[
                            FILTER_STRING] + ' == Skipping', False)
                        continue  # Skipping host...
                except KeyboardInterrupt:
                    self.util.key_interrupt()

            self.phost_count += 1
            if not config[SIMULATION_MODE]:
                if not self.host_worker():
                    break  # Stop loop if concrete method returns False
            else:
                # Simulated run
                self.__process_host_simulation()

            if self.phost_count % 10:  # Don't delay writing to file for every 10 hosts processed.
                self.last_run_log.flush()

        print ""
        self.log(logging.INFO,
                 "Script Duration: " + str(self.util.get_current_duration()) + " " + STRINGS_DELIMITER + " " + str(
                     self.phost_count) + " out of " + str(len(self.hosts)) + " hosts processed.", True)

    def host_worker(self):
        """
        Common code defining prerequisite actions per host like making the remote connection.
        :return: True signal continuation of hosts iteration, False otherwise.
        """
        retval = True
        self.util.start_timer()

        self.rhost = REORemoteHost(self.host_or_ip, config[PROMPT_REGEX], config[NEW_PROMPT_REGEX],
                                   config[NEW_PROMPT], logger=self.logger)

        if config[CIPHER_KEY_FILE]:
            self.rhost.cipher_key = REOUtility.get_string_from_file(config[CIPHER_KEY_FILE])
        else:
            self.rhost.cipher_key = REOUtility.CIPHER_KEY

        self.rhost.ssh_lib_log = config[LOGS_DIRECTORY] + config[SSH_LOG_FILE]
        self.rhost.util.toggle_debug(config[DEBUG_FLAG])
        self.rhost.usr = self.replace_column_vars(config[SSH_USER_NAME])

        if config[SSH_PASSWORD_CIPHER]:
            self.rhost.pwd = REOUtility.decrypt_str(self.replace_column_vars(config[SSH_PASSWORD_CIPHER]),
                                                    self.rhost.cipher_key)
        else:
            self.rhost.pwd = config[SSH_PASSWORD]

        self.rhost.key_file = self.replace_column_vars(config[SSH_PRIVATE_KEY_FILE])
        self.rhost.str_vars_exist = self.str_vars_exist

        if config[HOST_DISPLAY_FORMAT]:
            print self.__get_process_str() + self.replace_column_vars(config[HOST_DISPLAY_FORMAT]) + " ...",
            self.log(logging.INFO, "Processing host: " + self.replace_column_vars(config[HOST_DISPLAY_FORMAT]))
        else:
            print self.__get_process_str() + self.host_or_ip + " ...",
            self.log(logging.INFO, "Processing host: " + self.host_or_ip)
        sys.stdout.flush()

        connected = self.rhost.connect_host(set_prompt=config[OPERATION] != OPERATION_ACCESS,
                                            conn_timeout=config[SSH_CONNECTION_TIMEOUT],
                                            cmd_timeout=config[SSH_COMMAND_TIMEOUT],
                                            trust_hosts=config[SSH_TRUST_HOSTS], agent_only=config[SSH_AGENT_ONLY])

        self.log(logging.INFO, self.rhost.connect_status_string, True)
        if config[OPERATION] == OPERATION_ACCESS:
            self.last_run_log.write(self.rhost.connect_status_string + "\n")
        else:
            if self.rhost.connect_status_string != self.rhost.SERVER_STATUS_CONNECTED:
                self.last_run_log.write(self.rhost.connect_status_string + "\n")

        if connected:
            # Implemented in different ways by concrete classes
            retval = self.host_work()
            if config[SHOW_HOST_DURATION] and config[OPERATION] != OPERATION_ACCESS:
                print ("  Host Duration: " + str(self.util.stop_timer()))

        return retval

    def host_work(self):
        """
        Abstract method to be implemented by concrete class
        This method defines how the hosts are processed
        """
        raise NotImplementedError

    def run_command(self):
        """
        Process a single command with its options stored in the config[] dict.
        :return: True signal continuation of hosts iteration, False otherwise (halt).
        """
        retval = True

        self.__replace_vars_in_strings()

        if config[RUN_SUDO_FIRST]:
            sudo_cmd = 'sudo su -'
            if self.str_vars_exist:
                print ("  Switching to root user with: \'" + sudo_cmd + "\'")
                self.log(logging.INFO, 'Sudo switch to root user', False)
            output, error_msg = self.rhost.send_cmd_wait_respond(sudo_cmd, last_run_log=self.last_run_log)

            if error_msg:
                if config[SHOW_CONSOLE_OUTPUT]:
                    print ("  - Console Output: \n" + output)
                return retval, error_msg

        if self.str_vars_exist:
            print ("  Running command: \'" + self.command_string + "\'")
            self.log(logging.INFO, "Running command: \'" + self.command_string + "\'", False)

        if self.search_string or self.wait_string:
            # Send the command to the server and wait for a string
            output, error_msg = self.rhost.send_cmd_wait_respond(self.command_string, self.search_string,
                                                                 self.wait_string, self.response_string,
                                                                 self.last_run_log)
            # skip the rest of the if statement if error_msg != '' ?
            w = self.rhost.search_string_isfound

            if self.report_string and (w != ''):
                result = self.report_strings[self.search_strings.index(w)]
                print ("  - " + result)
                self.log(logging.INFO, "Report String: " + result, False)
                self.last_run_log.write(result + "\n")
                self.log(logging.DEBUG, "Command Wait String Found: " + w, False)
            else:
                if w != '':
                    self.log(logging.INFO, "  - Found: " + w, True)
                    self.last_run_log.write("Found: " + w + "\n")

            if config[HALT_ON_STRING]:
                if w == self.search_strings[0]:
                    print ("  - Found: \'" + w + "\' halting as requested.")
                    self.log(logging.INFO, "Found \'" + w + "\' halting as requested.", True)
                    retval = False  # Stop hosts loop, we found what we are looking for

        else:
            # Send the command to the server and wait for a string
            output, error_msg = self.rhost.send_cmd_wait_respond(self.command_string, last_run_log=self.last_run_log)

        if config[SHOW_CONSOLE_OUTPUT]:
            print ("  - Console Output: \n" + output)

        return retval, error_msg

    def show_header_confirmation(self):
        """
         Method to display confirmation information before execution.
        :return:
        """
        # Display for any mode
        print "Hosts File: " + config[HOSTS_INVENTORY_FILE]

        if not self.str_vars_exist:
            if config[RUN_SUDO_FIRST]:
                print ("- Will switch to root user with: \'sudo su -\'")

            if config[OPERATION] != OPERATION_ACCESS:
                print "- Command string to run: '" + config[COMMAND_STRING] + "'"

            if config[LOCAL_COMMAND]:
                print "- Will run command locally"

            if config[COMMAND_FIND_STRING]:
                print "- Search String: '" + config[COMMAND_FIND_STRING] + "'"

            if config[COMMAND_REPORT_STRING]:
                print "  - Report String: '" + config[COMMAND_REPORT_STRING] + "'"

            if config[COMMAND_WAIT_STRING]:
                print "- Wait String: '" + config[COMMAND_WAIT_STRING] + "'"

            if config[COMMAND_SEND_STRING]:
                tmp_list = config[COMMAND_SEND_STRING].split(STRINGS_DELIMITER)
                tmp_list = STRINGS_DELIMITER.join(
                    self.__replace_vars_in_list(tmp_list, replace_column=False, display_only=True))
                print "  - Send/Response String: '" + tmp_list + "'"

            if config[SHOW_CONSOLE_OUTPUT]:
                print "- Show console output"

            if config[HALT_ON_STRING] and config[COMMAND_FIND_STRING]:
                print ("- If " + config[COMMAND_FIND_STRING] + " is found, hosts loop will halt")

            if config[SHOW_HOST_DURATION] and config[OPERATION] != OPERATION_ACCESS:
                print ("- Calculate and show host processing duration")

        # Display the rest for specific modes
        if config[OPERATION] == OPERATION_BATCH:
            print "- Commands File: " + config[BATCH_FILE]
        if config[FILTER_STRING]:
            print ("Filter found. Filtering processing to: '" + config[FILTER_STRING]) + "'"

        print ("--------------------------------------------------------------------")

        if not config[NO_DESTRUCTIVE_PROMPT]:
            if config[OPERATION] == OPERATION_COMMAND:
                # Check for destructive commands in the command string or if running sudo
                if True in [(s in config[COMMAND_STRING]) for s in DESTRUCTIVE_COMMANDS] or config[RUN_SUDO_FIRST]:
                    self.destr_cmds_exist = True

            if self.destr_cmds_exist and not config[SIMULATION_MODE]:
                if not self.util.query_yes_no("\nYour command(s) contains one or more destructive commands: " + str(
                        DESTRUCTIVE_COMMANDS) + ".\nAre you sure you want to continue?", default='no'):
                    sys.exit(2)
                else:
                    self.log(logging.WARNING, "Destructive commands execution confirmed.", False)

        if not config[SIMULATION_MODE]:
            if not config[SSH_AGENT_ONLY]:
                # Prompt for user/password if not defined.
                if not config[SSH_USER_NAME] and not config[SSH_PASSWORD_CIPHER]:
                    config[SSH_USER_NAME], config[SSH_PASSWORD] = self.util.prompt_user_password(desc="SSH")

                elif not config[SSH_USER_NAME]:
                    config[SSH_USER_NAME], none = self.util.prompt_user_password(password_prompt=False, desc="SSH")

                elif not config[SSH_PASSWORD_CIPHER]:
                    none, config[SSH_PASSWORD] = self.util.prompt_user_password(user_prompt=False, desc="SSH")

    def simulate_command(self):
        """
        Display simulation confirmation per host
        :return: None
        """
        if not self.str_vars_exist:
            return

        self.__replace_vars_in_strings()

        if config[RUN_SUDO_FIRST]:
            print ("  Switch to root user with: \'sudo su -\'")

        if config[LOCAL_COMMAND]:
            print ("  Run command locally: \'" + self.command_string + "\'")
        else:
            print ("  Run command: \'" + self.command_string + "\'")

        if self.search_string:
            print ("  - Search for string(s): " + self.search_string)

            if self.report_string:
                print "    - Display string(s): '" + self.report_string + "'"

        if self.wait_string:
            print ("  - Wait for string(s) in sequence: " + self.wait_string)
            print ("    - Send string(s) in sequence: " + self.response_string_display)

        if config[HALT_ON_STRING] and self.search_string:
            print ("  - If '" + self.search_string + "' is found, hosts loop will halt.")

        if config[SHOW_CONSOLE_OUTPUT]:
            print ("  - Print console output")

        if config[SHOW_HOST_DURATION] and config[OPERATION] != OPERATION_ACCESS:
            print ("  - Calculate and show host processing duration")

    def __process_host_simulation(self):
        """
        Display per-host progress to screen.
        :return: True signal continuation of hosts iteration, False otherwise (halt).
        """  # Running in simulation mode
        if config[HOST_DISPLAY_FORMAT]:
            print (self.__get_process_str() + self.replace_column_vars(config[HOST_DISPLAY_FORMAT]))
        else:
            print (self.__get_process_str() + self.host_or_ip)

        # Implemented in different ways by concrete classes
        self.run_simulation()

    def run_simulation(self):
        """
        Abstract method to be implemented by concrete class
        This method defines how the hosts are simulated
        """
        raise NotImplementedError

    def display_host_fields(self):
        """
        Display a list of host file headers with corresponding $HF_#
        :return:
        """
        for i, col in enumerate(self.hosts.header_list):
            if col == config[IP_OR_HOST_COLUMN]:
                col = col + " (Key Column)"
            print '$HF_%s = %s' % (str(i + 1), col)

    def __eval_condition(self, filter):
        """
        Evaluate a single filter string. For example: 'Build=WHC058' or 'Hostname~app'
        :param filter: filter to be evaluated
        :return: True if filter is met, False otherwise.
        """
        ret_val = False
        t_cond = re.split("[~=!]", filter)
        if len(t_cond) != 2:
            raise KeyError('Invalid filter: ' + filter)
        field = t_cond[0]
        fvalue = t_cond[1]
        try:
            rvalue = self.current_host[field]
        except KeyError:
            # shouldn't happen, filter is already checked
            raise KeyError('Invalid field "' + field + '" in filter ' + filter)

        if STRINGS_CONTAINS in filter:
            ret_val = (fvalue in rvalue)
        elif STRINGS_NOT_EQUAL in filter:
            ret_val = (fvalue != rvalue)
        else:
            ret_val = (fvalue == rvalue)

        return ret_val
        # return (fvalue in rvalue) if '~' in filter else (fvalue == rvalue)

    def __replace_vars_in_list(self, l, replace_column=True, display_only=False):
        """
        Replace and column vars ($HF_#) with real values.
        :param l: List potentially containing vars.
        :return: New list with vars replaced with real values.
        """
        new_list = l
        for i, r in enumerate(new_list):
            x = r
            if replace_column:
                x = self.replace_column_vars(r)
            # Replace key strokes for display if exists
            if display_only:
                for k_str in REORemoteHost.KEY_STROKE_DISPLAY:
                    x = x.replace(k_str, REORemoteHost.KEY_STROKE_DISPLAY[k_str])
                cipher_text = re.search(re.escape(CIPHER_TEXT_MARKER) + '[^|]*', x)
                if cipher_text is not None:
                    x = x.replace(cipher_text.group(0), '**********')
            new_list[i] = x
        return new_list

    def __replace_vars_in_strings(self):
        """
        Replace vars ($HF_#) in switch strings
        :return: None
        """
        # Turn strings into list delimited by |
        self.command_string = [self.util.trim_quotes(config[COMMAND_STRING])]
        self.search_strings = config[COMMAND_FIND_STRING].split(STRINGS_DELIMITER)
        self.report_strings = config[COMMAND_REPORT_STRING].split(STRINGS_DELIMITER)
        self.wait_strings = config[COMMAND_WAIT_STRING].split(STRINGS_DELIMITER)
        self.response_strings = config[COMMAND_SEND_STRING].split(STRINGS_DELIMITER)

        # Replace column/string and key stroke variables
        self.command_string = STRINGS_DELIMITER.join(self.__replace_vars_in_list(self.command_string))
        self.report_string = STRINGS_DELIMITER.join(self.__replace_vars_in_list(self.report_strings))
        self.wait_string = STRINGS_DELIMITER.join(self.__replace_vars_in_list(self.wait_strings))
        self.search_string = STRINGS_DELIMITER.join(self.__replace_vars_in_list(self.search_strings))
        self.response_string = STRINGS_DELIMITER.join(self.__replace_vars_in_list(self.response_strings))

        # Special case for showing response_strings with key stroke variables
        self.response_string_display = STRINGS_DELIMITER.join(
            self.__replace_vars_in_list(self.response_strings, display_only=True))

    def replace_column_vars(self, s):
        """
        Replace a column var with its corresponding value.
        :param s: Column variable
        :return: Column value
        """
        cmd_str = s
        if COLUMN_VARIABLE in cmd_str:
            hvars = re.findall(re.escape(COLUMN_VARIABLE) + '\d*', cmd_str)
            for hvar in hvars:  # Replace all variables found
                col_num = int(hvar.split("_")[1])  # Read integer after $HF_
                cmd_str = cmd_str.replace(hvar, self.hosts.get_row_val(self.hosts.current_row, col_idx=col_num - 1))
        return cmd_str

    def log(self, level, message, print_to_screen=False):
        """
        Logging mechanism if defined.
        :param level: Log level
        :param message: Message
        :param print_to_screen: True to print message to screen as well
        :return:
        """
        if print_to_screen:
            print message

        if self.util.debug and level == logging.DEBUG:
            self.util.print_debug(message)

        if self.logger:
            self.logger.log(level, message)

    def __get_process_str(self):
        """
        Add new-lines to string depending on conditions for better reporting output
        :return: Proper string to display
        """
        p_str = 'Processing host: '
        if config[OPERATION] in (OPERATION_COMMAND, OPERATION_ACCESS):
            if self.phost_count == 1 or self.str_vars_exist:
                p_str = "\n" + p_str
        if config[OPERATION] == OPERATION_BATCH:
            if not self.destr_cmds_exist or self.phost_count > 1:
                p_str = "\n" + p_str

        return p_str

    def __del__(self):
        """
        Class destructor. Close log file.
        :return:
        """
        self.last_run_log.close()
