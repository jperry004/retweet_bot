#!/bin/bash

# This script runs a specified Python script and logs its output.
# The log is saved in a 'log' directory with a filename based on the current date and time.
#
# Usage:
#   ./script_name.sh script_name.py
#
# The script checks if a script name is provided as an argument. If not, it displays a usage message and exits.
# It then creates a 'log' directory if it doesn't already exist. The Python script is executed, and its output
# is both displayed on the console and saved to a log file named with the format MM-DD_HH.log in the 'log' directory.

# Get the current date and time in the format MM-DD_HH
DATE=$(date +%m-%d_%H)

# Create a log directory if it doesn't already exist
mkdir -p log

# Check if a script name was provided as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 script_name.py"
    exit 1
fi

# Run the Python script and redirect the output to a log file
python3 "$1" | tee log/$DATE.log
