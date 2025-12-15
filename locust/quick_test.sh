#!/bin/bash
# Quick test launcher - automatically activates venv and runs test

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the test scenario
./test_scenarios.sh "$@"
