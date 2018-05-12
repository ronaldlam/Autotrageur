#!/bin/bash

# Set the venv.
if source venv/Scripts/activate; then
    echo "Activated venv windows"
else
    source venv/bin/activate
    echo "Activated venv unix"
fi