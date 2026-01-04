#!/bin/bash

# setup venv if not exists
if [ ! -d "venv" ]; then
    echo "creating virtual environment..."
    python3 -m venv venv
fi

# activate venv
source venv/bin/activate

# install dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install ics
fi

# run script
python3 src/quest2cal.py
