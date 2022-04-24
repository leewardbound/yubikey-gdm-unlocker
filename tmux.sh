#!/bin/sh
cd $(dirname $0)
TMUX_SESSION='yubikey_gdm_unlocker'
LOGS='journalctl -u yubikey_gdm_unlocker -f --since "1 hour ago"'
PROCESSES='bash ./watch_yubikey_gdm_unlocker.sh'

tmux new -s $TMUX_SESSION -d "$PROCESSES"
tmux split-window -h "$LOGS"
tmux attach -d -t $TMUX_SESSION
