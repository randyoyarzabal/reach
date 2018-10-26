#!/usr/bin/env bash
# This is an OPTIONAL BASH library for use with Reach. Feel free to add aliases, functions etc.
# To use this, just source in your start_up script (i.e. profile or bashrc)

# A collection of utility environment vars, aliases and functions for Reach etc.
#
# Dev notes:
#    - Add "${@:N}" to the end of a function for dynamic parameters to be passed. Where N represents the optional parameter.
#    - Single quotes wont expand vars unless used in an alias. Use double quotes instead.

# ALIAS DEFINITIONS
############################

shopt -s expand_aliases

# Define the reach location here
REACH_DIR='/Users/m173404/dev/repos/github/reach'
REACH_BASH_LIB="$REACH_DIR/extras/reach_bash-lib.sh"
REACH_TOOL="$REACH_DIR/reach.py"

alias reach='$REACH_TOOL'

# Define any special aliases here

# Example aliases:
# alias reach-linux='$REACH_TOOL -f TYPE=Linux'

# Check platform type
# Probably best to fully define 'uname' path for cross-compatibility
uname_out="$(uname -s)"
case "${uname_out}" in
    Linux*)     PLATFORM='Linux';;
    Darwin*)    PLATFORM='Mac';;
    CYGWIN*)    PLATFORM='Cygwin';;
    MINGW*)     PLATFORM='MinGw';;
    *)          PLATFORM="UNKNOWN:${uname_out}"
esac

# GENERAL UTILITY FUNCTIONS
############################

function reach.search {
   if [ -z "$1" ] || [ -z "$2" ] || [ "$1" == "-?" ]; then
      echo "Find a string in the result of a command against the host fleet."
      echo "Usage: $FUNCNAME <command> <search string>";
      return;
   fi
   __timer start

   echo "Executing \"$1\" against selected hosts.  Searching for: \"$2\"";

   # This script can also be customized to halt the search (hosts iteration) with -h when string is found on a host.
   reach -c "$1" -s "$2"'|$NF' -r 'Found in Host: $HF_1 ($HF_3)|Not Found in Host: $HF_1 ($HF_3)' "${@:3}" | grep --color=never Found;

   __timer end
}

# HELPER FUNCTIONS
############################
function reach.edit_library() {
   if [ "$1" == "-?" ]; then
      echo "Edit the utility library."
      echo "Usage: $FUNCNAME"
      return;
   fi

   file="$REACH_BASH_LIB";
   if [ "$PLATFORM" == "Mac"  ]; then
       date=$(stat -f "%Sm" -t "%Y%m%dT%H%M%S" "$file");
       vi $file;
       date2=$(stat -f "%Sm" -t "%Y%m%dT%H%M%S" "$file");
   else
       date=$(stat -c %y "$file");
       vim $file;
       date2=$(stat -c %y "$file");
   fi

   # check if the file was actually modified before reloading
   if [[ $date2 != $date ]]; then
     echo "REACH BASH library was modified."
     reach.reload_library
   fi
}

function reach.reload_library() {
   if [ "$1" == "-?" ]; then
      echo "Reload this utility library."
      echo "Usage: $FUNCNAME"
      return;
   fi
   . $REACH_BASH_LIB
   echo "REACH BASH library was reloaded."
}

function __timer () {
   # Usage: __timer <start | end>
   if [ "$PLATFORM" != "Mac" ]; then  # Need to figure out the Mac equivalent of below
      if [ "$1" = "start" ]; then SECONDS=0; return; fi
      if [ "$1" = "end" ]; then echo "Task took: "`date +%T -d "1/1 + $SECONDS sec"`; fi
   fi
}

function __lower() {
   # Usage: __lower <string>
   valStr=$1
   valStr=`echo $valStr | awk '{print tolower($0)}'`
   echo $valStr
}

function __upper() {
   # Usage: __upper <string>
   valStr=$1
   valStr=`echo $valStr | awk '{print toupper($0)}'`
   echo $valStr
}

function __proper() {
   # Usage: __proper <string>
   sed 's/.*/\L&/; s/[a-z]*/\u&/g' <<<"$1"
}

function __isvalid_ip() {
   # Usage: __isValid_ip
   local  ip=$1
   local  stat=1

   if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
       OIFS=$IFS
       IFS='.'
       ip=($ip)
       IFS=$OIFS
       [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 \
           && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
       stat=$?
   fi
   return $stat
}

function __begin {
   # Linux implementation of Cisco's "begin"
   cat | sed -n "/$1/,\$p"
}
alias be='__begin'

function __show_progress() {
   # Usage: __show_progress <msg> <command> <output_variable>
   MSG_LENGTH=$(echo -n $1 | wc -m)
   # Create a random file to hold output
   tmp_file="/tmp/._`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1`"

   # Process the command in the background until it returns (saving the output to the temp file.
   #   In the meantime, keep printing the spinner chars.
   read < <( eval "$2" > $tmp_file & echo $! ); printf "$1"; __spinner $REPLY;

   # Clear the message in-place
   start=1
   end=$MSG_LENGTH

   # Move the cursor to the left
   for ((i=$start; i<=$end; i++)); do printf "$KEYS_LEFT"; done

   # Blank the message
   for ((i=$start; i<=$end; i++)); do printf " "; done

   # Reposition the cursor to the beginning before any other writes to the screen
   for ((i=$start; i<=$end; i++)); do printf "$KEYS_LEFT"; done

   # Save output to 3rd parameter variable
   eval "$3='`cat $tmp_file`'"

   # Display the command output to the screen
   # cat $tmp_file

   # Destroy / delete the temp file
   rm -rf $tmp_file
}

function __spinner() {
    local pid=$1
    local delay=0.75
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

function __ask_yes_or_no() {
    read -p "$1 ([y]es or [N]o): "
    case $(echo $REPLY | tr '[A-Z]' '[a-z]') in
        y|yes) echo "yes" ;;
        *)     echo "no" ;;
    esac
}

