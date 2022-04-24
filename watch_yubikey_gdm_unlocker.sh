#!/bin/sh
watch "ps -ef | grep -e '\(yubikey_gdm_unlocker\|caffeinate\)' | grep -v grep"
