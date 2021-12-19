#!/usr/bin/env bash
# This is an optional collection of utility environment vars, aliases and functions for Reach etc.
#
# HOW TO USE THIS LIBRARY:
#
# OPTION 1:
#   - Simply source this library a you would any other bash file:
#     $> source <this file>
#
# OPTION 2:
#   - Download the bash library management tool Chief, and add a this file as a plugin.
#     https://github.com/randyoyarzabal/chief
#
# Dev notes:
#    - Add "${@:N}" to the end of a function for dynamic parameters to be passed. Where N represents the optional parameter.
#    - Single quotes wont expand vars unless used in an alias. Use double quotes instead.

# ALIAS DEFINITIONS
############################

# Define the reach location and configuration you'd like to use here.

# When running natively outside a container
# REACH_DIR="<local path of reach root dir>"
# REACH_TOOL="${REACH_DIR}/reach.py"

# When running in a container

# DEVELOPMENT ONLY
# Assumes docker image: "reach-dev" it pre-run
REACH_TOOL="docker exec -it reach-dev reach.py"

# GENERAL USE
# Ad-hoc
# REACH_TOOL="docker run --rm -it -v $REACH_PATH/configs:/reach/configs randyoyarzabal/reach reach.py"
# Pre-built container
# REACH_TOOL="docker exec -it reach reach.py"

alias reach='$REACH_TOOL'
alias reach.bash='docker exec -it reach-dev bash'

function reach.build {
    CONFIG_TEMPLATE="$REACH_PATH/configs/config.sample"
    CONFIG_FILE="$REACH_PATH/configs/config.ini"
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "Config file doesn't exist, copying from template..."
        cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
    fi
    if [[ -z $1 ]]; then
        echo "Building general-use Reach container..."
        docker build "$REACH_PATH" -t randyoyarzabal/reach
        docker run --rm -d -it -h reach -v $REACH_PATH/configs:/reach/configs --name=reach randyoyarzabal/reach
    else #any param will do - Development
        echo "Building development Reach container..."
        docker build . -t randyoyarzabal/reach:dev -f "$REACH_PATH/Dockerfile.develop"
        docker run --rm -d -it -h reach-dev -v $REACH_PATH:/reach --name=reach-dev randyoyarzabal/reach:dev
    fi
}

function reach.search {
    USAGE="Usage: $FUNCNAME <command> <search string>

Find a string in the result of a command against the host fleet.
Note: You may pass Reach parameters to the end i.e. -f (filter) or -x (simulate) etc."
    if [[ -z $1 ]] || [[ -z $2 ]] || [[ $1 == "-?" ]]; then
        echo ${USAGE}
        return
    fi
    __timer start

    echo "Executing \"$1\" against selected hosts.  Searching for: \"$2\""

    # This script can also be customized to halt the search (hosts iteration) with -h when string is found on a host.
    chief.reach -c "$1" -s "$2"'|$NF' -r 'Found in Host: $HF_1 ($HF_3)|Not Found in Host: $HF_1 ($HF_3)' "${@:3}" | grep --color=never Found

    __timer end
}

function reach.passwd {
    USAGE="Change user password of the user defined in Reach.

Note: You may pass Reach parameters to the end i.e. -f (filter) or -x (simulate) etc.
Usage: $FUNCNAME <cipher-text current password> <cipher-text new password>"
    if [[ -z $1 ]] || [[ -z $2 ]] || [[ $1 == "-?" ]]; then
        echo ${USAGE}
        return
    fi

    __timer start

    chief.reach -c 'passwd' -w 'current|New|Retype' -p '$CT='"$1"'|$CT='"$2"'|$CT='"$2" -s 'successfully' -r 'Changed password' "${@:3}"

    __timer end
}
