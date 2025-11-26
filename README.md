# Album Collection Manager

A Python Flask + React web application to browse, manage, and share your music collection with album covers.

## Features

- 📁 **Automatic Scanning**: Recursively scans your music directory structure
- 👁️ **Live Detection**: Automatically detects and adds new albums as you add them to your library
- 🎨 **Album Covers**: Automatically finds existing covers or fetches missing ones via Cover Art Archive (MusicBrainz)
- 🔀 **Smart Shuffling**: Distributes albums so same artists aren't displayed next to each other
- 🗄️ **Database Persistence**: SQLite database for fast access and persistence
- ✅ **Shared Tracking**: Mark albums as shared with checkbox indicators
- 🔍 **Search & Filter**: Search by artist, album, or genre; filter by shared status
- 📊 **Statistics**: View collection stats (total albums, artists, shared count)
- 📱 **Responsive Grid**: Beautiful, responsive layout optimized for large collections (5000+ albums)

## Directory Structure

Your music should be organized as:
```
D:\Music\
├── a\              # Genre folders (a-z, 0-9, special characters)
│   ├── t\          # Artist first letter
│   │   ├── Tech N9ne\
│   │   │   ├── Album 1\
│   │   │   │   ├── cover.jpg
│   │   │   │   ├── track1.mp3
│   │   │   │   └── ...
│   │   │   └── Album 2\
│   │   └── ...
│   └── ...
└── ...
```

## Setup

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Build the React Frontend**:
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

4. **Run (Single Command)**:
   ```bash
   python main.py
   ```
   This will:
   - Start the web server at `http://localhost:5001`
   - Start watching your music library for new albums
   - Use the rescan button in the UI to initially populate your collection

**For Development**: Run the React dev server on port 3000 for hot reloading:
```bash
cd frontend
npm run dev
```
Then run Flask separately:
```bash
python app.py
```

5. **Fetch Missing Album Covers** (optional):
   ```bash
   # Fetch all missing covers from Cover Art Archive
   python cover_fetcher.py
   
   # Or limit to first 100 albums
   python cover_fetcher.py 100
   ```

6. **Configuration (optional)**:
   Set environment variables to override defaults (no arguments needed):
   ```bash
   # PowerShell
   $env:MUSIC_ROOT="E:\\Media\\Music"; $env:DB_PATH="C:\\data\\albums.db"; $env:PORT="8080"; python main.py
   
   # Disable auto-detection (if desired)
   $env:ENABLE_WATCHER="false"; python main.py
   ```

## Usage

### Web Interface

- **Browse Albums**: Scroll through your shuffled collection
- **Search**: Type artist, album, or genre name
- **Filter**: Show only shared or not-shared albums
- **Mark as Shared**: Click checkbox to track albums you've shared online
- **Pagination**: Navigate through large collections with page controls

### Legacy Scripts
You can still run individual scripts if desired:
```bash
python scanner.py
python cover_fetcher.py [limit]
python app.py
```

## Database Schema

SQLite database (`albums.db`) contains:
- **genre**: Album genre
- **artist**: Artist name
- **album**: Album title
- **release_date**: Release date/year
- **cover_path**: Path to album cover image
- **shared**: Boolean flag for shared status
- **display_order**: Shuffled order for display
- **folder_path**: Full path to album folder

## API Endpoints

- `GET /`: Main web interface
- `GET /api/albums`: Get paginated albums with search/filter
- `POST /api/albums/<id>/toggle_shared`: Toggle shared status
- `GET /api/stats`: Get collection statistics
- `GET /cover/<path>`: Serve album cover image

## Configuration

Prefer environment variables with `main.py`:
- **MUSIC_ROOT**: Path to music library (default `D:\\Music`)
- **DB_PATH**: Path to sqlite database (default `albums.db`)
- **HOST/PORT**: Server address (defaults `0.0.0.0:5001`)
- **ENABLE_WATCHER**: Enable/disable auto-detection (default `true`)

## Tips

- **Auto-detection**: New albums are automatically detected when added to your music library
- **Re-scanning**: Use the rescan button in the UI or running scanner again will skip existing albums
- **Re-shuffling**: Call `db.shuffle_display_order()` to re-shuffle
- **Backup**: SQLite database is in `albums.db` - back it up regularly
- **Placeholders**: Add `placeholder.png` in `static/` folder for missing covers

## Troubleshooting

- **No covers found**: Check that your album folders contain image files (jpg, png, etc.)
- **Cover fetcher fails**: iTunes API has rate limits; script includes 0.5s delay between requests
- **Slow loading**: Reduce `per_page` in `app.py` or use pagination
- **Database locked**: Close other connections to `albums.db`

Enjoy managing your music collection! 🎵
