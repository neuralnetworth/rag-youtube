# Playlist-Aware RAG Implementation Guide

> **Status**: 🔄 **Planning Phase** - Implementation roadmap for future development
> 
> **Current System**: Basic RAG pipeline functional with SpotGamma data
> **This Document**: Step-by-step implementation plan for playlist features

## Overview

This guide provides a step-by-step implementation roadmap for adding playlist support to RAG-YouTube, with specific paths for both FAISS (CPU) and ChromaDB (GPU) setups.

**Prerequisites**: The current basic RAG system should be working before implementing these enhancements.

## Implementation Phases

### Phase 1: YouTube API Enhancement (Both Setups)

#### Step 1.1: Create Playlist Fetcher

**File**: `src/playlist_fetcher.py`

```python
#!/usr/bin/env python3
"""
Fetch and manage YouTube playlist data.
"""
import os
import json
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class PlaylistFetcher:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.playlists_file = 'playlists.json'
        
    def fetch_channel_playlists(self, channel_id: str) -> List[Dict]:
        """Fetch all playlists for a channel with pagination."""
        playlists = []
        next_page_token = None
        
        while True:
            try:
                request = self.youtube.playlists().list(
                    part='snippet,contentDetails',
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    playlists.append({
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'publishedAt': item['snippet']['publishedAt'],
                        'itemCount': item['contentDetails']['itemCount'],
                        'videos': []  # To be filled by fetch_playlist_items
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"Error fetching playlists: {e}")
                break
                
        return playlists
    
    def fetch_playlist_items(self, playlist_id: str) -> List[str]:
        """Fetch all video IDs in a playlist."""
        video_ids = []
        next_page_token = None
        
        while True:
            try:
                request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_ids.append(item['contentDetails']['videoId'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"Error fetching playlist items: {e}")
                break
                
        return video_ids
    
    def build_playlist_data(self, channel_id: str) -> Dict:
        """Build complete playlist data structure."""
        print(f"Fetching playlists for channel {channel_id}...")
        playlists = self.fetch_channel_playlists(channel_id)
        
        # Fetch videos for each playlist
        for playlist in playlists:
            print(f"Fetching items for playlist: {playlist['title']}")
            playlist['videos'] = self.fetch_playlist_items(playlist['id'])
        
        # Build reverse mapping (video -> playlists)
        video_playlists = {}
        for playlist in playlists:
            for video_id in playlist['videos']:
                if video_id not in video_playlists:
                    video_playlists[video_id] = []
                video_playlists[video_id].append(playlist['id'])
        
        return {
            'channel_id': channel_id,
            'playlists': playlists,
            'video_playlists': video_playlists
        }
    
    def save_playlist_data(self, data: Dict):
        """Save playlist data to file."""
        with open(self.playlists_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved playlist data to {self.playlists_file}")
```

#### Step 1.2: Integrate with Video Listing

**Modify**: `src/list_videos.py`

Add playlist fetching after video listing:

```python
# After saving videos.json
if '--with-playlists' in sys.argv:
    from playlist_fetcher import PlaylistFetcher
    
    # Get API key from environment
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        sys.exit(1)
    
    # Fetch playlist data
    fetcher = PlaylistFetcher(api_key)
    playlist_data = fetcher.build_playlist_data(channel_id)
    fetcher.save_playlist_data(playlist_data)
```

### Phase 2: Storage Layer Implementation

#### Step 2.1: FAISS Metadata Storage

**File**: `src/metadata_store.py`

```python
#!/usr/bin/env python3
"""
SQLite metadata storage for FAISS setup.
"""
import sqlite3
import json
from typing import List, Dict, Optional
from contextlib import contextmanager

class MetadataStore:
    def __init__(self, db_path: str = "db/metadata.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id VARCHAR(32) PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    published_at DATETIME,
                    item_count INTEGER,
                    channel_id VARCHAR(32)
                );
                
                CREATE TABLE IF NOT EXISTS video_playlists (
                    video_id VARCHAR(32),
                    playlist_id VARCHAR(32),
                    position INTEGER,
                    PRIMARY KEY (video_id, playlist_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_vp_video 
                ON video_playlists(video_id);
                
                CREATE INDEX IF NOT EXISTS idx_vp_playlist 
                ON video_playlists(playlist_id);
            ''')
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def import_playlist_data(self, playlist_file: str = "playlists.json"):
        """Import playlist data from JSON file."""
        with open(playlist_file, 'r') as f:
            data = json.load(f)
        
        with self._get_connection() as conn:
            # Insert playlists
            for playlist in data['playlists']:
                conn.execute('''
                    INSERT OR REPLACE INTO playlists 
                    (id, title, description, published_at, item_count, channel_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    playlist['id'],
                    playlist['title'],
                    playlist.get('description', ''),
                    playlist.get('publishedAt'),
                    playlist.get('itemCount', 0),
                    data.get('channel_id')
                ))
            
            # Insert video-playlist mappings
            for video_id, playlist_ids in data['video_playlists'].items():
                for position, playlist_id in enumerate(playlist_ids):
                    conn.execute('''
                        INSERT OR REPLACE INTO video_playlists
                        (video_id, playlist_id, position)
                        VALUES (?, ?, ?)
                    ''', (video_id, playlist_id, position))
    
    def get_video_playlists(self, video_id: str) -> Dict:
        """Get playlist metadata for a video."""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT p.id, p.title
                FROM playlists p
                JOIN video_playlists vp ON p.id = vp.playlist_id
                WHERE vp.video_id = ?
                ORDER BY vp.position
            ''', (video_id,))
            
            rows = cursor.fetchall()
            return {
                'playlist_ids': [row['id'] for row in rows],
                'playlist_titles': [row['title'] for row in rows]
            }
    
    def filter_videos_by_playlist(self, video_ids: List[str], 
                                  playlist_ids: Optional[List[str]] = None,
                                  exclude_playlist_ids: Optional[List[str]] = None) -> List[str]:
        """Filter video IDs based on playlist membership."""
        if not playlist_ids and not exclude_playlist_ids:
            return video_ids
        
        with self._get_connection() as conn:
            query = "SELECT DISTINCT video_id FROM video_playlists WHERE video_id IN ({})".format(
                ','.join(['?'] * len(video_ids))
            )
            params = video_ids.copy()
            
            if playlist_ids:
                query += " AND playlist_id IN ({})".format(
                    ','.join(['?'] * len(playlist_ids))
                )
                params.extend(playlist_ids)
            
            if exclude_playlist_ids:
                query += " AND video_id NOT IN (SELECT video_id FROM video_playlists WHERE playlist_id IN ({}))".format(
                    ','.join(['?'] * len(exclude_playlist_ids))
                )
                params.extend(exclude_playlist_ids)
            
            cursor = conn.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
```

#### Step 2.2: Enhanced Document Loader

**Modify**: `src/document_loader.py`

```python
# Add playlist metadata loading
def load_documents():
    # Existing code...
    
    # Load playlist data if available
    playlist_metadata = {}
    if os.path.exists('playlists.json'):
        with open('playlists.json', 'r') as f:
            playlist_data = json.load(f)
            
        # For ChromaDB: embed metadata directly
        if using_chromadb:
            for video_id, playlist_ids in playlist_data['video_playlists'].items():
                playlist_titles = [
                    p['title'] for p in playlist_data['playlists'] 
                    if p['id'] in playlist_ids
                ]
                playlist_metadata[video_id] = {
                    'playlist_ids': playlist_ids,
                    'playlist_titles': playlist_titles
                }
        
        # For FAISS: import to SQLite
        else:
            from metadata_store import MetadataStore
            metadata_store = MetadataStore()
            metadata_store.import_playlist_data()
    
    # Enhance document metadata
    for doc in documents:
        video_id = doc.metadata.get('source', '')
        if video_id in playlist_metadata:
            doc.metadata.update(playlist_metadata[video_id])
```

### Phase 3: Retrieval Enhancement

#### Step 3.1: FAISS Playlist Retriever

**File**: `src/retrievers/faiss_playlist_retriever.py`

```python
#!/usr/bin/env python3
"""
FAISS retriever with playlist filtering support.
"""
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document
from metadata_store import MetadataStore

class FAISSPlaylistRetriever:
    def __init__(self, vector_store, metadata_store: MetadataStore, 
                 over_fetch_factor: int = 5):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.over_fetch_factor = over_fetch_factor
    
    def retrieve(self, query: str, k: int = 4,
                 playlist_ids: Optional[List[str]] = None,
                 exclude_playlist_ids: Optional[List[str]] = None) -> List[Document]:
        """Retrieve documents with playlist filtering."""
        
        # Calculate how many results to fetch
        fetch_k = k * self.over_fetch_factor
        if playlist_ids and len(playlist_ids) == 1:
            # Single playlist is more restrictive, fetch more
            fetch_k = k * 10
        
        # Get initial results from vector store
        results = self.vector_store.similarity_search(query, k=fetch_k)
        
        # Extract video IDs
        video_ids = [doc.metadata.get('source', '') for doc in results]
        
        # Filter by playlist membership
        filtered_video_ids = self.metadata_store.filter_videos_by_playlist(
            video_ids, playlist_ids, exclude_playlist_ids
        )
        
        # Build filtered results with enhanced metadata
        filtered_results = []
        for doc in results:
            video_id = doc.metadata.get('source', '')
            if video_id in filtered_video_ids:
                # Enhance metadata with playlist info
                playlist_info = self.metadata_store.get_video_playlists(video_id)
                doc.metadata.update(playlist_info)
                filtered_results.append(doc)
                
                if len(filtered_results) >= k:
                    break
        
        return filtered_results
```

#### Step 3.2: ChromaDB Playlist Retriever

**File**: `src/retrievers/chroma_playlist_retriever.py`

```python
#!/usr/bin/env python3
"""
ChromaDB retriever with native playlist filtering.
"""
from typing import List, Dict, Optional
from langchain.schema import Document

class ChromaPlaylistRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def retrieve(self, query: str, k: int = 4,
                 playlist_ids: Optional[List[str]] = None,
                 exclude_playlist_ids: Optional[List[str]] = None) -> List[Document]:
        """Retrieve documents with playlist filtering."""
        
        # Build where clause for ChromaDB
        where_clause = self._build_where_clause(playlist_ids, exclude_playlist_ids)
        
        # Use native ChromaDB filtering
        if where_clause:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                where=where_clause
            )
        else:
            results = self.vector_store.similarity_search(query=query, k=k)
        
        return results
    
    def _build_where_clause(self, playlist_ids: Optional[List[str]] = None,
                           exclude_playlist_ids: Optional[List[str]] = None) -> Optional[Dict]:
        """Build ChromaDB where clause for filtering."""
        if playlist_ids:
            return {"playlist_ids": {"$in": playlist_ids}}
        elif exclude_playlist_ids:
            return {"playlist_ids": {"$nin": exclude_playlist_ids}}
        return None
```

#### Step 3.3: Unified Retriever Factory

**File**: `src/retrievers/playlist_retriever_factory.py`

```python
#!/usr/bin/env python3
"""
Factory for creating appropriate playlist-aware retriever.
"""
from typing import Union
from vector_store_faiss import FAISSVectorStore
from langchain_community.vectorstores import Chroma
from .faiss_playlist_retriever import FAISSPlaylistRetriever
from .chroma_playlist_retriever import ChromaPlaylistRetriever
from metadata_store import MetadataStore

class PlaylistRetrieverFactory:
    @staticmethod
    def create_retriever(vector_store, config):
        """Create appropriate retriever based on vector store type."""
        if isinstance(vector_store, FAISSVectorStore):
            # FAISS needs external metadata store
            metadata_store = MetadataStore(
                db_path=os.path.join(config.db_persist_dir(), "metadata.db")
            )
            return FAISSPlaylistRetriever(vector_store, metadata_store)
        
        elif isinstance(vector_store, Chroma):
            # ChromaDB has native metadata support
            return ChromaPlaylistRetriever(vector_store)
        
        else:
            # Fallback to basic retriever
            return vector_store.as_retriever()
```

### Phase 4: API and UI Implementation

#### Step 4.1: API Endpoints

**Modify**: `src/app.py`

```python
# Add playlist endpoints
@app.route('/api/playlists')
def get_playlists():
    """Get all available playlists."""
    if not os.path.exists('playlists.json'):
        return {'playlists': []}
    
    with open('playlists.json', 'r') as f:
        data = json.load(f)
    
    # Format for UI
    playlists = []
    for playlist in data['playlists']:
        playlists.append({
            'id': playlist['id'],
            'title': playlist['title'],
            'description': playlist.get('description', ''),
            'itemCount': playlist.get('itemCount', 0),
            'videoCount': len(playlist.get('videos', []))
        })
    
    return {'playlists': playlists}

# Modify ask endpoint
@app.route('/ask', method='POST')
def ask():
    data = request.json
    question = data.get('question')
    playlist_ids = data.get('playlist_ids', None)
    exclude_playlist_ids = data.get('exclude_playlist_ids', None)
    
    # Create appropriate retriever
    retriever = PlaylistRetrieverFactory.create_retriever(
        agent.vectorstore, 
        agent.config
    )
    
    # Retrieve with playlist filtering
    docs = retriever.retrieve(
        question,
        k=data.get('k', 4),
        playlist_ids=playlist_ids,
        exclude_playlist_ids=exclude_playlist_ids
    )
    
    # Continue with existing chain logic...
```

#### Step 4.2: UI Components

**File**: `public/js/playlist-selector.vue`

```javascript
Vue.component('playlist-selector', {
    template: `
        <div class="playlist-selector">
            <h4>Filter by Playlist</h4>
            <div class="playlist-options">
                <button @click="selectAll">Select All</button>
                <button @click="clearAll">Clear All</button>
            </div>
            <div class="playlist-list">
                <div v-for="playlist in playlists" :key="playlist.id" 
                     class="playlist-item">
                    <label>
                        <input type="checkbox" 
                               :value="playlist.id"
                               v-model="selectedPlaylists">
                        {{ playlist.title }} ({{ playlist.videoCount }} videos)
                    </label>
                </div>
            </div>
            <div class="filter-mode">
                <label>
                    <input type="radio" value="include" v-model="filterMode">
                    Include selected playlists
                </label>
                <label>
                    <input type="radio" value="exclude" v-model="filterMode">
                    Exclude selected playlists
                </label>
            </div>
        </div>
    `,
    data() {
        return {
            playlists: [],
            selectedPlaylists: [],
            filterMode: 'include'
        };
    },
    mounted() {
        this.loadPlaylists();
    },
    methods: {
        async loadPlaylists() {
            const response = await fetch('/api/playlists');
            const data = await response.json();
            this.playlists = data.playlists;
        },
        selectAll() {
            this.selectedPlaylists = this.playlists.map(p => p.id);
        },
        clearAll() {
            this.selectedPlaylists = [];
        },
        getFilterParams() {
            if (this.selectedPlaylists.length === 0) {
                return {};
            }
            
            if (this.filterMode === 'include') {
                return { playlist_ids: this.selectedPlaylists };
            } else {
                return { exclude_playlist_ids: this.selectedPlaylists };
            }
        }
    }
});
```

### Phase 5: Testing Implementation

#### Step 5.1: Unit Tests

**File**: `test/test_playlist_filtering.py`

```python
#!/usr/bin/env python3
"""
Test playlist filtering functionality.
"""
import unittest
from src.metadata_store import MetadataStore
from src.retrievers.faiss_playlist_retriever import FAISSPlaylistRetriever

class TestPlaylistFiltering(unittest.TestCase):
    def setUp(self):
        self.metadata_store = MetadataStore(":memory:")
        self.load_test_data()
    
    def load_test_data(self):
        # Create test playlists and mappings
        test_data = {
            'playlists': [
                {'id': 'PL1', 'title': 'Educational', 'videos': ['v1', 'v2']},
                {'id': 'PL2', 'title': 'Daily Updates', 'videos': ['v2', 'v3']}
            ],
            'video_playlists': {
                'v1': ['PL1'],
                'v2': ['PL1', 'PL2'],
                'v3': ['PL2']
            }
        }
        # Import test data...
    
    def test_include_playlist_filter(self):
        # Test filtering to include specific playlist
        filtered = self.metadata_store.filter_videos_by_playlist(
            ['v1', 'v2', 'v3'],
            playlist_ids=['PL1']
        )
        self.assertEqual(sorted(filtered), ['v1', 'v2'])
    
    def test_exclude_playlist_filter(self):
        # Test filtering to exclude specific playlist
        filtered = self.metadata_store.filter_videos_by_playlist(
            ['v1', 'v2', 'v3'],
            exclude_playlist_ids=['PL2']
        )
        self.assertEqual(filtered, ['v1'])
```

#### Step 5.2: Performance Benchmarks

**File**: `test/benchmark_retrieval.py`

```python
#!/usr/bin/env python3
"""
Benchmark playlist filtering performance.
"""
import time
import statistics

def benchmark_retrieval(retriever, queries, scenarios):
    """Benchmark retrieval performance across scenarios."""
    results = {}
    
    for scenario_name, filter_params in scenarios.items():
        times = []
        
        for query in queries:
            start = time.time()
            docs = retriever.retrieve(query, k=4, **filter_params)
            elapsed = time.time() - start
            times.append(elapsed)
        
        results[scenario_name] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0,
            'result_counts': [len(docs) for docs in docs_list]
        }
    
    return results

# Define test scenarios
scenarios = {
    'no_filter': {},
    'single_playlist': {'playlist_ids': ['PLxxxxxx']},
    'multiple_playlists': {'playlist_ids': ['PLxxxxxx', 'PLyyyyyy']},
    'exclude_large': {'exclude_playlist_ids': ['PLzzzzzz']}  # Large playlist
}

# Run benchmarks for both FAISS and ChromaDB
for store_type in ['faiss', 'chromadb']:
    print(f"\nBenchmarking {store_type}:")
    retriever = create_retriever(store_type)
    results = benchmark_retrieval(retriever, test_queries, scenarios)
    print_results(results)
```

### Migration Guide

#### Migrating Existing Data

**File**: `scripts/add_playlist_metadata.py`

```python
#!/usr/bin/env python3
"""
Add playlist metadata to existing vector stores.
"""
import json
from document_loader import DocumentLoader
from metadata_store import MetadataStore

def migrate_existing_data():
    """Add playlist metadata to existing documents."""
    
    # Load playlist data
    with open('playlists.json', 'r') as f:
        playlist_data = json.load(f)
    
    # For FAISS: Just import to metadata store
    if using_faiss:
        metadata_store = MetadataStore()
        metadata_store.import_playlist_data()
        print("Playlist metadata added to SQLite store")
    
    # For ChromaDB: Update existing documents
    elif using_chromadb:
        # This requires re-embedding, which is expensive
        # Alternative: Update metadata without re-embedding
        collection = chromadb_client.get_collection("youtube_videos")
        
        for video_id, playlist_ids in playlist_data['video_playlists'].items():
            # Update documents with this video_id
            collection.update(
                where={"source": video_id},
                metadata={"playlist_ids": playlist_ids}
            )
        
        print("Playlist metadata added to ChromaDB")
```

### Deployment Checklist

1. **Pre-deployment**:
   - [ ] Backup existing vector stores
   - [ ] Test playlist fetching with API key
   - [ ] Verify SQLite installation (for FAISS)

2. **Deployment Steps**:
   - [ ] Deploy new code
   - [ ] Run `list_videos.py --with-playlists` to fetch playlist data
   - [ ] Run migration script if updating existing data
   - [ ] Restart web server

3. **Post-deployment**:
   - [ ] Verify `/api/playlists` endpoint returns data
   - [ ] Test filtering with single playlist
   - [ ] Test filtering with excluded playlist
   - [ ] Monitor performance metrics

### Configuration Options

Add to `rag-youtube.conf`:

```ini
[Playlists]
# Enable playlist filtering
enable_playlist_filter=true

# FAISS over-fetch factor
faiss_overfetch_factor=5

# Maximum playlists to display in UI
max_playlists_display=50

# Cache playlist metadata (minutes)
playlist_cache_ttl=60
```

### Troubleshooting

**Issue**: FAISS returns fewer results than requested
- **Solution**: Increase `faiss_overfetch_factor` in config
- **Alternative**: Fetch more videos for restrictive playlists

**Issue**: ChromaDB metadata filtering is slow
- **Solution**: Ensure playlist_ids field is indexed
- **Check**: Run `collection.create_index(['playlist_ids'])`

**Issue**: Playlist data missing after migration
- **Solution**: Re-run `list_videos.py --with-playlists`
- **Verify**: Check playlists.json exists and contains data

## Conclusion

This implementation provides a complete playlist filtering system that works with both FAISS and ChromaDB backends. The modular design allows for easy testing and future enhancements while maintaining backward compatibility.