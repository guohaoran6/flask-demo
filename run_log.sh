#!/bin/bash
shopt -s expand_aliases

alias grey-grep="GREP_COLOR='1;30' grep -E --color=always --line-buffered"
alias red-grep="GREP_COLOR='1;31' grep -E --color=always --line-buffered"
alias green-grep="GREP_COLOR='1;32' grep -E --color=always --line-buffered"
alias yellow-grep="GREP_COLOR='1;33' grep -E --color=always --line-buffered"
alias cyan-grep="GREP_COLOR='1;36' grep -E --color=always --line-buffered"
option=""

#!/bin/bash

while getopts ":t:f:p:" opt; do
  case $opt in
    t) types="$OPTARG"
    ;;
    f) filter="$OPTARG"
    ;;
    p) path="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [ -z "$path" ] ; then
  path="logs/app.logs"
fi

if [ -z "$types" ] || [ "$types" == "tail" ]; then
  types="tail"
  option="-f"
fi

"$types" "$option" "$path" | grey-grep "$filter" | cyan-grep "INFO|$" | yellow-grep "WARNING|$" | green-grep "Success|$" | red-grep "FAIL|$"| red-grep "[ERROR].*|[FATAL].*|$" | red-grep "*error*|$"| green-grep "***|$"
