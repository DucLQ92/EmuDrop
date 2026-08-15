#!/bin/bash
APP_DIR=$(dirname "$0")
cd $APP_DIR

chmod -R 777 .

export PYSDL2_DLL_PATH="/usr/trimui/lib/"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/SDCARD/System/lib/

if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "Internet connection detected."
else 
    echo "No internet connection. Press B to exit."
    exit
fi

# CPU Power Management: Use ondemand governor to keep CPU cool and save battery
if [ -f "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" ]; then
    echo ondemand > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || true
fi
if [ -f "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq" ]; then
    echo 408000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq 2>/dev/null || true
fi
if [ -d "/sys/devices/system/cpu/cpufreq/ondemand" ]; then
    echo 85 > /sys/devices/system/cpu/cpufreq/ondemand/up_threshold 2>/dev/null || true
fi

echo 1 > /tmp/stay_awake #keep screen awake

export ROMS_DIR="/mnt/SDCARD/Roms/"
export IMGS_DIR="/mnt/SDCARD/Imgs/{SYSTEM}/{IMAGE_NAME}.png"
export EXECUTABLES_DIR="$APP_DIR/assets/executables/"

"$APP_DIR/EmuDrop"
rm -f /tmp/stay_awake