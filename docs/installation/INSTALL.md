Steps for installing/using Reach:
--------------------------------

Get the latest stable build of Reach by manually downloading the Reach tree 
[zip file](https://github.com/randyoyarzabal/reach/archive/v1.0.2.zip) OR with git via SSH:

> `git clone git@github.com:randyoyarzabal/reach.git`

*Reach requires Python 2.7 (not compatible with 3.x) and the paramiko library module, if you already have it, skip to Step 5.*

1. Install required packages: 

    >`yum install gcc openssl-devel libffi-devel python-devel glibc python`
    
2. Install EPEL (Extra Packages for Enterprise Linux) Repo for your OS.  
Follow: http://www.tecmint.com/how-to-enable-epel-repository-for-rhel-centos-6-5/
    
3. Install python-pip:

    >`sudo install python-pip` 
    
    OR (if above doesn't work) 
    
    >`sudo yum --enablerepo=epel install python-pip`
    
4. Install paramiko:

    >`pip install paramiko`

    *See [sample log file](sample_install_log.txt) for example sucessful Steps 1-4.*

5. Create a copy of [docs/templates/config_template.ini](../templates/config_template.ini) 
as `config.ini` (exact name required) in the `configs` directory by default. Or, create it with any name you choose 
and pass it to Reach like this: `./reach.py --config_file=<config file>`

5. Have your SSH hosts stored in a CSV files (at a minimum, you just need an IP Address column) 
You can optionally have other columns so you can selectively process hosts, or use host specific 
data like username, password (in cipher text), etc.  See sample [docs/templates/hosts_file_sample.csv](../templates/hosts_file_sample.csv).  The columns and 
specific types are up to you, as long as it is in CSV (comma-delimited) format and you define a KEY_COLUMN (`-k`).
It is recommended you have categorical columns so you can use `-f` later to select a subset of your hosts. 

6. Generate your password cipher text

    >`./reach.py --cipher_text <password>` against all passwords you will use.  Take the output and put 
    in `SSH_PASSWORD_CIPHER` of the `config.ini` file.

7. Edit the rest of `config.ini` file variables to suit your needs.

8. You can optionally do a quick test by checking access to your hosts or by running a simple command:

    - Check access:
        > `./reach.py -a -x` to simulate.

        > `./reach.py -a` to check your access against all the hosts.

    - Run a simple command like `whoami` on all hosts, optionally append a filter condition against the hosts on 
        an available column like `Type` example: `-f 'Type=Linux'` to run only against Linux hosts only:

        > `./reach.py -c 'whoami' -o` (append `-x` to simulate like above)

That's it!

Notes
-------

Note that you may create copies of the config.ini file and pass to the tool like this:

   >`./reach.py --config_file=<config file>`

Optionally, you can also pass the hosts file:

   >`./reach.py -i docs/templates/hosts_file_sample.csv -k 'IP Address' ...`


Remember -x for simulation!  Useful for checking to make sure the commands and filtering (-f)
  is correct before actually executing.
