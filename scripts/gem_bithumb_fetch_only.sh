#!/bin/bash

# Set the venv.
if source venv/Scripts/activate; then
    echo "Activated venv windows"
else
    source venv/bin/activate
    echo "Activated venv unix"
fi

# Run the main module.
python run_autotrageur.py <SECRET_KEY_FILE> configs/dry_gem_bithumb_eth.yaml
