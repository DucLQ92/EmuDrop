#!/bin/sh
APP_DIR=$(dirname "$0")
cd "$APP_DIR"

# Ensure permissions
chmod +x app_ota.sh db_ota.sh EmuDrop assets/infoscreen.sh
# 7z/chdman/ccd2cue/ecm2bin ship without the bit set; extraction fails without this.
chmod -R +x assets/executables 2>/dev/null || true

# Logging setup
LOG_FILE="$APP_DIR/log.txt"
echo "Starting EmuDrop at $(date)" > "$LOG_FILE"
echo "Current directory: $PWD" >> "$LOG_FILE"

# Set library paths for NextUI
export LD_LIBRARY_PATH="$APP_DIR/lib:$LD_LIBRARY_PATH:/usr/lib:/lib"

# PySDL2 Path Setup
# Check for local lib folder first
if [ -d "$APP_DIR/lib" ] && [ "$(ls -A $APP_DIR/lib)" ]; then
    echo "Found local lib directory with files." >> "$LOG_FILE"
    export PYSDL2_DLL_PATH="$APP_DIR/lib"
elif [ -d "/usr/trimui/lib" ]; then
    echo "Found /usr/trimui/lib, using it for PySDL2." >> "$LOG_FILE"
    export PYSDL2_DLL_PATH="/usr/trimui/lib"
else
    echo "No specific lib dir found, defaulting to /usr/lib" >> "$LOG_FILE"
    export PYSDL2_DLL_PATH="/usr/lib"
fi

echo "PYSDL2_DLL_PATH: $PYSDL2_DLL_PATH" >> "$LOG_FILE"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH" >> "$LOG_FILE"

# Environment Variables
export ROMS_DIR="/mnt/SDCARD/Roms/"
export IMGS_DIR="/mnt/SDCARD/Roms/{SYSTEM}/.media/{IMAGE_NAME}.png"
export EXECUTABLES_DIR="$APP_DIR/assets/executables/"
export INFOSCREEN="/mnt/SDCARD/System/usr/trimui/scripts/infoscreen.sh"

if [ -f "$APP_DIR/assets/systems_nextui.json" ]; then
    cp "$APP_DIR/assets/systems_nextui.json" "$APP_DIR/assets/systems.json"
fi

# Show splash screen using NextUI show.elf
if [ -f "$APP_DIR/icon.png" ]; then
    # NextUI show.elf takes image path and delay in seconds
    if command -v show.elf >/dev/null 2>&1; then
        show.elf "$APP_DIR/icon.png" 1
    fi
fi

# Internet Check
if [ -f "$INFOSCREEN" ]; then
    $INFOSCREEN -m "Checking internet connection..." -t 0.2
    
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        $INFOSCREEN -m "Internet connection detected." -t 0.1
    else 
        $INFOSCREEN -m "No internet connection. Press B to exit." -k B
        exit
    fi
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

# Launch app (OTA updates disabled for custom build)
echo "Launching EmuDrop binary..." >> "$LOG_FILE"
./EmuDrop >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "EmuDrop exited with code $EXIT_CODE" >> "$LOG_FILE"

