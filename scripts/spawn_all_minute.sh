#!/bin/bash

set +o history

# Set the venv.
source scripts/venv_start.sh

DBFILE="$1"

# Read user-inputted password and salt.
echo Password:
read -s PASSWORD
echo Salt:
read -s SALT

# Run minute scripts, per exchange, parallel - max 5 pairs.
shopt -s globstar
script_count=0
for dir in configs/fetch_rpi/*/; do
    for file in $dir/minute/*; do
        ((script_count++))
        yes | python analytics/history_to_db.py "$file" "$DBFILE" "$PASSWORD" "$SALT" &

        if [ $script_count -eq 5 ]; then
            echo "Script count at 5"
            wait
            script_count=0
        fi
    done
done

wait
shopt -u globstar
set -o history