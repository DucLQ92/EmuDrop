#!/bin/bash
APP_DIR=$(dirname "$0")
cd $APP_DIR

chmod -R 777 .

export PYSDL2_DLL_PATH="/usr/trimui/lib/"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/SDCARD/System/lib/
export INFOSCREEN="/mnt/SDCARD/System/usr/trimui/scripts/infoscreen.sh"

$INFOSCREEN -m "Checking internet connection..." -t 0.2

if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    $INFOSCREEN -m "Internet connection detected." -t 0.1
else 
    $INFOSCREEN -m "No internet connection. Press B to exit." -k B
    exit
fi

# CPU Power Management: ondemand + 408MHz floor keeps the device cool while
# browsing. The originals are saved and restored on exit so whatever runs after
# EmuDrop (emulators, MainUI) does not inherit our settings.
GOV_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
MIN_FREQ_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq"
ORIG_GOV=""
ORIG_MIN_FREQ=""

restore_cpu() {
    if [ -n "$ORIG_GOV" ]; then
        echo "$ORIG_GOV" > "$GOV_PATH" 2>/dev/null || true
    fi
    if [ -n "$ORIG_MIN_FREQ" ]; then
        echo "$ORIG_MIN_FREQ" > "$MIN_FREQ_PATH" 2>/dev/null || true
    fi
}
trap restore_cpu EXIT

if [ -f "$GOV_PATH" ]; then
    ORIG_GOV=$(cat "$GOV_PATH" 2>/dev/null)
    echo ondemand > "$GOV_PATH" 2>/dev/null || true
fi
if [ -f "$MIN_FREQ_PATH" ]; then
    ORIG_MIN_FREQ=$(cat "$MIN_FREQ_PATH" 2>/dev/null)
    echo 408000 > "$MIN_FREQ_PATH" 2>/dev/null || true
fi
if [ -d "/sys/devices/system/cpu/cpufreq/ondemand" ]; then
    echo 85 > /sys/devices/system/cpu/cpufreq/ondemand/up_threshold 2>/dev/null || true
fi

# Network TCP Buffer & Performance Tuning for Fast WiFi Downloads
if [ -f "/proc/sys/net/core/rmem_max" ]; then
    echo 4194304 > /proc/sys/net/core/rmem_max 2>/dev/null || true
fi
if [ -f "/proc/sys/net/core/wmem_max" ]; then
    echo 4194304 > /proc/sys/net/core/wmem_max 2>/dev/null || true
fi
if [ -f "/proc/sys/net/ipv4/tcp_rmem" ]; then
    echo "4096 87380 4194304" > /proc/sys/net/ipv4/tcp_rmem 2>/dev/null || true
fi
if [ -f "/proc/sys/net/ipv4/tcp_wmem" ]; then
    echo "4096 65536 4194304" > /proc/sys/net/ipv4/tcp_wmem 2>/dev/null || true
fi
if [ -f "/proc/sys/net/ipv4/tcp_window_scaling" ]; then
    echo 1 > /proc/sys/net/ipv4/tcp_window_scaling 2>/dev/null || true
fi

echo 1 > /tmp/stay_awake #keep screen awake

export ROMS_DIR="/mnt/SDCARD/Roms/"
export IMGS_DIR="/mnt/SDCARD/Imgs/{SYSTEM}/{IMAGE_NAME}.png"
export EXECUTABLES_DIR="$APP_DIR/assets/executables/"

./EmuDrop
rm -f /tmp/stay_awake