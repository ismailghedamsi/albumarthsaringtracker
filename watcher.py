import os
import threading
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scanner import MusicScanner
from database import AlbumDatabase


class AlbumWatcher(FileSystemEventHandler):
    """Watch for new album folders in the music directory"""
    
    def __init__(self, music_root: str, db: AlbumDatabase, scan_delay: int = 5):
        """
        Args:
            music_root: Path to the music directory
            db: Database instance
            scan_delay: Delay in seconds before triggering a scan after a change
        """
        self.music_root = Path(music_root)
        self.db = db
        self.scan_delay = scan_delay
        self.audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        self.changes_detected = False
        self.last_change_time = 0
        self.scan_lock = threading.Lock()
        self.observed_paths = set()
        
        # Start background thread to debounce changes
        self.scan_thread = threading.Thread(target=self._debounced_scan, daemon=True)
        self.scan_thread.start()
    
    def _has_audio_files(self, path: Path) -> bool:
        """Check if a directory contains audio files"""
        try:
            if not path.is_dir():
                return False
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix.lower() in self.audio_extensions:
                    return True
            return False
        except (PermissionError, OSError):
            return False
    
    def _is_album_folder(self, path: Path) -> bool:
        """Determine if a path is a potential album folder"""
        # Must be a directory
        if not path.is_dir():
            return False
        
        # Check if it contains audio files
        if self._has_audio_files(path):
            return True
        
        # Check if any subdirectories contain audio files
        try:
            for entry in path.iterdir():
                if entry.is_dir() and self._has_audio_files(entry):
                    return True
        except (PermissionError, OSError):
            pass
        
        return False
    
    def on_created(self, event):
        """Handle file/directory creation events"""
        if event.is_directory:
            self._handle_change(Path(event.src_path))
    
    def on_moved(self, event):
        """Handle file/directory move events"""
        if event.is_directory and event.dest_path:
            self._handle_change(Path(event.dest_path))
    
    def _handle_change(self, path: Path):
        """Handle a filesystem change"""
        # Only watch paths within the music root
        try:
            path = path.resolve()
            if not self._is_within_music_root(path):
                return
            
            # Check if this is a potential album folder
            if self._is_album_folder(path):
                with self.scan_lock:
                    self.changes_detected = True
                    self.last_change_time = time.time()
                    print(f"New album folder detected: {path.name}")
        except (PermissionError, OSError, ValueError):
            pass
    
    def _is_within_music_root(self, path: Path) -> bool:
        """Check if path is within the music root directory"""
        try:
            return str(path).startswith(str(self.music_root.resolve()))
        except:
            return False
    
    def _debounced_scan(self):
        """Background thread that waits for changes to settle before scanning"""
        while True:
            time.sleep(1)  # Check every second
            
            with self.scan_lock:
                if self.changes_detected and (time.time() - self.last_change_time) >= self.scan_delay:
                    print(f"\n{'='*60}")
                    print("AUTO-SCANNING: Detected new albums in music library...")
                    print(f"{'='*60}")
                    
                    # Perform incremental scan
                    scanner = MusicScanner(str(self.music_root), self.db)
                    added, skipped = scanner.scan()
                    
                    if added > 0:
                        print(f"✓ Auto-added {added} new album(s)")
                    else:
                        print("✓ No new albums to add")
                    
                    self.changes_detected = False


def start_watcher(music_root: str, db: AlbumDatabase, scan_delay: int = 5) -> Observer:
    """
    Start watching the music directory for new albums
    
    Args:
        music_root: Path to the music directory
        db: Database instance
        scan_delay: Delay in seconds before triggering a scan after a change
    
    Returns:
        Observer instance that is running in a background thread
    """
    if not os.path.exists(music_root):
        print(f"Warning: Music root directory does not exist: {music_root}")
        return None
    
    event_handler = AlbumWatcher(music_root, db, scan_delay)
    observer = Observer()
    observer.schedule(event_handler, music_root, recursive=True)
    observer.start()
    
    print(f"✓ Started watching music library: {music_root}")
    print(f"✓ Auto-scan will trigger {scan_delay}s after changes are detected")
    
    return observer


if __name__ == "__main__":
    # Test the watcher
    import sys
    
    music_root = sys.argv[1] if len(sys.argv) > 1 else r"D:\Music"
    db_path = "albums.db"
    
    db = AlbumDatabase(db_path)
    observer = start_watcher(music_root, db, scan_delay=5)
    
    if observer:
        try:
            # Keep the watcher running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
            print("\nWatcher stopped.")

