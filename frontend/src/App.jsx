import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [albums, setAlbums] = useState([]);
  const [stats, setStats] = useState({
    total_albums: 0,
    unique_artists: 0,
    shared_albums: 0
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [filterShared, setFilterShared] = useState('');
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [currentAlbumId, setCurrentAlbumId] = useState(null);
  const [activeTab, setActiveTab] = useState('file');
  const [rescanLoading, setRescanLoading] = useState(false);
  const perPage = 100;

  useEffect(() => {
    loadStats();
    loadAlbums(1);
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get('/api/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const loadAlbums = async (page = 1) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/albums?page=${page}&per_page=${perPage}&search=${encodeURIComponent(search)}&filter_shared=${filterShared}`);
      setAlbums(response.data.albums);
      setCurrentPage(response.data.page);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Error loading albums:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadAlbums(1);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const toggleShared = async (albumId, event) => {
    event.stopPropagation();
    
    try {
      // Save current scroll position
      const scrollPosition = window.scrollY;
      
      const response = await axios.post(`/api/albums/${albumId}/toggle_shared`);
      
      if (response.status === 200) {
        // Remove the album from the list
        setAlbums(albums.filter(album => album.id !== albumId));
        loadStats();
        
        // Restore scroll position after a brief delay
        setTimeout(() => {
          window.scrollTo(0, scrollPosition);
        }, 50);
      }
    } catch (error) {
      console.error('Error toggling shared status:', error);
    }
  };

  const openModal = (albumId) => {
    setCurrentAlbumId(albumId);
    setModalOpen(true);
    setActiveTab('file');
  };

  const closeModal = () => {
    setModalOpen(false);
    setCurrentAlbumId(null);
  };

  const triggerRescan = async () => {
    setRescanLoading(true);
    try {
      const response = await axios.post('/api/rescan');
      if (response.data.success) {
        loadStats();
        loadAlbums(1);
        alert(`Rescan complete. Added: ${response.data.added}, Skipped: ${response.data.skipped}`);
      } else {
        alert('Rescan failed');
      }
    } catch (error) {
      console.error('Rescan error', error);
      alert('Rescan failed');
    } finally {
      setRescanLoading(false);
    }
  };

  const uploadCoverFile = async () => {
    const fileInput = document.getElementById('coverFile');
    const file = fileInput.files[0];

    if (!file) {
      alert('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', 'file');

    await uploadCover(formData);
  };

  const uploadCoverUrl = async () => {
    const url = document.getElementById('coverUrl').value.trim();

    if (!url) {
      alert('Please enter a URL');
      return;
    }

    const formData = new FormData();
    formData.append('url', url);
    formData.append('source', 'url');

    await uploadCover(formData);
  };

  const uploadCoverApi = async () => {
    const formData = new FormData();
    formData.append('source', 'api');

    await uploadCover(formData);
  };

  const uploadCover = async (formData) => {
    try {
      const response = await axios.post(`/api/albums/${currentAlbumId}/update_cover`, formData);
      
      if (response.data.success) {
        // Reload albums to get updated cover
        loadAlbums(currentPage);
        closeModal();
        alert('Cover updated successfully!');
      } else {
        alert(`Error: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Error uploading cover:', error);
      alert('Failed to upload cover');
    }
  };

  const getCurrentAlbum = () => {
    return albums.find(a => a.id === currentAlbumId);
  };

  return (
    <div className="container">
      <header>
        <h1>🎵 Album Collection</h1>
        
        <div className="stats">
          <div className="stat-card">
            <strong>{stats.total_albums}</strong>
            <span>Total Albums</span>
          </div>
          <div className="stat-card">
            <strong>{stats.unique_artists}</strong>
            <span>Unique Artists</span>
          </div>
          <div className="stat-card">
            <strong>{stats.shared_albums}</strong>
            <span>Shared Albums</span>
          </div>
        </div>

        <div className="controls">
          <input 
            type="text" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search by artist, album, or genre..." 
          />
          <select 
            value={filterShared}
            onChange={(e) => setFilterShared(e.target.value)}
          >
            <option value="">Not Shared</option>
            <option value="shared">Shared Only</option>
          </select>
          <button onClick={handleSearch}>Search</button>
          <button onClick={triggerRescan} disabled={rescanLoading}>
            {rescanLoading ? 'Rescanning...' : 'Rescan Library'}
          </button>
        </div>
      </header>

      <div className="album-grid">
        {loading ? (
          <div className="loading">Loading albums...</div>
        ) : albums.length === 0 ? (
          <div className="no-results">No albums found</div>
        ) : (
          albums.map(album => (
            <div key={album.id} className="album-card">
              {album.shared && <div className="shared-badge">✓ Shared</div>}
              <img 
                src={album.cover_path ? `/cover/${encodeURIComponent(album.cover_path)}` : '/static/placeholder.svg'} 
                alt={album.album} 
                className="album-cover" 
                onError={(e) => { 
                  if (!e.target.src.includes('placeholder.svg')) {
                    e.target.src = '/static/placeholder.svg';
                  }
                }}
                onClick={() => openModal(album.id)}
              />
              <div className="album-info">
                <div className="album-artist">{album.artist}</div>
                <div className="album-title">{album.album}</div>
                <div className="album-meta">
                  <span className="album-genre">{album.genre || 'Unknown'}</span>
                  <span className="album-year">{album.release_date || '-'}</span>
                </div>
                <div className="album-meta">
                  <label>
                    <input 
                      type="checkbox" 
                      className="share-checkbox" 
                      checked={album.shared} 
                      onChange={(e) => toggleShared(album.id, e)}
                    />
                    Mark as Shared
                  </label>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => loadAlbums(currentPage - 1)} disabled={currentPage === 1}>«</button>
          
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNum;
            if (totalPages <= 5) {
              pageNum = i + 1;
            } else if (currentPage <= 3) {
              pageNum = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i;
            } else {
              pageNum = currentPage - 2 + i;
            }
            
            return (
              <button 
                key={pageNum}
                onClick={() => loadAlbums(pageNum)} 
                className={pageNum === currentPage ? 'active' : ''}
              >
                {pageNum}
              </button>
            );
          })}
          
          <button onClick={() => loadAlbums(currentPage + 1)} disabled={currentPage === totalPages}>»</button>
        </div>
      )}

      {/* Cover Upload Modal */}
      <div className={`modal ${modalOpen ? 'show' : ''}`} onClick={(e) => e.target.id === 'coverModal' && closeModal()}>
        <div className="modal-content">
          <div className="modal-header">
            <h2>
              {getCurrentAlbum() 
                ? `Update Album Cover — ${getCurrentAlbum().artist} - ${getCurrentAlbum().album}` 
                : 'Update Album Cover'}
            </h2>
            <button className="close-modal" onClick={closeModal}>&times;</button>
          </div>

          <div className="modal-tabs">
            <button 
              className={`modal-tab ${activeTab === 'file' ? 'active' : ''}`} 
              onClick={() => setActiveTab('file')}
            >
              Upload File
            </button>
            <button 
              className={`modal-tab ${activeTab === 'url' ? 'active' : ''}`} 
              onClick={() => setActiveTab('url')}
            >
              From URL
            </button>
            <button 
              className={`modal-tab ${activeTab === 'api' ? 'active' : ''}`} 
              onClick={() => setActiveTab('api')}
            >
              iTunes API
            </button>
          </div>

          <div id="tab-file" className={`tab-content ${activeTab === 'file' ? 'active' : ''}`}>
            <div className="form-group">
              <label>Select Image File</label>
              <input type="file" id="coverFile" accept="image/*" />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={closeModal}>Cancel</button>
              <button className="btn-primary" onClick={uploadCoverFile}>Upload</button>
            </div>
          </div>

          <div id="tab-url" className={`tab-content ${activeTab === 'url' ? 'active' : ''}`}>
            <div className="form-group">
              <label>Image URL</label>
              <input type="text" id="coverUrl" placeholder="https://example.com/cover.jpg" />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={closeModal}>Cancel</button>
              <button className="btn-primary" onClick={uploadCoverUrl}>Download</button>
            </div>
          </div>

          <div id="tab-api" className={`tab-content ${activeTab === 'api' ? 'active' : ''}`}>
            <p>Automatically fetch album cover from iTunes based on artist and album name.</p>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={closeModal}>Cancel</button>
              <button className="btn-primary" onClick={uploadCoverApi}>Fetch from iTunes</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

