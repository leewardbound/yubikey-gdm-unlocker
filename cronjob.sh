#!/usr/bin/env bash

cd $(dirname $0)

source .localenv

PYTHON="python3"
SCRIPT="yubikey_gdm_unlocker.py"
COMMAND="$PYTHON $SCRIPT"

ps -ef | grep $PYTHON | grep $SCRIPT && exit 1

echo "Running: $COMMAND"

nohup $COMMAND | tee -a /tmp/yubikey_gdm_unlocker.log &
