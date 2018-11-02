Installation Instructions
--------------------------------

Notes: *Reach requires Python 2.x (NOT 3.x), paramiko, and pycrypto library modules.* Also, make sure 
your distribution has up-to-date packages. If you don't want to muck with your existing Python installation or unable to 
install required packages, you should consider installing Reach in a Docker or VirtualEnv container (instructions for 
each are beyond the scope of this document.)

1. Install required modules. 

    >`pip install paramiko pycrypto`

2. Get Reach by manually downloading the latest release 
[zip file](https://github.com/randyoyarzabal/reach/archive/v1.0.3.zip).  Alternatively, choose from either the latest 
stable (master) or development branches git:

    1. To get the master (stable) branch:
        > `git clone https://github.com/randyoyarzabal/reach.git`

        Or
    
    2. To get the development branch:
        > `git clone https://github.com/randyoyarzabal/reach.git --branch dev --single-branch <local dir>`
    
3. Create a copy of [docs/templates/config_template.ini](templates/config_template.ini) 
as `config.ini` (exact name required) in the `configs` directory by default. Or, create it with any name you choose 
and pass it to Reach like this: `./reach.py --config_file=<config file>`. Edit the `config.ini`:

    1. `HOSTS_INVENTORY_FILE :` Have your SSH hosts stored in a CSV file inventory.  There's no particular order or number 
    of fields required but at a minimum, you need an IP Address or Hostname (FQDN) column and must be comma-separated with 
    a header column. You can optionally have other columns so you can selectively process hosts, or use host specific data 
    like username, password (in cipher text), private key location etc. 
    See sample [docs/templates/hosts_file_sample.csv](templates/hosts_file_sample.csv).  The columns and specific types 
    are up to you, as long as it is in CSV (comma-delimited) format and you define a `IP_OR_HOST_COLUMN` (`-k`).
    It is recommended you have categorical columns so you can use `-f` later to filter your hosts. 

    2. `CIPHER_KEY_FILE :` Optional (but highly-recommended), create a file with a single string of exactly 32 random 
    characters. In Linux/Mac you can do this automatically by typing the following command:

        >`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1 > /path/somefile`
    
        Or if you get an Illegal byte sequence error try...
    
        >`cat /dev/random | LC_CTYPE=C tr -dc "[:alpha:]" | fold -w 32 | head -n 1 > /path/somefile`
    
    3. Generate your password cipher text

        >`./reach.py --cipher_text` for all passwords you will use.  Take the output and put in `SSH_PASSWORD_CIPHER` 
        of the `config.ini` file or define in the CSV inventory as a column then define `SSH_PASSWORD_CIPHER : $HF_#` 
        where # is the column number of the password to use. You may also use the output of this for any input you'd 
        like to obfuscate by prefixing it with `$CT=<cipher text>` before using it (i.e. with the -p option.)

    4. Edit the rest of `config.ini` file variables to suit your needs. Note the options: `SSH_USER_NAME`, 
    `SSH_PASSWORD_CIPHER`, and `SSH_PRIVATE_KEY`: if you have one user, password, or key for your entire inventory
    you can set it directly. Otherwise, if you have information on a per-host basis, you can define each as the column
    in the inventory. For example, if the SSH username is in column 5: `SSH_USER_NAME : $HF_5`

4. You can do a quick test by checking access to your hosts or by running a simple command:

    - Check access to each host in the inventory file:
        > `./reach.py -a` to check your access against all the hosts.
        
        > `./reach.py -a -x` to simulate.

    - Run a simple command like `whoami` on all hosts, optionally append a filter condition against the hosts on 
        an available column like `Type` example: `-f 'Type=Linux'` to run only against Linux hosts only:

        > `./reach.py -c 'whoami' -o -f 'Type=Linux'` (append `-x` to simulate like above)

5. Optional (but highly-recommended), you may source the bash library in the `extras` directory so that you can use (and
possibly add your own) BASH functions:

    - Add the following to your start-up files (i.e. /etc/profile, ~/.bashrc or ~/.profile):
        > export REACH_DIR='/path_to_reach'
        
        > source $REACH_DIR/extras/reach_bash-lib.sh
        
        > export PATH=$PATH:$REACH_DIR
        
    - Now you may call reach by simply `reach` instead of `reach.py`.  You may also edit the library on-demand:
        > reach.edit_library

That's it! For more information on Reach command options, type: `reach.py -?`

Other Notes
-------

Note that you may create copies of the config.ini file and pass to the tool like this:

   >`./reach.py --config_file=<config file>`

Optionally, you can also pass the hosts file:

   >`./reach.py -i docs/templates/hosts_file_sample.csv -k 'IP_Address' ...`

Remember -x for simulation!  Useful for checking to make sure the commands and filtering (-f)
  is correct before actually executing.
