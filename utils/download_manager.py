import os
import shutil
import threading
import time
import json
from dataclasses import dataclass, fields
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.config import Config
from utils.logger import logger
from utils.screenscrapper import ScreenScraper
from utils.games_extractor_converter import GamesExtractorConverter


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
}

def create_optimized_session() -> Session:
    """Create requests Session configured for high-speed file transfers with connection pooling."""
    session = Session()
    adapter = HTTPAdapter(
        pool_connections=16,
        pool_maxsize=16,
        max_retries=Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


@dataclass
class GameProp:
    platform_id: str
    name: str
    game_url: str
    image_url: str
    isExtractable: bool
    canBeRenamed: bool
    source_name: str
    attributes: str


class DownloadManager:
    """Manages game downloads with multi-connection segmentation, progress tracking, and cancellation support."""

    # Class variable to track all download managers
    _all_managers = []
    
    def __init__(self, game: dict):
        """Initialize download manager for a specific game."""
        game_fields = {f.name for f in fields(GameProp)}
        filtered_data = {k: v for k, v in game.items() if k in game_fields}
        self.game_prop = GameProp(**filtered_data)
        
        for ch in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            self.game_prop.name = self.game_prop.name.replace(ch, '')
        
        self.download_path = os.path.join(Config.DOWNLOAD_DIR, self.game_prop.name)
        
        # Download state
        self.status = {
            "state": "queued",  # queued, downloading, processing, scraping, completed, error, cancelled
            "progress": 0,
            "total_size": 0,
            "current_size": 0,
            "download_speed": 0,
            "queue_position": 0,
            "current_operation": "",
            "error_message": "",
            "is_paused": False
        }
        
        # Control events
        self.cancel_download = threading.Event()
        self.pause_download = threading.Event()
        
        # Thread references
        self.download_url = None
        self.session = create_optimized_session()
        self.download_thread = None
        self.size_check_thread = None
        self.size_check_complete = threading.Event()
        self.size_check_error = None
        self.gameExtractorConverter = None
        self.filename = ""
        self._download_lock = threading.Lock()
        
    def add_manager(self):
        DownloadManager._all_managers.append(self)
        self._update_queue_positions()
        
    def _update_queue_positions(self):
        """Update queue positions for all queued downloads."""
        queued_managers = [m for m in DownloadManager._all_managers if m.status["state"] == "queued"]
        for i, manager in enumerate(queued_managers):
            manager.status["queue_position"] = i + 1

    def _get_download_url(self):
        if self.download_url:
            return self.download_url
            
        self.filename = self.get_file_name_from_url(self.game_prop.game_url)
        return self.game_prop.game_url
    
    def get_file_name_from_url(self, text):
        decode_map = {
            "%20": " ", "%21": "!", "%22": '"', "%23": "#", "%24": "$", "%25": "%", "%26": "&",
            "%27": "'", "%28": "(", "%29": ")", "%2A": "*", "%2B": "+", "%2C": ",", "%2D": "-",
            "%2E": ".", "%2F": "/", "%3A": ":", "%3B": ";", "%3C": "<", "%3D": "=", "%3E": ">",
            "%3F": "?", "%40": "@", "%5B": "[", "%5C": "\\", "%5D": "]", "%5E": "^", "%5F": "_",
            "%60": "`", "%7B": "{", "%7C": "|", "%7D": "}", "%7E": "~"
        }
        for encoded, decoded in decode_map.items():
            text = text.replace(encoded, decoded)
        
        file_name = text.split('/')[-1]
        return file_name

    def start_download(self):
        """Start downloading the game."""
        if self.status["state"] == "downloading":
            logger.warning("Download already in progress")
            return False
        
        download_url = self._get_download_url()
        if not download_url:
            logger.error("Could not retrieve download URL")
            self.status["state"] = "error"
            self.status["error_message"] = "Could not retrieve download URL"
            return False
        
        self.status.update({
            "state": "downloading",
            "progress": 0,
            "current_size": 0,
            "queue_position": 0,
            "error_message": "",
            "is_paused": False
        })
        
        self.cancel_download.clear()
        self._update_queue_positions()
        
        if os.path.exists(self.download_path):
            shutil.rmtree(self.download_path)
            
        os.makedirs(self.download_path, exist_ok=True)

        self.download_thread = threading.Thread(
            target=self._download_worker, 
            args=(download_url, )
        )
        self.download_thread.start()
        
        return True

    def pause(self):
        """Pause the ongoing download."""
        if self.status["state"] == "downloading":
            self.pause_download.set()
            self.status["is_paused"] = True
            logger.info(f"Download paused: {self.game_prop.name}")

    def resume(self):
        """Resume the paused download."""
        if self.status["state"] == "downloading" and self.status["is_paused"]:
            self.pause_download.clear()
            self.status["is_paused"] = False
            logger.info(f"Download resumed: {self.game_prop.name}")

    def _download_worker(self, download_url):
        """Background worker to download the game file with multi-segment acceleration when possible."""
        try:
            # 1. Initial probe request
            head_resp = self.session.get(download_url, stream=True, timeout=30)
            head_resp.raise_for_status()
            
            total_size = int(head_resp.headers.get('content-length', 0))
            self.status["total_size"] = total_size
            accept_ranges = head_resp.headers.get('accept-ranges', '').lower() == 'bytes'
            
            dest_file = os.path.join(self.download_path, self.filename)
            
            # Pre-allocate file on SD card to prevent filesystem fragmentation & boost write speed
            if total_size > 0:
                with open(dest_file, "wb") as f:
                    f.truncate(total_size)
            
            # Segmented multi-stream download threshold: files > 15MB that support Range requests
            NUM_STREAMS = 3
            use_segmented = (total_size >= 15 * 1024 * 1024 and accept_ranges)
            
            start_time = time.time()
            downloaded = 0
            
            if use_segmented:
                logger.info(f"Starting {NUM_STREAMS}-stream accelerated download for {self.game_prop.name} ({total_size // 1024 // 1024} MB)")
                part_size = total_size // NUM_STREAMS
                stream_threads = []
                stream_errors = []
                
                def part_worker(part_idx, start_byte, end_byte):
                    nonlocal downloaded
                    try:
                        part_headers = {"Range": f"bytes={start_byte}-{end_byte}"}
                        with self.session.get(download_url, headers=part_headers, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            with open(dest_file, "r+b") as pf:
                                pf.seek(start_byte)
                                for chunk in r.iter_content(chunk_size=131072):
                                    if self.cancel_download.is_set():
                                        return
                                    if self.pause_download.is_set():
                                        while self.pause_download.is_set() and not self.cancel_download.is_set():
                                            time.sleep(0.1)
                                        if self.cancel_download.is_set():
                                            return
                                    if chunk:
                                        pf.write(chunk)
                                        with self._download_lock:
                                            downloaded += len(chunk)
                                            self.status["current_size"] = downloaded
                                            self.status["progress"] = (downloaded / total_size * 100) if total_size > 0 else 0
                                            elapsed = time.time() - start_time
                                            if elapsed > 0:
                                                self.status["download_speed"] = downloaded / elapsed
                    except Exception as err:
                        stream_errors.append(err)
                        logger.warning(f"Segment {part_idx} download error: {err}")

                for i in range(NUM_STREAMS):
                    s_byte = i * part_size
                    e_byte = (total_size - 1) if i == NUM_STREAMS - 1 else ((i + 1) * part_size - 1)
                    t = threading.Thread(target=part_worker, args=(i, s_byte, e_byte))
                    t.daemon = True
                    t.start()
                    stream_threads.append(t)
                    
                for t in stream_threads:
                    t.join()
                    
                if self.cancel_download.is_set():
                    logger.info("Download cancelled")
                    return
                    
                if stream_errors:
                    raise RuntimeError(f"One or more download streams failed: {stream_errors[0]}")
            else:
                # High-speed single-stream download with 256KB memory buffer
                with open(dest_file, "wb" if total_size == 0 else "r+b") as file:
                    for chunk in head_resp.iter_content(chunk_size=262144):
                        if self.cancel_download.is_set():
                            logger.info("Download cancelled")
                            return
                        if self.pause_download.is_set():
                            while self.pause_download.is_set() and not self.cancel_download.is_set():
                                time.sleep(0.1)
                            if self.cancel_download.is_set():
                                return
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            elapsed = time.time() - start_time
                            self.status["current_size"] = downloaded
                            self.status["progress"] = (downloaded / total_size * 100) if total_size > 0 else 0
                            if elapsed > 0:
                                self.status["download_speed"] = downloaded / elapsed

            # Process the downloaded file if not cancelled
            if not self.cancel_download.is_set():
                self.status["progress"] = 100
                self.status["state"] = "processing"
                
                try:
                    self.gameExtractorConverter = GamesExtractorConverter(self.status, self.game_prop, self.download_path)
                    game_names_to_scrape = self.gameExtractorConverter.move_game()
                    logger.info(f"{self.game_prop.name} has been moved successfully")
                    
                    # Update status for scraping
                    self.status["state"] = "scraping"
                    self.status["current_operation"] = "Scraping Cover Images"
                    
                    scrapper = ScreenScraper()
                    for name in game_names_to_scrape:
                        if self.cancel_download.is_set():
                            return
                        message = scrapper.scrape_rom(self.game_prop.image_url, name, self.game_prop.platform_id)
                        logger.info(message)
                    
                    # Mark as completed
                    self.status["state"] = "completed"
                    self.status["current_operation"] = ""
                except Exception as e:
                    if self.cancel_download.is_set():
                        logger.info("Operation cancelled during processing")
                        return
                    raise e

        except Exception as e:
            if self.cancel_download.is_set():
                logger.info("Operation cancelled")
                return
            logger.error(f"Download failed: {e}")
            self.status["state"] = "error"
            self.status["error_message"] = str(e)
        
        finally:
            if not self.cancel_download.is_set():
                try:
                    shutil.rmtree(self.download_path)
                except Exception as e:
                    logger.error(f"Error cleaning up download directory: {e}")

    def cancel(self):
        """Cancel the ongoing download."""
        self.status['state'] = "cancelling"
        
        if self.gameExtractorConverter is not None:
            try:
                self.gameExtractorConverter.cancel()
            except Exception as e:
                logger.error(f"Error cancelling extraction: {e}")
        
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_download.set()
            try:
                self.download_thread.join(timeout=5)
            except Exception as e:
                logger.error(f"Error waiting for download thread: {e}")
        
        try:
            if os.path.exists(self.download_path):
                shutil.rmtree(self.download_path)
        except Exception as e:
            logger.error(f"Error cleaning up download directory: {e}")

        if self in DownloadManager._all_managers:
            DownloadManager._all_managers.remove(self)
                
        self._update_queue_positions()
        self.status['state'] = "cancelled"
        self.status['current_operation'] = ""

    @staticmethod
    def format_size(size_bytes):
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def get_disk_space():
        """Get disk space information for the given path."""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(os.path.dirname(Config.DOWNLOAD_DIR)),
                    None,
                    ctypes.pointer(total_bytes),
                    ctypes.pointer(free_bytes)
                )
                return total_bytes.value, free_bytes.value
            else:  # Unix/Linux/macOS
                st = os.statvfs(os.path.dirname(Config.DOWNLOAD_DIR))
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                return total, free
        except Exception as e:
            logger.error(f"Error getting disk space: {e}")
            return 0, 0

    def get_game_size_async(self):
        """Start asynchronous game size check."""
        if self.size_check_thread and self.size_check_thread.is_alive():
            return
            
        self.size_check_complete.clear()
        self.size_check_error = None
        self.size_check_thread = threading.Thread(target=self._size_check_worker)
        self.size_check_thread.daemon = True
        self.size_check_thread.start()

    def _size_check_worker(self):
        """Background worker for checking game size."""
        try:
            download_url = self._get_download_url()
            if not download_url:
                self.size_check_error = "Could not get download URL"
                return
            
            response = self.session.head(download_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                self.status["total_size"] = int(response.headers.get('content-length', 0))
            else:
                self.size_check_error = f"HTTP error: {response.status_code}"
        except Exception as e:
            logger.error(f"Error getting game size: {e}")
            self.size_check_error = str(e)
        finally:
            self.size_check_complete.set()

    def wait_for_size(self, timeout=None):
        """Wait for size check to complete."""
        if not self.size_check_thread:
            return False
            
        self.size_check_complete.wait(timeout)
        return not bool(self.size_check_error)
    
    @classmethod
    def get_active_download_count(cls):
        """Get the number of active downloads."""
        return sum(1 for m in cls._all_managers if m.status["state"] in ["downloading", "processing", "scraping"])
