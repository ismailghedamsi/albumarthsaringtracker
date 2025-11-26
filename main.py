import os
from pathlib import Path
from database import AlbumDatabase
from scanner import MusicScanner
from watcher import start_watcher


def run_scan(music_root: str, db_path: str) -> None:
    db = AlbumDatabase(db_path)
    scanner = MusicScanner(music_root, db)
    scanner.scan()


def run_server(db_path: str, host: str, port: int, debug: bool, music_root: str, enable_watcher: bool = True) -> None:
    # Lazy import to prevent Flask dependency for pure scan usage
    from app import app
    app.config['DB_PATH'] = db_path
    # Ensure MUSIC_ROOT available to app endpoints (e.g., rescan)
    if 'MUSIC_ROOT' not in app.config:
        app.config['MUSIC_ROOT'] = music_root
    
    # Start file watcher if enabled
    watcher = None
    if enable_watcher:
        db = AlbumDatabase(db_path)
        watcher = start_watcher(music_root, db, scan_delay=5)
    
    # Disable auto-reloader to avoid duplicate logs and infinite startup loops
    try:
        app.run(debug=debug, host=host, port=port, use_reloader=False)
    finally:
        # Clean up watcher on shutdown
        if watcher:
            watcher.stop()
            watcher.join()


def main() -> None:
    # Zero-argument entrypoint. Configure via environment variables if needed.
    music_root = os.environ.get("MUSIC_ROOT", r"D:\\Music")
    db_path = os.environ.get("DB_PATH", "albums.db")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("DEBUG", "false").lower() in {"1", "true", "yes"}
    enable_watcher = os.environ.get("ENABLE_WATCHER", "true").lower() in {"1", "true", "yes"}

    # Do not scan on startup; only via the UI button/endpoint.
    # Ensure MUSIC_ROOT is available to the Flask app for on-demand rescans.
    os.environ["MUSIC_ROOT"] = music_root
    run_server(db_path, host, port, debug, music_root, enable_watcher)


if __name__ == "__main__":
    main()
