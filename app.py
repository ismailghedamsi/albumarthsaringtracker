from flask import Flask, request, jsonify, send_file, send_from_directory
import logging
from database import AlbumDatabase
from pathlib import Path
import os
import requests
from werkzeug.utils import secure_filename
from scanner import MusicScanner

app = Flask(__name__, static_folder='frontend/dist', template_folder='frontend/dist')
# Reduce default logging noise
logging.getLogger('werkzeug').setLevel(logging.WARNING)
app.logger.setLevel(logging.WARNING)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config.setdefault('DB_PATH', 'albums.db')

# Lazy initialization - db will be created when first accessed
_db = None

def get_db():
    """Get or create the database instance"""
    global _db
    if _db is None:
        db_path = app.config.get('DB_PATH', 'albums.db')
        _db = AlbumDatabase(db_path)
    return _db

# Create covers directory if it doesn't exist
covers_dir = Path("covers")
covers_dir.mkdir(exist_ok=True)

@app.route('/')
def index():
    """Main page displaying all albums"""
    return send_from_directory('frontend/dist', 'index.html')

@app.route('/api/albums')
def get_albums():
    """API endpoint to get all albums"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    search = request.args.get('search', '', type=str)
    filter_shared = request.args.get('filter_shared', '', type=str)
    
    albums = get_db().get_all_albums()
    
    # Apply filters
    if search:
        search_lower = search.lower()
        albums = [a for a in albums if 
                 search_lower in a['artist'].lower() or 
                 search_lower in a['album'].lower() or
                 (a['genre'] and search_lower in a['genre'].lower())]
    
    # Always exclude shared unless 'shared' is explicitly requested
    if filter_shared == 'shared':
        albums = [a for a in albums if a['shared']]
    else:
        albums = [a for a in albums if not a['shared']]
    
    # Pagination
    total = len(albums)
    start = (page - 1) * per_page
    end = start + per_page
    albums_page = albums[start:end]
    
    return jsonify({
        'albums': albums_page,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/albums/<int:album_id>/toggle_shared', methods=['POST'])
def toggle_shared(album_id):
    """Toggle the shared status of an album"""
    get_db().toggle_shared(album_id)
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    """Get statistics about the collection"""
    albums = get_db().get_all_albums()
    
    total_albums = len(albums)
    shared_albums = sum(1 for a in albums if a['shared'])
    albums_with_covers = sum(1 for a in albums if a['cover_path'])
    albums_without_covers = total_albums - albums_with_covers
    
    # Count unique artists
    unique_artists = len(set(a['artist'] for a in albums))
    
    return jsonify({
        'total_albums': total_albums,
        'shared_albums': shared_albums,
        'not_shared_albums': total_albums - shared_albums,
        'albums_with_covers': albums_with_covers,
        'albums_without_covers': albums_without_covers,
        'unique_artists': unique_artists
    })

@app.route('/api/rescan', methods=['POST'])
def rescan():
    """Rescan the music library and add any new albums.
    Existing albums are skipped (unique folder_path), preserving any cover_path set manually or via API.
    """
    music_root = app.config.get('MUSIC_ROOT', os.environ.get('MUSIC_ROOT', r"D:\\Music"))
    scanner = MusicScanner(music_root, get_db())
    added, skipped = scanner.scan()
    return jsonify({'success': True, 'added': added, 'skipped': skipped})

@app.route('/api/albums/<int:album_id>/update_cover', methods=['POST'])
def update_cover(album_id):
    """Update album cover from file upload or URL"""
    try:
        cover_source = request.form.get('source', 'file')
        
        if cover_source == 'file' and 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if file:
                # Create safe filename
                filename = secure_filename(f"album_{album_id}_{file.filename}")
                filepath = covers_dir / filename
                
                # Save file
                file.save(str(filepath))
                
                # Update database
                get_db().update_cover_path(album_id, str(filepath))
                
                return jsonify({'success': True, 'cover_path': str(filepath)})
        
        elif cover_source == 'url':
            # Handle URL download
            url = request.form.get('url', '')
            if not url:
                return jsonify({'success': False, 'error': 'No URL provided'}), 400
            
            # Download image from URL
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Determine file extension from URL or content type
            ext = '.jpg'
            if '.' in url:
                ext = '.' + url.rsplit('.', 1)[-1].split('?')[0].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    ext = '.jpg'
            
            filename = f"album_{album_id}_downloaded{ext}"
            filepath = covers_dir / filename
            
            # Save downloaded image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Update database
            get_db().update_cover_path(album_id, str(filepath))
            
            return jsonify({'success': True, 'cover_path': str(filepath)})
        
        elif cover_source == 'api':
            # Fetch from iTunes API
            albums = get_db().get_all_albums()
            album = next((a for a in albums if a['id'] == album_id), None)
            
            if not album:
                return jsonify({'success': False, 'error': 'Album not found'}), 404
            
            # Search iTunes API
            search_term = f"{album['artist']} {album['album']}"
            api_url = "https://itunes.apple.com/search"
            params = {
                'term': search_term,
                'media': 'music',
                'entity': 'album',
                'limit': 1
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['resultCount'] == 0:
                return jsonify({'success': False, 'error': 'No cover found on iTunes'}), 404
            
            # Get high-res artwork URL
            artwork_url = data['results'][0].get('artworkUrl100', '')
            
            if not artwork_url:
                return jsonify({'success': False, 'error': 'No artwork URL found on iTunes'}), 404
            
            # Upgrade to 600x600 resolution
            artwork_url = artwork_url.replace('100x100', '600x600')
            
            # Download image
            img_response = requests.get(artwork_url, timeout=15)
            img_response.raise_for_status()
            
            filename = f"album_{album_id}_itunes.jpg"
            filepath = covers_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # Update database
            get_db().update_cover_path(album_id, str(filepath))
            
            return jsonify({'success': True, 'cover_path': str(filepath)})
        
        return jsonify({'success': False, 'error': 'Invalid source'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cover/<path:cover_path>')
def serve_cover(cover_path):
    """Serve album cover image"""
    # Handle both absolute and relative paths
    if os.path.isabs(cover_path):
        if os.path.exists(cover_path):
            return send_file(cover_path)
    else:
        # Relative path from app directory
        full_path = Path(cover_path)
        if full_path.exists():
            return send_file(full_path)
    
    # Return placeholder if cover not found (use a generic image or return 404)
    # For now, just return 404 if cover doesn't exist
    return jsonify({'error': 'Cover not found'}), 404

@app.route('/static/<path:path>')
def serve_static_file(path):
    """Serve static files from the static directory"""
    try:
        return send_from_directory('static', path)
    except:
        return jsonify({'error': 'File not found'}), 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve React assets"""
    try:
        return send_from_directory('frontend/dist/assets', filename)
    except:
        return jsonify({'error': 'Asset not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
