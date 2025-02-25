#!/bin/bash

# Start Xvfb with display number 99
Xvfb :99 -screen 0 1920x1080x24 &
sleep 2  # Ensure Xvfb initializes

# Export the display variable to use the Xvfb display
export DISPLAY=:99
echo $DISPLAY

# Source env file to access env variables
source /home/dhon_bobis/shopee/.envrc

# Activate venv and run Shopee script
google-chrome & /home/dhon_bobis/shopee/venv/bin/python /home/dhon_bobis/shopee/pyauto_respondio.py >> /home/dhon_bobis/shopee/respondio_download_log.log 2>&1
