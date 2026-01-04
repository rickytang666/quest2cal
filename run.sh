#!/bin/bash

# setup venv if not exists
if [ ! -d "venv" ]; then
    echo "creating virtual environment..."
    python3 -m venv venv
fi

# activate venv
source venv/bin/activate

# install dependencies
# check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    pip install ics -q
fi

# run script with arguments
python3 src/main.py "$@"
