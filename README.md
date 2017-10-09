### Developers

- Randy Oyarzabal 
- Francis Lan

### Tested Use Cases

- Firewall rules validation
- Network device configuration (e.g. Cisco, F5, Brocade etc. equipment)
- Firewall / host backups
- Middleware installation/support management
- Host package management
- User and Password management
- Multi-host File/State Search
- Monitoring

### Installation

   See the [INSTALL.md](docs/installation/INSTALL.md) file in the `docs/installation/` folder.
   
### Sample Prerequisite Files

   - [Inventory/hosts](docs/templates/hosts_file_sample.csv) file
   - [Configuration](docs/templates/config_template.ini) file
   - [Batch commands](docs/templates/sample_commands.csv) file

### Synopsis

    ./reach.py -?
    ./reach.py -v
    ./reach.py -a
    ./reach.py --cipher_text=<password>
    ./reach.py -b commands_file [-x] [-g] ...
    ./reach.py -c command [-d search_string [-r report_string]] [-w wait_string -p response_string] ...

    Optionally, for any mode:
    ./reach.py [--config=<config_file>] [-i inventory_file] [-k column_key] [-x] [-g]

### Help / Usage

    -? : This help screen
    -v : Display version information only

### Operation Modes

    -a : Access Check only
    -b <commands file> : Run Batch Commands (comma separated file, see template for format/options)
    -c <command> : Run Command 

### Optional for all Modes 

    --config=<config_file> Override the default config.ini
    -x : Enable SIMULATION (no connection/commands invoked)
    -g : Enable DEBUG
    -i <inventory_file> : Inventory (hosts) file (comma separated, define header key with -k)
      -k <key_column> : [Required with -i] Column header of keys
    -e <condition> : Filter hosts to process. Operators are supported: = equal, | or, ~ contains, & and.
        Note: Reach does not support mixed (& and |) in this release.
        Example conditions: 'Build=WHC0122' , 'Build=WHC0122&Host~app, 'Build=WHC0122|Host~app|Host~dom'

### Optional for Command (-c) Mode
##### *Note that for Batch Mode, these are internally defined in the commands file.*

    -o : Show command console output (ignored in batch (-b option) mode)
    -s : Run command as root (run 'sudo su -' first)
    -h : Halt looping through hosts when first done string (-d) is found

##### The following can use hosts file column variables ($HF) delimited by '|':
##### *For example: '$HF_#' where # is the column number in the hosts file*

     --username=<ssh_user> : Force user string instead of what is configured.
     --password=<ssh_cipher-text password> : Force cipher-text password instead of what is configured.
     --private_key=<ssh_rsa_key> : Force private RSA key file instead of what is configured.
     -d <search_string> : Search for string in output (For example: 'Complete' or 'Nothing|Complete')
        Can also use '$NF' to test for string is not found.
        -r <report_string> : [Optional with same length as -d] Matching string to print to screen when -d match
           For example: 'Installed|Not Installed'
     -w <wait_string> : Wait string
        -p <response_string> : [Required with same length as -w] Send a string when -w string is found
          The following list of special markers can be used in -p:
            $ENTER_KEY : '\n'
            $RETURN_KEY : '\r'
            $TAB_KEY : '\t'
            $SPACE_KEY : ' '
            $CT=<password in cipher text> : Used for sending passwords to the terminal like changing passwords 
              or sending Cisco ASA passwords in "enable" mode.  

### Special mode only for changing passwords to cipher text
    --cipher_text=<password> return the password in cipher text to put in the password file

### Examples

    - Run 'yum -y install gdb' as root, look for the strings: 'Nothing' or 'Complete', then display
        'Installed' or 'Not Installed' on the screen. Process hosts matching 'Build' column = 'WHC038'
    ./reach.py -c 'yum -y install gdb' -s -d 'Nothing|Complete' -r 'Installed|Not Installed' -e 'Build=WHC038'
              -------------------------------------------------------------------------------
    - Run 'sh ip route 10.143.92.134', look for the strings: 'bond0.' or 'bond0', then display
        'Found in: $HF_1' ($HF_1 is the first column of the inventory) or 'Not Here' then halt the hosts loop
    ./reach.py -c "sh ip route 10.143.92.134" -d 'bond0.|bond0' -r 'Found in: $HF_1|Not Here' -h
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
    ./reach.py -c 'passwd randyo' -w 'New|Retype' -p 'mypass3|mypass3' -d 'successfully' -r 'Changed password'

### Helpful Tips

    - Always be sure to run in SIMULATION (-x) mode first to see what the script is about to do!
    NOTE: Some of the example below use specific details that may not pertain to your use and is 
       provided simply as a guide.
    - Use the -r option in conjunction with -d to substitute results, optionally use: grep and/or sed to limit output.
        Example: Find all hosts where 'vyatta' is found in the zones list.
        ./reach.py -c 'show zone-policy zone' -d 'vyatta|$NF' -r 'yes|no' | grep -E 'yes|no' 
      Or used the output in the logs/last_run-log.txt
      You may then paste the output as a new column in your inventory file.
    - Use bash aliases for different hosts inventory or use, for example:
        alias prjA-Utility='reach.py --config=/util_hosts/projectA.ini'
        alias prjB-Utility='reach.py --config=/util_hosts/projectB.ini'
        alias home-Utility='reach.py --config=/util_hosts/combined.ini -e "Location=Home" --username=\$HF_5'
        alias work-Utility='reach.py --config=/util_hosts/combined.ini -e "Location=Work"'
    - You can even use a bash function of your favorite use, for example, to find the firewall that an IP belongs to:
        function find_firewall { whcUtility -c "sh ip route $1" -d 'bond0.|bond0' \
        -r 'Found in: $HF_1 - $HF_3 : $HF_5|Not Here' "${@:2}" -h; }
      To use this: find_firewall <ip address>
      If you're wondering what "${@:2}" means, it is a neat bash specific notation for handling additional 
      arguments you may want to use, like: -x (simulation) or -g (debug) etc.
    - Be sure to set SSH_COMMAND_TIMEOUT higher than the longest anticipated command duration. But not too high because
      if a command hangs, it will wait for that duration before timing out.

### Git Repository
[https://github.com/randyoyarzabal/reach](https://github.com/randyoyarzabal/reach)
