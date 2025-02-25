#!/bin/bash

# Start Xvfb with display number 99
Xvfb :99 -screen 0 1920x1080x24 &

# Export the display variable to use the Xvfb display
export DISPLAY=:99

# source env file to access env variables
source /home/dhon_bobis/shopee/.envrc

# activate venv and run shopee script
/home/dhon_bobis/shopee/venv/bin/python /home/dhon_bobis/shopee/sel_shopee.py >> /home/dhon_bobis/shopee/shopee_cron_sh_log.log 2>&1