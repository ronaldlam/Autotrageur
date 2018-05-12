#!/bin/bash

# Set the venv.
source scripts/venv_start.sh

# Run the main module.
python run_autotrageur.py encrypted-secret.txt 'oolong milk tea' pearls configs/dry_gem_bithumb_eth.yaml
