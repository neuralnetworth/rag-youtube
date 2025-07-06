# Playlist-Aware RAG Technical Design

## Architecture Overview

This design introduces playlist support while maintaining compatibility with both FAISS (CPU-optimized) and ChromaDB (GPU-optimized) vector stores. The architecture emphasizes minimal changes to existing code while adding powerful filtering capabilities.

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   YouTube API   │────▶│  Playlist Cache  │────▶│  Vector Store   │
│  (videos.json)  │     │(playlists.json) │     │ (FAISS/Chroma) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌───────────────┐         ┌───────────────┐
                        │Metadata Store │         │   Retriever   │
                        │   (SQLite)    │         │  + Filtering  │
                        └───────────────┘         └───────────────┘
```

## Data Model

### Current State
```python
# videos.json
{
  "id": {"videoId": "xpXaF6OI9L0"},
  "snippet": {
    "title": "Video Title",
    "description": "Description",
    "publishedAt": "2024-01-01T00:00:00Z"
  }
}

# Vector Store Metadata
{
  "source": "video_id",
  "title": "Video Title",
  "url": "https://youtube.com/watch?v=..."
}
```

### Enhanced Data Model
```python
# playlists.json
{
  "playlists": [
    {
      "id": "PLxxxxxx",
      "title": "Options Education Series",
      "description": "Learn options trading",
      "itemCount": 30,
      "videos": ["videoId1", "videoId2", ...]
    }
  ],
  "video_playlists": {
    "videoId1": ["PLxxxxxx", "PLyyyyyy"],
    "videoId2": ["PLxxxxxx"]
  }
}

# Enhanced Vector Store Metadata
{
  "source": "video_id",
  "title": "Video Title",
  "url": "https://youtube.com/watch?v=...",
  "playlist_ids": ["PLxxxxxx", "PLyyyyyy"],
  "playlist_titles": ["Options Education", "Advanced Topics"],
  "published_at": "2024-01-01T00:00:00Z"
}
```

### SQLite Schema (For FAISS Metadata)
```sql
-- Playlists table
CREATE TABLE playlists (
    id VARCHAR(32) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    published_at DATETIME,
    item_count INTEGER,
    channel_id VARCHAR(32)
);

-- Video-Playlist mapping
CREATE TABLE video_playlists (
    video_id VARCHAR(32),
    playlist_id VARCHAR(32),
    position INTEGER,
    added_at DATETIME,
    PRIMARY KEY (video_id, playlist_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
);

-- Indexes for performance
CREATE INDEX idx_video_playlists_video ON video_playlists(video_id);
CREATE INDEX idx_video_playlists_playlist ON video_playlists(playlist_id);
```

## Component Design

### 1. YouTube API Integration

**New: playlist_fetcher.py**
```python
class PlaylistFetcher:
    def fetch_channel_playlists(channel_id: str) -> List[Playlist]:
        """Fetch all playlists with pagination"""
        
    def fetch_playlist_items(playlist_id: str) -> List[VideoRef]:
        """Fetch all videos in playlist with pagination"""
        
    def build_video_playlist_map(playlists: List[Playlist]) -> Dict:
        """Create bidirectional mapping"""
```

**API Quota Considerations**:
- playlists.list: 1 unit per call (50 playlists per page)
- playlistItems.list: 1 unit per call (50 items per page)
- Estimated cost for SpotGamma: ~10-20 units total

### 2. Document Loader Enhancement

**Modified: document_loader.py**
```python
class DocumentLoader:
    def load_with_playlists(self):
        # Load playlist data
        playlists = self._load_playlist_data()
        
        # Enhance metadata for each document
        for video_id, doc in documents:
            metadata = self._get_base_metadata(video_id)
            metadata.update(self._get_playlist_metadata(video_id, playlists))
            
    def _get_playlist_metadata(self, video_id, playlists):
        return {
            "playlist_ids": playlists.video_playlists.get(video_id, []),
            "playlist_titles": [p.title for p in playlists if video_id in p.videos]
        }
```

### 3. Dual Vector Store Implementation

#### FAISS Approach (CPU-Optimized)

**Strategy**: Post-retrieval filtering with over-fetching

```python
class FAISSPlaylistRetriever:
    def __init__(self, vector_store, metadata_db):
        self.vector_store = vector_store
        self.metadata_db = metadata_db
        self.over_fetch_factor = 5  # Retrieve 5x requested results
        
    def search_with_playlists(self, query, k=4, playlist_ids=None, exclude_playlists=None):
        # Over-fetch to ensure enough results after filtering
        raw_results = self.vector_store.similarity_search(
            query, 
            k=k * self.over_fetch_factor
        )
        
        # Apply playlist filtering
        filtered = []
        for doc, metadata in raw_results:
            if self._matches_playlist_filter(metadata, playlist_ids, exclude_playlists):
                filtered.append((doc, metadata))
                if len(filtered) >= k:
                    break
                    
        return filtered[:k]
```

**Metadata Storage**: Separate SQLite database with video-playlist mappings

**Performance**: O(n) post-retrieval filtering, where n = k * over_fetch_factor

#### ChromaDB Approach (GPU-Optimized)

**Strategy**: Native metadata filtering using WHERE clause

```python
class ChromaPlaylistRetriever:
    def search_with_playlists(self, query, k=4, playlist_ids=None, exclude_playlists=None):
        where_clause = self._build_where_clause(playlist_ids, exclude_playlists)
        
        return self.vector_store.similarity_search(
            query,
            k=k,
            where=where_clause
        )
        
    def _build_where_clause(self, playlist_ids, exclude_playlists):
        if playlist_ids:
            return {"playlist_ids": {"$in": playlist_ids}}
        elif exclude_playlists:
            return {"playlist_ids": {"$nin": exclude_playlists}}
        return None
```

**Metadata Storage**: Native in ChromaDB

**Performance**: O(log n) with indexed metadata filtering

### 4. Unified Retriever Interface

```python
class PlaylistAwareRetriever:
    """Factory that returns appropriate retriever based on vector store type"""
    
    @staticmethod
    def create(vector_store, config):
        if isinstance(vector_store, FAISSVectorStore):
            metadata_db = MetadataDB(config.db_path)
            return FAISSPlaylistRetriever(vector_store, metadata_db)
        elif isinstance(vector_store, Chroma):
            return ChromaPlaylistRetriever(vector_store)
        else:
            raise ValueError(f"Unsupported vector store: {type(vector_store)}")
```

### 5. API Enhancements

**New Endpoints**:
```python
# GET /api/playlists
# Returns all available playlists
{
    "playlists": [
        {
            "id": "PLxxxxxx",
            "title": "Options Education Series",
            "itemCount": 30,
            "description": "..."
        }
    ]
}

# POST /api/ask
# Enhanced with playlist filtering
{
    "question": "How do gamma squeezes work?",
    "playlist_ids": ["PLxxxxxx"],  # Optional: include only
    "exclude_playlist_ids": ["PLyyyyyy"],  # Optional: exclude
    "k": 4
}
```

### 6. UI Components

**New: PlaylistSelector.vue**
```javascript
// Multi-select dropdown with:
// - Checkbox for each playlist
// - "Select All" / "Clear All" options
// - Preset filters (Educational, Recent, etc.)
// - Show video count per playlist
```

## Performance Considerations

### FAISS Optimization Strategies

1. **Adaptive Over-fetching**
   ```python
   # Adjust factor based on filter restrictiveness
   if len(playlist_ids) == 1:
       over_fetch_factor = 10  # More restrictive = higher factor
   else:
       over_fetch_factor = 5
   ```

2. **Metadata Caching**
   ```python
   # Cache playlist metadata in memory
   @lru_cache(maxsize=1000)
   def get_video_playlists(video_id):
       return db.query("SELECT playlist_ids FROM video_playlists WHERE video_id = ?", video_id)
   ```

3. **Batch Processing**
   ```python
   # Fetch metadata for multiple videos in one query
   video_ids = [doc.metadata['source'] for doc in raw_results]
   all_metadata = db.batch_query(video_ids)
   ```

### ChromaDB Optimization

1. **Index Configuration**
   ```python
   # Ensure playlist_ids is indexed
   collection.create_index(["playlist_ids"])
   ```

2. **Query Optimization**
   ```python
   # Use specific operators for better performance
   where = {
       "$and": [
           {"playlist_ids": {"$contains": playlist_id}},
           {"published_at": {"$gte": cutoff_date}}
       ]
   }
   ```

## Migration Strategy

### From Current to Playlist-Aware

1. **Phase 1**: Add playlist fetching without breaking changes
2. **Phase 2**: Enhance metadata in new documents
3. **Phase 3**: Backfill existing documents with playlist data
4. **Phase 4**: Enable UI filtering options

### From FAISS to ChromaDB

```python
# Migration preserves playlist metadata
class PlaylistAwareMigrator:
    def migrate(self, source_faiss, target_chroma):
        # Standard migration
        documents, embeddings = source_faiss.export()
        
        # Enhance with playlist metadata
        metadata_db = MetadataDB()
        for i, doc in enumerate(documents):
            video_id = doc.metadata['source']
            playlist_data = metadata_db.get_playlists(video_id)
            doc.metadata.update(playlist_data)
            
        # Import to ChromaDB
        target_chroma.import(documents, embeddings)
```

## Security & Privacy Considerations

1. **API Key Protection**: Playlist fetching uses same Google API key
2. **Rate Limiting**: Implement client-side rate limiting for playlist queries
3. **Access Control**: Consider playlist-based access control for private deployments

## Testing Strategy

### Unit Tests
- Playlist fetching with pagination
- Metadata filtering logic
- FAISS over-fetching behavior
- ChromaDB WHERE clause generation

### Integration Tests
- End-to-end playlist filtering
- Performance benchmarks (FAISS vs ChromaDB)
- UI component interaction
- API endpoint validation

### Performance Tests
```python
# Benchmark different scenarios
scenarios = [
    {"name": "No filter", "playlist_ids": None},
    {"name": "Single playlist", "playlist_ids": ["PLxxxxxx"]},
    {"name": "Exclude large playlist", "exclude_playlist_ids": ["PLyyyyyy"]},
]

for scenario in scenarios:
    measure_retrieval_time(query, **scenario)
    measure_accuracy(query, expected_results, **scenario)
```

## Trade-offs and Decisions

### FAISS vs ChromaDB Trade-offs

| Aspect | FAISS Approach | ChromaDB Approach |
|--------|----------------|-------------------|
| Metadata Storage | External SQLite | Native in vector DB |
| Filtering Performance | O(n) post-retrieval | O(log n) indexed |
| Setup Complexity | Higher (two databases) | Lower (single store) |
| Memory Usage | Lower | Higher |
| GPU Requirement | None | Recommended |
| Result Quality | May return < k results | Always returns k results |

### Design Decisions

1. **Separate Playlist File**: Keep playlists.json separate from videos.json for:
   - Backward compatibility
   - Easier playlist updates
   - Reduced parsing overhead

2. **Over-fetching Strategy**: For FAISS, use 5x over-fetching by default:
   - Balances performance vs result quality
   - Adjustable based on filter restrictiveness

3. **Unified Interface**: Single retriever interface for both stores:
   - Simplifies application code
   - Enables easy switching between stores
   - Consistent API regardless of backend

4. **Metadata Denormalization**: Store playlist titles with IDs:
   - Faster display without joins
   - Slight storage overhead acceptable

## Future Enhancements

1. **Smart Over-fetching**: Use ML to predict optimal over-fetch factor
2. **Playlist Embeddings**: Create playlist-level embeddings for better retrieval
3. **Hierarchical Retrieval**: Search playlists first, then videos
4. **Cross-playlist Queries**: Find videos that appear in multiple specified playlists
5. **Temporal Filtering**: Combined playlist + date range filtering

## Conclusion

This design provides a robust playlist filtering system that works efficiently with both FAISS and ChromaDB backends. The architecture maintains backward compatibility while adding powerful new capabilities that significantly improve the RAG experience for organized YouTube channels.