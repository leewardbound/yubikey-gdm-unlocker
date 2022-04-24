#!/usr/bin/env bash

cd $(dirname $0)
source .envrc &>/dev/null

python3 yubikey_gdm_unlocker.py
