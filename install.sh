#!/bin/bash

REQ_PYTHON_V="380"

ACTUAL_PYTHON_V=$(python -c 'import sys; version=sys.version_info[:3]; print("{0}{1}{2}".format(*version))')
ACTUAL_PYTHON3_V=$(python3 -c 'import sys; version=sys.version_info[:3]; print("{0}{1}{2}".format(*version))')

# 1. Check python version requirement
echo -e "1. Checking python version Requirements..."

if [[ $ACTUAL_PYTHON_V > $REQ_PYTHON_V ]] || [[ $ACTUAL_PYTHON_V == $REQ_PYTHON_V ]];  then
    PYTHON=python
elif [[ $ACTUAL_PYTHON3_V > $REQ_PYTHON_V ]] || [[ $ACTUAL_PYTHON3_V == $REQ_PYTHON_V ]]; then 
    PYTHON=python3
else
    echo -e "\tPython 3.8 is not installed on this machine. Please install Python 3.8 before continuing."
    exit 1
fi

echo -e "\t--Your python version is above 3.8, which is enough for this application."

# 2. What OS are we running on?
PLATFORM=$($PYTHON -c 'import platform; print(platform.system())')

echo -e $PLATFORM

echo -e "2. Checking OS Platform..."
echo -e "\t--OS=Platform=$PLATFORM"

# 3. Create Virtual environment
echo -e "3. Creating new virtual environment..."

# Remove the env directory if it exists 
if [[ -d env ]]; then
    echo -e "\t--Virtual Environment already exists. Deleting old one now."
    rm -rf env
fi

python3 -m venv env

if [[ ! -d env ]]; then
    echo -e "\t--Could not create virutal environment...Please make sure venv is installed"
    exit 1
fi

# 4. Install Requirements
echo -e "4. Installing Requirements..."
if [[ ! -e "requirements.txt" ]]; then 
    echo -e "\t--Need to requirements.txt to install packages."
    exit 1
fi

source env/bin/activate
pip3 install -r requirements.txt

echo -e "Install is complete."

# 5. Run the application
echo -e "5. Running the application..."
python3 app.py

# 6. Open the demopage
echo -e "6. Opening the demopage"

URL1=http://127.0.0.1:3003/
URL2=http://127.0.0.1:3004/

if [[ $PLATFORM == 'Linux' ]];  then
    xdg-open $URL1
    xdg-open $URL2
elif [[ $PLATFORM == 'Darwin' ]];  then
    open $URL1
    open $URL2
elif [[ $PLATFORM == 'Windows' ]];  then
    start $URL1
    start $URL2
else
    echo -e "Your OS is not supported."
    exit 1
fi
