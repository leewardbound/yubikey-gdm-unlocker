#!/usr/bin/env bash

echo "unlock.sh: $(date)"
sudo loginctl unlock-sessions

echo "unlock.sh: caffinate..."
caffeinate sleep 300
