#!/usr/bin/env bash
# A collection of utility environment vars, aliases and functions for Reach etc.
#
# Dev notes:
#    - Add "${@:N}" to the end of a function for dynamic parameters to be passed. Where N represents the optional parameter.
#    - Single quotes wont expand vars unless used in an alias. Use double quotes instead.

# ALIAS DEFINITIONS
############################

# Define the reach location and configuration you'd like to use here.
CHIEF_REACH_DIR="${CHIEF_PATH}/python/reach"
CHIEF_REACH_TOOL="${CHIEF_REACH_DIR}/reach.py"

alias chief.reach='$CHIEF_REACH_TOOL'

function chief.reach_search {
    USAGE="Usage: $FUNCNAME <command> <search string>

Find a string in the result of a command against the host fleet.
Note: You may pass Reach parameters to the end i.e. -f (filter) or -x (simulate) etc."
    if [[ -z $1 ]] || [[ -z $2 ]] || [[ $1 == "-?" ]]; then
        echo ${USAGE};
        return;
    fi
    __timer start

    echo "Executing \"$1\" against selected hosts.  Searching for: \"$2\"";

    # This script can also be customized to halt the search (hosts iteration) with -h when string is found on a host.
    chief.reach -c "$1" -s "$2"'|$NF' -r 'Found in Host: $HF_1 ($HF_3)|Not Found in Host: $HF_1 ($HF_3)' "${@:3}" | grep --color=never Found;

    __timer end
}

function chief.reach_passwd {
    USAGE="Change user password of the user defined in Reach.

Note: You may pass Reach parameters to the end i.e. -f (filter) or -x (simulate) etc.
Usage: $FUNCNAME <cipher-text current password> <cipher-text new password>"
    if [[ -z $1 ]] || [[ -z $2 ]] || [[ $1 == "-?" ]]; then
        echo ${USAGE};
        return;
    fi

    __timer start

    chief.reach -c 'passwd' -w 'current|New|Retype' -p '$CT='"$1"'|$CT='"$2"'|$CT='"$2" -s 'successfully' -r 'Changed password' "${@:3}"

    __timer end
}

