Known Issues
------------

We've extensively tested Reach for production use for a variety of use cases against different target host
types such as Linux, Mac, Vyatta, and Cisco devices.  However, we are aware of some issues and are continually
working towards enhancements.  Here are known issues:

- Reach sends remote commands to a host via an SSH connection over a virtual terminal session. There is no easy
    way to detect command completion. What we did (and is the commonly accepted solution) is to set a
    personalized prompt and detect the prompt in the virtual terminal's output. This works great for common
    commands but we are aware that some situations may lead to unexpected outcomes. Examples:

     - Long running commands: Reach will timeout after SSH_COMMAND_TIMEOUT seconds. If you know some commands
        are slow, make sure to set a high enough timeout value.
     - Executing processes in the background. The command will immediately return but their output will
        intertwine with the subsequent commands' output.
        Possible solution: Redirect the background output to a file.
     - Highly unlikely: the command's output matches the personalized prompt... and then hangs. In that case,
        Reach wrongly assumes the command has completed and goes on to the next command or next host.
     - The initial prompt is not '#', '$', '# ', or '$ ' and thus Reach will fail.
        Solution: configure the PROMPT_REGEX value in config.ini      

- If you are using Excel or any other spreadsheet program to edit CSV files, be careful of invisible characters
    that are introduced when pasting formatted text like that of from the terminal.  You may not see it, but 
    when you paste formatted text to Excel, it preserved formatting and therefore introducing invisible characters
    that will later haunt you in the output or worse yet, the results from Reach.  Solution: Always paste to a 
    text editor first, then copy/paste into Excel before exporting as CSV.

- Other potential issues:
     - For commands that hang (e.g. telnet):
        - Look for alternatives, for example, it is possible to force telnet to exit on successful connection:
            like this: `echo B | telnet -e B 192.168.2.100 8443`, however this only works if the port is
            listening.  If it it's not, it will just hang at "Trying..."
        - An alternative is to use nc. for example, `echo "QUIT" | nc -w 5 192.168.2.100 8443`, if
            connected, it won't display any results, if not, it will display: "Ncat: Connection timed out."
            You can then use the output as a done string (-d) condition.

If in doubt, always run tests on a single host before running against many and use simulation mode (-x) to verify the actions that will be performed.
