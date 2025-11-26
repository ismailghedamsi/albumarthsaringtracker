import os
from pathlib import Path
from typing import Optional, Tuple
import mutagen
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from database import AlbumDatabase

class MusicScanner:
    def __init__(self, music_root: str, db: AlbumDatabase):
        self.music_root = Path(music_root)
        self.db = db
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    def find_album_cover(self, album_folder: Path) -> Optional[str]:
        """Find album cover in the album folder"""
        # Common cover art filenames
        cover_names = ['cover', 'folder', 'album', 'front', 'albumart', 'albumartsmall']
        
        # First, look for common filenames
        for cover_name in cover_names:
            for ext in self.image_extensions:
                cover_path = album_folder / f"{cover_name}{ext}"
                if cover_path.exists():
                    return str(cover_path)
        
        # If not found, look for any image file
        for file in album_folder.iterdir():
            if file.is_file() and file.suffix.lower() in self.image_extensions:
                return str(file)
        
        return None
    
    def extract_metadata_from_file(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """Extract genre and release date from audio file"""
        try:
            audio = mutagen.File(file_path, easy=True)
            if audio is None:
                return None, None
            
            genre = None
            release_date = None
            
            # Try to get genre
            if 'genre' in audio:
                genre = audio['genre'][0] if isinstance(audio['genre'], list) else audio['genre']
            
            # Try to get release date/year
            for date_tag in ['date', 'year', 'originaldate']:
                if date_tag in audio:
                    release_date = audio[date_tag][0] if isinstance(audio[date_tag], list) else audio[date_tag]
                    break
            
            return genre, release_date
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")
            return None, None
    
    def get_metadata_from_folder(self, album_folder: Path) -> Tuple[Optional[str], Optional[str]]:
        """Extract metadata from any audio file in the album folder"""
        audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        
        for file in album_folder.iterdir():
            if file.is_file() and file.suffix.lower() in audio_extensions:
                genre, release_date = self.extract_metadata_from_file(file)
                if genre or release_date:
                    return genre, release_date
        
        return None, None
    
    def scan(self):
        """Scan the music directory recursively and populate the database.
        Any directory containing audio files is considered an album folder.
        Artist and genre are inferred heuristically from parent folders or audio tags."""
        if not self.music_root.exists():
            print(f"Error: Music root directory does not exist: {self.music_root}")
            return
        
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"Scanning music directory recursively: {self.music_root}\n")
        
        # Audio file extensions to detect album folders
        audio_extensions = {'.mp3', '.flac', '.m4a', '.ogg', '.wav', '.wma', '.aac'}
        
        def folder_has_audio(folder: Path) -> bool:
            try:
                for entry in folder.iterdir():
                    if entry.is_file() and entry.suffix.lower() in audio_extensions:
                        return True
                return False
            except Exception:
                return False
        
        try:
            for dirpath, dirnames, filenames in os.walk(self.music_root):
                album_folder = Path(dirpath)
                # Quickly skip extremely deep system folders
                if album_folder.name.startswith('.'):
                    continue
                
                # Determine if this folder should be treated as an album
                contains_audio = any(Path(dirpath, f).suffix.lower() in audio_extensions for f in filenames)
                if not contains_audio:
                    continue
                
                try:
                    album_name = album_folder.name
                    cover_path = self.find_album_cover(album_folder)
                    
                    # Extract metadata from audio files (genre, release_date)
                    extracted_genre, release_date = self.get_metadata_from_folder(album_folder)
                    
                    # Heuristics for artist and genre from path
                    artist_name = album_folder.parent.name if album_folder.parent != album_folder else "Unknown Artist"
                    fallback_genre = album_folder.parent.parent.name if album_folder.parent.parent != album_folder.parent else None
                    final_genre = extracted_genre if extracted_genre else fallback_genre
                    
                    album_id = self.db.add_album(
                        genre=final_genre,
                        artist=artist_name,
                        album=album_name,
                        folder_path=str(album_folder),
                        release_date=release_date,
                        cover_path=cover_path
                    )
                    
                    if album_id > 0:
                        added_count += 1
                        if added_count % 200 == 0:
                            print(f"  Progress: {added_count} albums added...")
                    else:
                        skipped_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"  ERROR processing album folder {album_folder}: {e}")
        
        except Exception as e:
            print(f"\nFATAL ERROR during scan: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n" + "="*50)
        print(f"SCAN COMPLETE!")
        print(f"="*50)
        print(f"Added: {added_count} albums")
        print(f"Skipped (already exists): {skipped_count} albums")
        print(f"Errors: {error_count}")
        print(f"Total processed: {added_count + skipped_count}")
        
        if added_count > 0:
            print("\nShuffling album display order...")
            self.db.shuffle_display_order()
        
        return added_count, skipped_count

if __name__ == "__main__":
    # Initialize database
    db = AlbumDatabase("albums.db")
    
    # Scan music directory
    scanner = MusicScanner(r"D:\Music", db)
    scanner.scan()
