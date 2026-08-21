#!/bin/bash
# Absolute, so paths built from it keep working after the cd below.
APP_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$APP_DIR"

chmod -R 777 .

export PYSDL2_DLL_PATH="/usr/trimui/lib/"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/SDCARD/System/lib/

if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "Internet connection detected."
else 
    echo "No internet connection. Press B to exit."
    exit
fi

# CPU Power Management: ondemand + 408MHz floor keeps the device cool while
# browsing. The originals are saved and restored on exit so whatever runs after
# EmuDrop (emulators, MainUI) does not inherit our settings.
GOV_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
MIN_FREQ_PATH="/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq"
ORIG_GOV=""
ORIG_MIN_FREQ=""

WIFI_IF=""
ORIG_WIFI_PS=""
ORIG_TCP_CC=""

restore_system() {
    if [ -n "$ORIG_GOV" ]; then
        echo "$ORIG_GOV" > "$GOV_PATH" 2>/dev/null || true
    fi
    if [ -n "$ORIG_MIN_FREQ" ]; then
        echo "$ORIG_MIN_FREQ" > "$MIN_FREQ_PATH" 2>/dev/null || true
    fi
    if [ -n "$WIFI_IF" ] && [ -n "$ORIG_WIFI_PS" ]; then
        iw dev "$WIFI_IF" set power_save "$ORIG_WIFI_PS" 2>/dev/null || true
    fi
    if [ -n "$ORIG_TCP_CC" ]; then
        echo "$ORIG_TCP_CC" > /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null || true
    fi
}
trap restore_system EXIT

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

# WiFi power save parks the radio between beacons, which costs a lot of
# throughput on these modules. Off for the session, restored on exit.
if command -v iw >/dev/null 2>&1; then
    WIFI_IF=$(iw dev 2>/dev/null | awk '$1=="Interface"{print $2; exit}')
    if [ -n "$WIFI_IF" ]; then
        ORIG_WIFI_PS=$(iw dev "$WIFI_IF" get power_save 2>/dev/null | awk '{print $NF}')
        iw dev "$WIFI_IF" set power_save off 2>/dev/null || true
    fi
fi

# BBR holds up much better than cubic on a lossy wifi link. Only if the kernel
# actually ships it; most handheld kernels do not.
if [ -f "/proc/sys/net/ipv4/tcp_available_congestion_control" ]; then
    if grep -qw bbr /proc/sys/net/ipv4/tcp_available_congestion_control 2>/dev/null; then
        ORIG_TCP_CC=$(cat /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null)
        echo bbr > /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null || true
    fi
fi

echo 1 > /tmp/stay_awake #keep screen awake

export ROMS_DIR="/mnt/SDCARD/Roms/"
export IMGS_DIR="/mnt/SDCARD/Imgs/{SYSTEM}/{IMAGE_NAME}.png"
export EXECUTABLES_DIR="$APP_DIR/assets/executables/"

"$APP_DIR/EmuDrop"
rm -f /tmp/stay_awake