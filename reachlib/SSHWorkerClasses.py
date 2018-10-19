from reachlib.BaseREOSSHWorker import BaseREOSSHWorker
from reolib.REODelimitedFile import REODelimitedFile
from reachlib.SSHWorkerConfig import *
import pdb


class CheckAccessWorker(BaseREOSSHWorker):
    """
    Concrete class to process access (-a) checks.
    """

    def host_work(self):
        return True  # Don't stop at 1 host

    def run_simulation(self):
        pass


class RunCommandWorker(BaseREOSSHWorker):
    """
    Concrete class to process individual commands (-c).
    """

    def host_work(self):
        retval, error_msg = self.run_command()
        if error_msg:
            print("  - Error: " + error_msg)
        return retval

    def run_simulation(self):
        self.simulate_command()


class RunBatchCommandsWorker(BaseREOSSHWorker):
    """
    Concrete class to process batch commands (-b).
    """

    def __init__(self, commands_file='', logger=None):
        """
        Class Constructor
        :param commands_file: Commands file to process.
        """
        super(self.__class__, self).__init__(logger)

        self.commands_file = commands_file  # Future use
        """File path containing batch commands"""

        self.commands = REODelimitedFile(self.commands_file, ',')
        """File containing batch commands"""

        self.str_vars_exist = True  # Assume true no matter what
        config[BATCH_FILE] = commands_file
        self.process_commands(check_only=True)  # Check for destructive commands, and wait time

    def run_simulation(self):
        self.process_commands(False, True)

    def process_commands(self, check_only=False, simulation=False):
        """
        Loop through commands file for simulation
        :param simulation: True if running in simulation, False otherwise
        :param check_only: True if only checking for destructive commands, False otherwise
        :return: None
        """
        retval = True
        row_num = 0
        for cmd in self.commands:
            row_num += 1

            if row_num == 1:
                continue

            """
            Keys for cmd[X]
            0 - Command
            1 - Show Output Flag
            2 - Local Command
            3 - Wait String(s)
            4 - Send String
            5 - Done String
            6 - Report String(s)
            7 - Halt Loop Flag
            """

            # Trim any Excel generated quotes
            for i, s in enumerate(cmd):
                cmd[i] = self.util.trim_quotes(cmd[i])

            cmd_str = cmd[0]
            if check_only:
                # Check for destructive commands
                config[COMMAND_STRING] = cmd_str

                # Check for destructive commands in the command string or if running sudo
                if True in [(s in config[COMMAND_STRING]) for s in DESTRUCTIVE_COMMANDS]:
                    self.destr_cmds_exist = True  # Once true, always true

                continue

            # 0 - Command: Check/replace if command has vars to replace
            cmd_str = self.replace_column_vars(cmd_str)

            config[COMMAND_STRING] = cmd_str

            # 1 - Show Output Flag
            if cmd[1].lower() in VALID_YES:
                config[SHOW_CONSOLE_OUTPUT] = True
            else:
                config[SHOW_CONSOLE_OUTPUT] = False

            # 2 - Show Output Flag
            if str(cmd[2]).lower() in VALID_YES:
                config[LOCAL_COMMAND] = True
            else:
                config[LOCAL_COMMAND] = False

            # 3 - Wait String(s)
            config[COMMAND_WAIT_STRING] = cmd[3]

            # 4 - Send String
            config[COMMAND_SEND_STRING] = cmd[4]

            # 5 - Done String
            config[COMMAND_SEARCH_STRING] = cmd[5]

            # 6 - Report String(s)
            config[COMMAND_REPORT_STRING] = cmd[6]

            # 7 - Halt Loop Flag
            if str(cmd[7]).lower() in VALID_YES:
                config[HALT_ON_STRING] = True
            else:
                config[HALT_ON_STRING] = False

            if simulation:
                self.simulate_command()
            else:
                if config[LOCAL_COMMAND]:
                    print ("    Running command locally: " + config[COMMAND_STRING])
                    cmd_output = self.util.run_os_command(config[COMMAND_STRING])
                    if config[HALT_ON_STRING]:
                        retval = False
                    if config[SHOW_CONSOLE_OUTPUT]:
                        print("  Console Output: \n" + cmd_output)
                else:
                    new_retval, error_msg = self.run_command()
                    retval &= new_retval
                    # If not continue_commands (ie a command timed out), end
                    # this host and move on to the next
                    # TODO: ask user to retry the batch of commands on this host or not
                    if error_msg:
                        print("  - Error: " + error_msg)
                        break
        return retval

    def host_work(self):
        return self.process_commands(False, config[RUN_IN_SIMULATION_MODE])
