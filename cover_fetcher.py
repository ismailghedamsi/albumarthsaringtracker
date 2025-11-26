import requests
from pathlib import Path
from typing import Optional
from database import AlbumDatabase
import time

class CoverFetcher:
    def __init__(self, db: AlbumDatabase):
        self.db = db
        self.covers_dir = Path("covers")
        self.covers_dir.mkdir(exist_ok=True)
    
    def search_itunes(self, artist: str, album: str) -> Optional[str]:
        """Search iTunes API for album cover"""
        try:
            search_term = f"{artist} {album}"
            url = "https://itunes.apple.com/search"
            params = {
                'term': search_term,
                'media': 'music',
                'entity': 'album',
                'limit': 1
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['resultCount'] > 0:
                result = data['results'][0]
                return result.get('artworkUrl100', '').replace('100x100', '600x600')
            return None
        except Exception as e:
            print(f"Error searching iTunes for {artist} - {album}: {e}")
            return None
    
    def download_cover(self, url: str, album_id: int, artist: str, album: str) -> Optional[str]:
        """Download album cover from URL"""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Create filename from artist and album
            safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_album = "".join(c for c in album if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_artist}_{safe_album}_{album_id}.jpg"
            
            cover_path = self.covers_dir / filename
            
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            return str(cover_path)
        
        except Exception as e:
            print(f"Error downloading cover for {artist} - {album}: {e}")
            return None
    
    def fetch_missing_covers(self, limit: Optional[int] = None):
        """Fetch covers for all albums missing cover art"""
        albums = self.db.get_albums_without_covers()
        
        if not albums:
            print("No albums missing covers!")
            return
        
        total = len(albums)
        if limit:
            albums = albums[:limit]
        
        print(f"Found {total} albums without covers. Fetching covers for {len(albums)} albums...")
        
        success_count = 0
        failed_count = 0
        
        for i, album in enumerate(albums, 1):
            artist = album['artist']
            album_name = album['album']
            album_id = album['id']
            
            print(f"[{i}/{len(albums)}] Fetching cover for: {artist} - {album_name}")
            
            # Search for cover via iTunes
            artwork_url = self.search_itunes(artist, album_name)
            
            if artwork_url:
                # Download cover
                cover_path = self.download_cover(artwork_url, album_id, artist, album_name)
                
                if cover_path:
                    # Update database
                    self.db.update_cover_path(album_id, cover_path)
                    success_count += 1
                    print(f"  ✓ Downloaded cover")
                else:
                    failed_count += 1
                    print(f"  ✗ Failed to download")
            else:
                failed_count += 1
                print(f"  ✗ Cover not found")
            
            # Rate limiting - be nice to the API
            time.sleep(0.5)
        
        print(f"\nCover fetch complete!")
        print(f"Success: {success_count}")
        print(f"Failed: {failed_count}")

if __name__ == "__main__":
    import sys
    
    # Initialize database
    db = AlbumDatabase("albums.db")
    
    # Create cover fetcher
    fetcher = CoverFetcher(db)
    
    # Get limit from command line if provided
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Limiting to {limit} albums")
        except ValueError:
            print("Invalid limit, fetching all missing covers")
    
    # Fetch missing covers
    fetcher.fetch_missing_covers(limit=limit)
