# Unified Content Analysis & Organization Technical Design

> **Status**: 🔄 **Planning Phase** - Future enhancement not yet implemented
> 
> **Current System**: Basic RAG with video-level retrieval working (192/341 videos with captions)
> **This Document**: Technical design for unified content analysis combining caption quality, playlist organization, and content intelligence

## Architecture Overview

This design document outlines a unified content analysis system that comprehensively analyzes YouTube channel content across multiple dimensions - caption quality, playlist organization, temporal patterns, and content categories. This unified approach provides a complete content intelligence layer for enhanced RAG retrieval.

**Core Principle**: Single analysis pass that captures all content dimensions, enabling intelligent filtering and retrieval based on quality, organization, and content type.

**Note**: This is a planning document. The current working system provides basic RAG functionality with 192 captioned videos out of 341 total videos.

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   YouTube API   │────▶│ Unified Content │────▶│  Vector Store   │
│  (videos.json)  │     │    Analyzer     │     │ (FAISS/Chroma) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                          │
         │                       ▼                          ▼
         │              ┌───────────────┐         ┌───────────────┐
         └─────────────▶│Content Intel  │────────▶│ Smart Retriever│
                        │   Database    │         │   + Filters    │
                        │   (SQLite)    │         └───────────────┘
                        └───────────────┘

Components:
- Unified Content Analyzer: Single-pass analysis of captions, playlists, metadata
- Content Intel Database: Comprehensive storage of all content dimensions
- Smart Retriever: Multi-dimensional filtering and quality-aware ranking
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
  "url": "https://youtube.com/watch?v=...",
  "has_captions": false  # Currently missing for 149/341 videos
}
```

### Unified Content Intelligence Model
```python
# content_analysis.json - Single unified analysis output
{
  "analysis_timestamp": "2024-01-15T10:30:00Z",
  "channel_stats": {
    "total_videos": 341,
    "captioned_videos": 192,
    "playlist_count": 12,
    "date_range": ["2023-01-01", "2024-01-15"]
  },
  "videos": {
    "videoId1": {
      # Core metadata
      "title": "Understanding Options Greeks",
      "published_at": "2024-01-01T00:00:00Z",
      "duration": 1235,  # seconds
      
      # Caption analysis
      "caption_status": {
        "available": true,
        "source": "cleaned",  # original, cleaned, auto-generated, none
        "quality_score": 0.85,  # 0-1 scale
        "quality_factors": {
          "completeness": 0.95,  # timestamp coverage
          "technical_accuracy": 0.80,  # domain terms present
          "formatting": 0.75,  # speaker labels, punctuation
          "confidence": 0.90  # if auto-generated
        },
        "word_count": 1523,
        "technical_terms": ["delta", "gamma", "theta", "vega"]
      },
      
      # Content intelligence
      "content_analysis": {
        "primary_category": "educational",
        "subcategory": "options_basics",
        "topics": ["greeks", "risk_management"],
        "complexity_level": "intermediate",
        "temporal_relevance": "evergreen",  # vs time-sensitive
        "engagement_potential": "high"
      },
      
      # Organizational context
      "playlist_membership": [
        {
          "id": "PLxxxxxx",
          "title": "Options Education Series",
          "position": 5,
          "playlist_category": "educational"
        }
      ],
      
      # Publishing patterns
      "publishing_context": {
        "day_of_week": "monday",
        "time_of_day": "morning",
        "series_position": 5,  # if part of series
        "related_videos": ["videoId2", "videoId3"]
      }
    }
  },
  
  # Aggregated insights
  "content_insights": {
    "caption_coverage_by_category": {
      "educational": {"total": 80, "captioned": 75, "avg_quality": 0.82},
      "daily_update": {"total": 200, "captioned": 90, "avg_quality": 0.65},
      "interview": {"total": 41, "captioned": 27, "avg_quality": 0.71}
    },
    "playlist_quality_correlation": {
      "high_quality_playlists": ["PLxxxxxx", "PLyyyyyy"],
      "needs_improvement": ["PLzzzzzz"]
    },
    "temporal_patterns": {
      "best_caption_coverage": "monday_wednesday",
      "content_gaps": "weekend_content"
    }
  }
}
```

### SQLite Schema (Unified Content Intelligence)
```sql
-- Core video intelligence table
CREATE TABLE video_intelligence (
    video_id VARCHAR(32) PRIMARY KEY,
    title TEXT NOT NULL,
    published_at DATETIME,
    duration INTEGER,
    
    -- Caption intelligence
    has_captions BOOLEAN DEFAULT FALSE,
    caption_source VARCHAR(20), -- original, cleaned, auto-generated, none
    caption_quality_score REAL, -- 0.0 to 1.0
    caption_completeness REAL,
    caption_technical_accuracy REAL,
    caption_word_count INTEGER,
    
    -- Content classification
    primary_category VARCHAR(50), -- educational, daily_update, interview
    subcategory VARCHAR(50), -- options_basics, market_analysis, etc
    complexity_level VARCHAR(20), -- beginner, intermediate, advanced
    temporal_relevance VARCHAR(20), -- evergreen, time-sensitive, dated
    
    -- Publishing patterns
    day_of_week VARCHAR(10),
    time_of_day VARCHAR(20),
    
    -- Analysis metadata
    analyzed_at DATETIME,
    analysis_version VARCHAR(10)
);

-- Playlist intelligence
CREATE TABLE playlist_intelligence (
    id VARCHAR(32) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50),
    avg_caption_quality REAL,
    caption_coverage REAL,
    total_duration INTEGER,
    coherence_score REAL -- how well videos fit together
);

-- Enhanced video-playlist mapping with context
CREATE TABLE video_playlist_context (
    video_id VARCHAR(32),
    playlist_id VARCHAR(32),
    position INTEGER,
    relevance_score REAL, -- how well video fits playlist theme
    PRIMARY KEY (video_id, playlist_id),
    FOREIGN KEY (video_id) REFERENCES video_intelligence(video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlist_intelligence(id)
);

-- Content relationships
CREATE TABLE video_relationships (
    video_id VARCHAR(32),
    related_video_id VARCHAR(32),
    relationship_type VARCHAR(50), -- sequel, prerequisite, similar_topic
    confidence REAL,
    PRIMARY KEY (video_id, related_video_id)
);

-- Aggregated insights cache
CREATE TABLE content_insights (
    insight_type VARCHAR(50) PRIMARY KEY,
    insight_data JSON,
    calculated_at DATETIME
);

-- Performance indexes
CREATE INDEX idx_video_quality ON video_intelligence(
    has_captions, caption_quality_score, primary_category
);
CREATE INDEX idx_temporal ON video_intelligence(
    published_at, temporal_relevance
);
CREATE INDEX idx_complexity ON video_intelligence(
    complexity_level, primary_category
);
```

## Component Design

### Unified Content Analyzer

**New: content_analyzer.py**
```python
class UnifiedContentAnalyzer:
    """Single-pass analyzer for all content dimensions"""
    
    def __init__(self, config: AnalyzerConfig):
        self.caption_analyzer = CaptionQualityAnalyzer()
        self.playlist_analyzer = PlaylistAnalyzer() 
        self.pattern_analyzer = ContentPatternAnalyzer()
        self.relationship_analyzer = VideoRelationshipAnalyzer()
        
    async def analyze_channel_comprehensive(self) -> ContentIntelligence:
        """Perform complete channel analysis in single pass"""
        # Load all data sources
        videos = await self._load_videos()
        playlists = await self._fetch_playlists() if self.config.fetch_playlists else []
        captions = self._scan_caption_files()
        
        # Parallel analysis of different dimensions
        results = await asyncio.gather(
            self._analyze_caption_quality(videos, captions),
            self._analyze_content_patterns(videos),
            self._analyze_playlist_coherence(videos, playlists),
            self._discover_relationships(videos)
        )
        
        # Synthesize insights
        intelligence = self._synthesize_intelligence(results)
        
        # Cache results
        self._store_intelligence(intelligence)
        
        return intelligence
        
    def _analyze_caption_quality(self, videos, captions) -> CaptionAnalysis:
        """Advanced caption quality assessment"""
        analysis = CaptionAnalysis()
        
        for video in videos:
            if video.id in captions:
                quality = self.caption_analyzer.assess_quality(
                    caption_file=captions[video.id],
                    video_metadata=video,
                    check_technical_terms=True,
                    analyze_timestamps=True
                )
                analysis.add_video_quality(video.id, quality)
                
        return analysis
        
    def _synthesize_intelligence(self, results) -> ContentIntelligence:
        """Combine all analysis dimensions into unified intelligence"""
        return ContentIntelligence(
            caption_insights=results[0],
            content_patterns=results[1],
            playlist_insights=results[2],
            relationships=results[3],
            recommendations=self._generate_recommendations(results)
        )
```

### Smart Quality Assessment

**Enhanced: caption_quality_analyzer.py**
```python
class CaptionQualityAnalyzer:
    """Advanced caption quality assessment with multiple metrics"""
    
    def __init__(self):
        self.technical_terms = self._load_domain_vocabulary()
        self.quality_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
    def assess_quality(self, caption_file: str, video_metadata: dict,
                      check_technical_terms=True, analyze_timestamps=True) -> QualityAssessment:
        """Comprehensive caption quality assessment"""
        
        caption_data = self._parse_caption_file(caption_file)
        
        # Multiple quality dimensions
        scores = {
            'completeness': self._assess_completeness(caption_data, video_metadata['duration']),
            'technical_accuracy': self._assess_technical_accuracy(caption_data) if check_technical_terms else 1.0,
            'formatting': self._assess_formatting(caption_data),
            'timestamp_quality': self._assess_timestamp_quality(caption_data) if analyze_timestamps else 1.0,
            'coherence': self._assess_coherence(caption_data)
        }
        
        # Weighted composite score
        weights = {'completeness': 0.3, 'technical_accuracy': 0.25, 
                  'formatting': 0.15, 'timestamp_quality': 0.2, 'coherence': 0.1}
        
        composite_score = sum(scores[k] * weights[k] for k in scores)
        
        return QualityAssessment(
            scores=scores,
            composite_score=composite_score,
            quality_level=self._score_to_level(composite_score),
            technical_terms_found=self._extract_technical_terms(caption_data),
            issues=self._identify_quality_issues(scores)
        )
        
    def _assess_completeness(self, caption_data, video_duration):
        """Analyze temporal coverage and gaps"""
        if not caption_data.timestamps:
            return 0.0
            
        # Calculate coverage
        covered_duration = self._calculate_covered_duration(caption_data.timestamps)
        coverage_ratio = covered_duration / video_duration
        
        # Penalize for large gaps
        max_gap = self._find_largest_gap(caption_data.timestamps)
        gap_penalty = min(max_gap / 60, 0.2)  # Max 20% penalty for gaps > 1 min
        
        return max(0, min(1, coverage_ratio - gap_penalty))
```

### 2. Document Loader Enhancement

**Modified: document_loader.py**
```python
class EnhancedDocumentLoader:
    def __init__(self, analyzer: UnifiedContentAnalyzer):
        self.analyzer = analyzer
        self.intelligence_cache = None
        
    async def load_with_content_intelligence(self):
        """Load documents with comprehensive content intelligence"""
        
        # Run unified analysis if not cached
        if not self.intelligence_cache:
            self.intelligence_cache = await self.analyzer.analyze_channel_comprehensive()
        
        intelligence = self.intelligence_cache
        
        # Load base documents
        documents = self._load_base_documents()
        
        # Enhance each document with multi-dimensional metadata
        enhanced_documents = []
        for doc in documents:
            video_id = doc.metadata.get('source', '')
            if video_id in intelligence.videos:
                video_intel = intelligence.videos[video_id]
                
                # Add all intelligence dimensions
                doc.metadata.update({
                    # Caption intelligence
                    'has_captions': video_intel.caption_status.available,
                    'caption_quality_score': video_intel.caption_status.quality_score,
                    'caption_source': video_intel.caption_status.source,
                    
                    # Content intelligence
                    'primary_category': video_intel.content_analysis.primary_category,
                    'complexity_level': video_intel.content_analysis.complexity_level,
                    'temporal_relevance': video_intel.content_analysis.temporal_relevance,
                    
                    # Organizational context
                    'playlist_ids': [p['id'] for p in video_intel.playlist_membership],
                    'playlist_titles': [p['title'] for p in video_intel.playlist_membership],
                    
                    # Quality composite
                    'retrieval_priority': self._calculate_retrieval_priority(video_intel)
                })
            
            enhanced_documents.append(doc)
        
        return enhanced_documents
        
    def _calculate_retrieval_priority(self, video_intel):
        """Calculate retrieval priority based on multiple factors"""
        score = 0.0
        
        # Caption quality weight
        score += video_intel.caption_status.quality_score * 0.4
        
        # Content relevance weight
        if video_intel.content_analysis.temporal_relevance == 'evergreen':
            score += 0.3
        
        # Complexity appropriateness
        if video_intel.content_analysis.complexity_level == 'intermediate':
            score += 0.2
            
        # Playlist membership bonus
        if video_intel.playlist_membership:
            score += 0.1
            
        return score
```

### 3. Dual Vector Store Implementation

#### FAISS Approach (CPU-Optimized)

**Strategy**: Multi-dimensional filtering with intelligent over-fetching

```python
class FAISSIntelligentRetriever:
    def __init__(self, vector_store, content_db):
        self.vector_store = vector_store
        self.content_db = content_db  # SQLite with full intelligence
        self.adaptive_fetcher = AdaptiveOverFetcher()
        
    def search_with_intelligence(self, query: str, filters: RetrievalFilters) -> List[Document]:
        """Search with comprehensive content intelligence filters"""
        
        # Calculate optimal over-fetch based on filter restrictiveness
        fetch_factor = self.adaptive_fetcher.calculate_factor(filters)
        
        # Initial vector search
        raw_results = self.vector_store.similarity_search(query, k=filters.k * fetch_factor)
        
        # Get video IDs for batch intelligence lookup
        video_ids = [doc.metadata['source'] for doc in raw_results]
        video_intelligence = self.content_db.get_video_intelligence_batch(video_ids)
        
        # Apply multi-dimensional filtering
        filtered_results = []
        for doc in raw_results:
            video_id = doc.metadata['source']
            intel = video_intelligence.get(video_id)
            
            if not intel:
                continue
                
            # Check all filter dimensions
            if self._passes_all_filters(intel, filters):
                # Enhance document with intelligence
                doc.metadata.update(self._extract_key_intelligence(intel))
                
                # Add relevance boost based on quality
                doc.metadata['relevance_boost'] = intel.caption_status.quality_score * 0.1
                
                filtered_results.append(doc)
                
                if len(filtered_results) >= filters.k:
                    break
        
        # Re-rank by combined score
        return self._rerank_by_intelligence(filtered_results, filters)
        
    def _passes_all_filters(self, intel: VideoIntelligence, filters: RetrievalFilters) -> bool:
        """Check if video passes all filter criteria"""
        
        # Caption filters
        if filters.require_captions and not intel.caption_status.available:
            return False
            
        if filters.min_caption_quality:
            if intel.caption_status.quality_score < self._quality_threshold(filters.min_caption_quality):
                return False
        
        # Content filters
        if filters.categories and intel.content_analysis.primary_category not in filters.categories:
            return False
            
        if filters.complexity_levels and intel.content_analysis.complexity_level not in filters.complexity_levels:
            return False
            
        # Temporal filters
        if filters.temporal_relevance and intel.content_analysis.temporal_relevance != filters.temporal_relevance:
            return False
            
        # Playlist filters
        if filters.playlist_ids:
            video_playlists = {p['id'] for p in intel.playlist_membership}
            if not video_playlists.intersection(filters.playlist_ids):
                return False
                
        return True
```

**Metadata Storage**: Separate SQLite database with video-playlist mappings

**Performance**: O(n) post-retrieval filtering, where n = k * over_fetch_factor

#### ChromaDB Approach (GPU-Optimized)

**Strategy**: Native metadata filtering using WHERE clause with caption quality

```python
class ChromaEnhancedRetriever:
    def search_with_filters(self, query, k=4, playlist_ids=None, exclude_playlists=None,
                           require_captions=False, min_caption_quality="low"):
        where_clause = self._build_where_clause(
            playlist_ids, exclude_playlists, require_captions, min_caption_quality
        )
        
        return self.vector_store.similarity_search(query, k=k, where=where_clause)
        
    def _build_where_clause(self, playlist_ids, exclude_playlists, require_captions, min_quality):
        conditions = []
        
        # Caption filtering
        if require_captions:
            conditions.append({"has_captions": {"$eq": True}})
            if min_quality != "low":
                conditions.append({"caption_quality": {"$in": self._get_quality_levels(min_quality)}})
        
        # Playlist filtering  
        if playlist_ids:
            conditions.append({"playlist_ids": {"$in": playlist_ids}})
        elif exclude_playlists:
            conditions.append({"playlist_ids": {"$nin": exclude_playlists}})
            
        return {"$and": conditions} if len(conditions) > 1 else conditions[0] if conditions else None
        
    def _get_quality_levels(self, min_quality):
        levels = {"low": ["low", "medium", "high"], 
                 "medium": ["medium", "high"], 
                 "high": ["high"]}
        return levels.get(min_quality, ["low", "medium", "high"])
```

**Metadata Storage**: Native in ChromaDB

**Performance**: O(log n) with indexed metadata filtering

### 4. Unified Retriever Interface

```python
class EnhancedRetriever:
    """Factory that returns appropriate retriever based on vector store type"""
    
    @staticmethod
    def create(vector_store, config):
        if isinstance(vector_store, FAISSVectorStore):
            metadata_db = MetadataDB(config.db_path)
            return FAISSEnhancedRetriever(vector_store, metadata_db)
        elif isinstance(vector_store, Chroma):
            return ChromaEnhancedRetriever(vector_store)
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
# Enhanced with caption and playlist filtering
{
    "question": "How do gamma squeezes work?",
    "playlist_ids": ["PLxxxxxx"],  # Optional: include only
    "exclude_playlist_ids": ["PLyyyyyy"],  # Optional: exclude
    "require_captions": true,  # Optional: only captioned content
    "min_caption_quality": "medium",  # Optional: quality threshold
    "k": 4
}

# GET /api/caption-stats
# Returns caption coverage analysis
{
    "total_videos": 341,
    "captioned_videos": 192,
    "coverage_percentage": 56.3,
    "quality_breakdown": {
        "high": 120,
        "medium": 52, 
        "low": 20,
        "none": 149
    },
    "by_content_type": {
        "educational": {"total": 80, "captioned": 75},
        "daily_updates": {"total": 200, "captioned": 90},
        "interviews": {"total": 61, "captioned": 27}
    }
}
```

### 6. UI Components

**New: EnhancedFilterPanel.js**
```javascript
// Combined filtering interface with:
// - Caption quality toggle ("Captions Required", "High Quality Only")
// - Playlist multi-select dropdown with caption coverage stats
// - Content type presets ("Educational Only", "Recent Updates", "Interviews")
// - Visual indicators for video counts and caption coverage per filter
// - "Smart Filter" that automatically prioritizes captioned educational content

// Example filter panel:
// ┌─ Content Filters ────────────────────┐
// │ ☑ Require Captions (192/341 videos)  │ 
// │ ☐ High Quality Only (120/192 videos) │
// │                                      │
// │ Playlists: [Multi-Select Dropdown]   │
// │ ├─ Options Education (75/80 videos)  │
// │ ├─ Daily Updates (90/200 videos)     │
// │ └─ Interviews (27/61 videos)         │
// │                                      │
// │ Quick Filters:                       │
// │ [Educational] [Recent] [High Quality]│
// └──────────────────────────────────────┘
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

### From Current to Enhanced System

1. **Phase 1**: Unified Content Analysis (Foundation)
   - Implement UnifiedContentAnalyzer for single-pass analysis
   - Analyze captions, playlists, patterns, and relationships together
   - Generate comprehensive content intelligence database
   - Provide immediate value: caption coverage report + content insights
   
2. **Phase 2**: Intelligence Integration
   - Enhance document metadata with full intelligence
   - Implement intelligent retrieval with multi-dimensional filtering
   - Add quality-aware ranking and re-ranking
   
3. **Phase 3**: Advanced Features
   - Content relationship discovery and navigation
   - Predictive quality improvements
   - Auto-categorization for new content
   
4. **Phase 4**: UI and API Enhancement
   - Unified filter interface with all dimensions
   - Real-time intelligence dashboard
   - Content quality recommendations

### From FAISS to ChromaDB

```python
# Migration preserves caption + playlist metadata
class EnhancedMigrator:
    def migrate(self, source_faiss, target_chroma):
        # Standard migration
        documents, embeddings = source_faiss.export()
        
        # Enhance with caption and playlist metadata
        caption_analyzer = CaptionAnalyzer()
        metadata_db = MetadataDB()
        
        for i, doc in enumerate(documents):
            video_id = doc.metadata['source']
            
            # Add caption metadata
            caption_data = caption_analyzer.get_video_caption_data(video_id)
            doc.metadata.update(caption_data)
            
            # Add playlist metadata
            playlist_data = metadata_db.get_playlists(video_id)
            doc.metadata.update(playlist_data)
            
        # Import to ChromaDB with enhanced metadata
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