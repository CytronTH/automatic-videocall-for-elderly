#!/bin/bash

# Define Google Meet URL (replace with the specific meeting link)
MEET_URL="https://meet.google.com"

# Set Chromium path (adjust if different)
CHROMIUM_PATH="/usr/bin/chromium-browser --remote-debugging-port=9222 --start-maximized"
#CHROMIUM_PATH="/usr/bin/chromium-browser --remote-debugging-port=9222 --user-data-dir='/home/cytron/selenium-test/api'"
# Navigate to Google Meet URL
$CHROMIUM_PATH --app="$MEET_URL"



