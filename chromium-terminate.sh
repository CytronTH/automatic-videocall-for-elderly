#!/bin/bash

if ps aux | grep -q chromium; then
  pkill -f chromium
fi
