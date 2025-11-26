import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

class AlbumDatabase:
    def __init__(self, db_path: str = "albums.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre TEXT,
                artist TEXT NOT NULL,
                album TEXT NOT NULL,
                release_date TEXT,
                cover_path TEXT,
                shared BOOLEAN DEFAULT 0,
                display_order INTEGER,
                folder_path TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_artist ON albums(artist)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_display_order ON albums(display_order)
        """)
        
        conn.commit()
        conn.close()
    
    def add_album(self, genre: str, artist: str, album: str, folder_path: str,
                  release_date: Optional[str] = None, cover_path: Optional[str] = None) -> int:
        """Add a new album to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO albums (genre, artist, album, release_date, cover_path, folder_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (genre, artist, album, release_date, cover_path, folder_path))
            
            album_id = cursor.lastrowid
            conn.commit()
            return album_id
        except sqlite3.IntegrityError:
            # Album already exists
            return -1
        finally:
            conn.close()
    
    def update_cover_path(self, album_id: int, cover_path: str):
        """Update the cover path for an album"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE albums SET cover_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (cover_path, album_id))
        
        conn.commit()
        conn.close()
    
    def toggle_shared(self, album_id: int):
        """Toggle the shared status of an album"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE albums SET shared = NOT shared, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (album_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_albums(self, order_by: str = "display_order") -> List[Dict]:
        """Get all albums ordered by specified field"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM albums ORDER BY {order_by}
        """)
        
        albums = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return albums
    
    def get_albums_without_covers(self) -> List[Dict]:
        """Get all albums that don't have cover art"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM albums WHERE cover_path IS NULL OR cover_path = ''
        """)
        
        albums = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return albums
    
    def shuffle_display_order(self):
        """Shuffle albums so that same artists are not adjacent"""
        import random
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all albums grouped by artist
        cursor.execute("SELECT * FROM albums ORDER BY artist, album")
        albums = [dict(row) for row in cursor.fetchall()]
        
        if not albums:
            conn.close()
            return
        
        # Group albums by artist
        artist_albums = {}
        for album in albums:
            artist = album['artist']
            if artist not in artist_albums:
                artist_albums[artist] = []
            artist_albums[artist].append(album)
        
        # Distribute albums to avoid adjacency
        shuffled = []
        artist_queues = list(artist_albums.values())
        random.shuffle(artist_queues)
        
        while artist_queues:
            # Remove empty queues
            artist_queues = [q for q in artist_queues if q]
            if not artist_queues:
                break
            
            # Pick from a random queue
            queue = random.choice(artist_queues)
            album = queue.pop(0)
            
            # Try to avoid putting same artist consecutively
            if shuffled and shuffled[-1]['artist'] == album['artist'] and len(artist_queues) > 1:
                # Try to find a different artist
                other_queues = [q for q in artist_queues if q and q[0]['artist'] != album['artist']]
                if other_queues:
                    queue.insert(0, album)  # Put it back
                    queue = random.choice(other_queues)
                    album = queue.pop(0)
            
            shuffled.append(album)
        
        # Update display_order in database
        for order, album in enumerate(shuffled):
            cursor.execute("""
                UPDATE albums SET display_order = ? WHERE id = ?
            """, (order, album['id']))
        
        conn.commit()
        conn.close()
        
        print(f"Shuffled {len(shuffled)} albums")
    
    def get_album_count(self) -> int:
        """Get total number of albums in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM albums")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
