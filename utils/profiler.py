"""
Performance & Hardware Diagnostic Profiler for EmuDrop.
Monitors CPU Temperature, Frequency, Frame Render Timing, and System Resource Utilization.
"""
import os
import time
from typing import Dict, Any, Tuple
from utils.logger import logger


class PerformanceProfiler:
    """Monitors and logs real-time hardware metrics (CPU Temp, Frequency, Render Pacing)."""
    
    _instance = None
    
    def __init__(self):
        self.last_log_time = time.time()
        self.log_interval = 10.0  # Log summary every 10 seconds
        
        self.frame_count = 0
        self.total_frame_cpu_time = 0.0
        self.total_sleep_time = 0.0
        self.max_frame_cpu_time = 0.0
        
        self.cached_temp = "N/A"
        self.cached_freq = "N/A"
        self.cached_governor = "N/A"
        self.last_hw_check = 0.0
        
    @classmethod
    def get_instance(cls) -> 'PerformanceProfiler':
        if cls._instance is None:
            cls._instance = PerformanceProfiler()
        return cls._instance
        
    def read_cpu_temp(self) -> str:
        """Read Allwinner A133P / Linux CPU temperature in °C."""
        temp_paths = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/devices/virtual/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
            "/sys/class/hwmon/hwmon1/temp1_input",
        ]
        for p in temp_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        raw = f.read().strip()
                        val = float(raw)
                        if val > 1000:
                            val /= 1000.0
                        return f"{val:.1f}°C"
                except Exception:
                    pass
        return "N/A"
        
    def read_cpu_freq(self) -> Tuple[str, str]:
        """Read CPU frequency (MHz) and governor."""
        freq_str = "N/A"
        gov_str = "N/A"
        
        freq_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        gov_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        
        if os.path.exists(freq_path):
            try:
                with open(freq_path, "r") as f:
                    raw = int(f.read().strip())
                    freq_str = f"{raw // 1000} MHz"
            except Exception:
                pass
                
        if os.path.exists(gov_path):
            try:
                with open(gov_path, "r") as f:
                    gov_str = f.read().strip()
            except Exception:
                pass
                
        return freq_str, gov_str

    def record_frame(self, cpu_work_time_ms: float, sleep_time_ms: float, is_active: bool = True) -> None:
        """Record timing for a completed frame and periodically log metrics."""
        self.frame_count += 1
        self.total_frame_cpu_time += cpu_work_time_ms
        self.total_sleep_time += sleep_time_ms
        if cpu_work_time_ms > self.max_frame_cpu_time:
            self.max_frame_cpu_time = cpu_work_time_ms
            
        now = time.time()
        if now - self.last_log_time >= self.log_interval:
            # Refresh HW metrics
            self.cached_temp = self.read_cpu_temp()
            self.cached_freq, self.cached_governor = self.read_cpu_freq()
            
            avg_cpu = (self.total_frame_cpu_time / max(1, self.frame_count))
            avg_sleep = (self.total_sleep_time / max(1, self.frame_count))
            actual_fps = self.frame_count / max(0.001, (now - self.last_log_time))
            
            # CPU load percentage approximation
            total_time = avg_cpu + avg_sleep
            cpu_load_pct = (avg_cpu / total_time * 100.0) if total_time > 0 else 0.0
            
            logger.info(
                f"[PERF_DIAG] Temp: {self.cached_temp} | "
                f"Freq: {self.cached_freq} ({self.cached_governor}) | "
                f"CPU Load: {cpu_load_pct:.1f}% | "
                f"Frame Work: {avg_cpu:.2f}ms (Peak: {self.max_frame_cpu_time:.2f}ms) | "
                f"Sleep: {avg_sleep:.2f}ms | "
                f"FPS: {actual_fps:.1f} | "
                f"Active: {is_active}"
            )
            
            # Reset counters
            self.last_log_time = now
            self.frame_count = 0
            self.total_frame_cpu_time = 0.0
            self.total_sleep_time = 0.0
            self.max_frame_cpu_time = 0.0

    def get_hardware_status(self) -> Dict[str, str]:
        """Get cached or latest hardware status for UI display."""
        now = time.time()
        if now - self.last_hw_check >= 2.0:
            self.cached_temp = self.read_cpu_temp()
            self.cached_freq, self.cached_governor = self.read_cpu_freq()
            self.last_hw_check = now
            
        return {
            "temp": self.cached_temp,
            "freq": self.cached_freq,
            "governor": self.cached_governor
        }


profiler = PerformanceProfiler.get_instance()
