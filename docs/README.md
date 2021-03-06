[![GitHub release](https://img.shields.io/badge/Download-Release%20v1.0.3-lightgrey.svg?style=social)](https://github.com/randyoyarzabal/reach/releases/latest) [![GitHub commits (since latest release)](https://img.shields.io/github/commits-since/randyoyarzabal/reach/latest.svg?style=social)](https://github.com/randyoyarzabal/reach/commits/master)

### Introduction

Reach is an automation tool that sends SSH commands to one or more hosts and is the perfect complement to any Server or Network Administrator’s tool-box. It is similar to Ansible, but Reach is a faster alternative for operating on your fleet of hosts.  This is accomplished with ad-hoc commands that operate remotely or locally in conjunction with ad-hoc host filters (without the need for any modules or pre-defining custom YAML files).  While it was originally written for network device management like Cisco, F5 or Brocade, it will work on any remote host accessible via SSH, especially those that are Linux/Unix-based. You can get up-and-running very quickly by using existing CSV hosts inventory to send raw/direct series of SSH commands directly to any (or all) of your hosts using on-the-fly filters.  

### Installation

   See the [INSTALL.md](INSTALL.md) file in the `docs` folder.

### Contents
- [Features](#features)
- [Tested Use Cases](#tested-use-cases)
- [Sample Prerequisite Files](#sample-prerequisite-files)
- [Synopsis](#synopsis)
- [Usage / Help](#usage-and-help)
- [Operation Modes](#operation-modes)
- [Optional for Command (-c) Mode](#optional-for-command-mode)
- [Special Variables or Markers](#special-variables-or-markers)
- [Optional for all Modes](#optional-for-all-modes)
- [Special Modes](#special-modes)
- [Examples](#examples)
- [Helpful Tips](#helpful-tips)
- [Developers](#developers)
- [Git Repository](git-repository)

### Features

- Send SSH commands directly to quickly search and adopt changes to your fleet of hosts.
- Get up-and-running quickly using an existing CSV or Excel file of hosts inventory.
- On-the-fly filters using columns in the inventory file.
- Similar to playbooks, create a batch-file of commands to run remotely or locally.
- Password and input text obfuscation.
- Interactive commands support via wait (expect) and send (put) strings. 

### Tested Use Cases

- Network/host Device management (e.g. Cisco, F5, Brocade etc.)
- Firewall (ASA, and Brocade/Vyatta) management configuration
- Middleware installation/support management
- Host package management
- User and Password management
- Multi-host File/State Search
- Monitoring
   
### Sample Prerequisite Files

   - [Inventory/hosts](templates/hosts_file_sample.csv) file
   - [Configuration](templates/config_template.ini) file
   - [Batch commands](templates/sample_commands.csv) file

### Synopsis

    ./reach.py -?
    ./reach.py -v
    ./reach.py -a
    ./reach.py --cipher_text
    ./reach.py --host_fields
    ./reach.py -b commands_file [-x] [-d] ...
    ./reach.py -c command [-s search_string [-r report_string]] [-w wait_string -p response_string] ...

    Optionally, for any mode:
    ./reach.py [--config=<config_file>] [-i inventory_file] [-k column_key] [-x] [-d]

### Usage and Help

    -? : This help screen
    -v : Display version information only

### Operation Modes

    -a : Access Check only
    -b <commands file> : Run Batch Commands (comma separated file, see template for format/options)
    -c <command> : Run Command 

### Optional for Command Mode
#### *Note that for Batch Mode, these are internally defined in the commands file.*

    -o : Show command console output (ignored in batch (-b option) mode)
    -u : Run command as root (run 'sudo su -' first), supports password-less sudo only
    -h : Halt looping through hosts when first done string (-s) is found
    -s <search_string> : Search string in output (For example: 'Complete' or 'Nothing|Complete')
       Can also use '$NF' to test for string is not found.
       -r <report_string> : [Optional with same length as -s] Matching string to print to screen when -s match
          For example: 'Installed|Not Installed'
    -w <wait_string> : Wait string
       -p <response_string> : [Required with same length as -w] Send a string when -w string is found

### Optional for all Modes 

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

### Special Variables or Markers

#### Variables/markers:

    $HF_# : Reference to the host file where # is the column number.
    $NF : Signal that the search string is not found in -s e.g. '-s search_string|$NF'
    $CT=<cipher text> : Used for sending passwords to the terminal like changing passwords or sending 
        Cisco ASA passwords in "enable" mode. Used in -p, or as host column data; can then be referenced 
        as $HF_# as described below ($HF_# support). 
        *See related option: --cipher_text option.*
   
#### The following support $HF_#:
##### Command-line options:
	-s, -r, -w, -p, --username=, --password=, --private_key=
	
##### Configuration options:
	SSH_USER_NAME, SSH_PASSWORD_CIPHER, SSH_PRIVATE_KEY_FILE, HOST_DISPLAY_FORMAT
	
#### Special keystrokes for use in -p:

    ENTER_KEY : '\n'
    RETURN_KEY : '\r'
    TAB_KEY : '\t'
    SPACE_KEY : ' '

### Special Modes

    --cipher_text : generate cipher text from a password for use in SSH_PASSWORD_CIPHER or $CT=<cipher_text> (-p)
    --host_fields : return a list of column headers (with $HF_#) from the host file

### Examples

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
    ./reach.py -c 'passwd randyo' -w 'New|Retype' -p 'mypass3|mypass3' -s 'successfully' -r 'Changed password'
    Remember that -p supports $CT=<cipher text> to obfuscate the password. So it would be: -p '$CT=xxxxx|$CT=xxxxx'

### Helpful Tips

    - Always be sure to run in SIMULATION (-x) mode first to see what the script is about to do!
    NOTE: Some of the example below use specific details that may not pertain to your use and is 
       provided simply as a guide.
    - Use the -r option in conjunction with -s to substitute results, optionally use: grep and/or sed to limit output.
        Example: Search all hosts where 'vyatta' is found in the zones list.
        ./reach.py -c 'show zone-policy zone' -s 'vyatta|$NF' -r 'yes|no' | grep -E 'yes|no' 
      Or used the output in the logs/last_run-log.txt
      You may then paste the output as a new column in your inventory file.
    - Use bash aliases for different hosts inventory or use, for example:
        alias prjA-Utility='reach.py --config=/util_hosts/projectA.ini'
        alias prjB-Utility='reach.py --config=/util_hosts/projectB.ini'
        alias home-Utility='reach.py --config=/util_hosts/combined.ini -f "Location=Home" --username=\$HF_5'
        alias work-Utility='reach.py --config=/util_hosts/combined.ini -f "Location=Work"'
    - You can even use a bash function of your favorite use, for example, to find the firewall that an IP belongs to:
        function find_firewall { whcUtility -c "sh ip route $1" -s 'bond0.|bond0' \
        -r 'Found in: $HF_1 - $HF_3 : $HF_5|Not Here' "${@:2}" -h; }
      To use this: find_firewall <ip address>
      If you're wondering what "${@:2}" means, it is a neat bash specific notation for handling additional 
      arguments you may want to use, like: -x (simulation) or -d (debug) etc.
    - Be sure to set SSH_COMMAND_TIMEOUT higher than the longest anticipated command duration. But not too high because
      if a command hangs, it will wait for that duration before timing out.

### Developers

- Randy Oyarzabal 
- Francis Lan

### Git Repository
[https://github.com/randyoyarzabal/reach](https://github.com/randyoyarzabal/reach)
