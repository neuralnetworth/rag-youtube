# Simple Content Intelligence Technical Design

> **Status**: 🔄 **Planning Phase** - Simplified enhancement ready for implementation
> 
> **Current System**: Basic RAG with video-level retrieval working (192/341 videos with captions)
> **This Document**: Technical design for practical content filtering using metadata enhancement

## Architecture Overview

This design document outlines a simplified content intelligence system that enhances YouTube video metadata with practical filtering capabilities - caption availability, title-based categorization, basic quality scoring, and playlist organization. This lightweight approach provides immediate value without complex analysis.

**Core Principle**: Enhance existing metadata during document loading with simple pattern matching and scoring, enabling practical filtering without additional infrastructure.

**Note**: This is a simplified approach designed for quick implementation (1 week) while maintaining system simplicity.

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   YouTube API   │────▶│ Document Loader │────▶│  Vector Store   │
│  (videos.json)  │     │  + Enhancer     │     │ (FAISS/Chroma) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                          │
         │                       ▼                          ▼
         │              ┌───────────────┐         ┌───────────────┐
         └─────────────▶│ Simple Filters │────────▶│ FastAPI + UI   │
                        │ (In-Memory)    │         │   Filtering    │
                        └───────────────┘         └───────────────┘

Components:
- Document Loader + Enhancer: Adds metadata during loading (categories, quality, keywords)
- Simple Filters: In-memory filtering using enhanced metadata
- FastAPI + UI: Existing API with new filter parameters
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

### Enhanced Metadata Model
```python
# Enhanced document metadata (added during loading)
{
  "source": "xpXaF6OI9L0",  # video ID
  "title": "Understanding Options Greeks",
  "url": "https://youtube.com/watch?v=xpXaF6OI9L0",
  "published_at": "2024-01-01T00:00:00Z",
  
  # New simple enhancements
  "has_captions": true,
  "category": "educational",  # inferred from title
  "caption_quality": 0.75,    # simple words/minute calculation
  "quality_level": "high",    # high/medium/low
  "technical_score": 0.8,     # keyword frequency
  "playlist_ids": ["PLxxxxxx", "PLyyyyyy"],
  "playlist_titles": ["Options Education", "Greeks Explained"]
}

# Category patterns (simple title matching)
CATEGORY_PATTERNS = {
  "daily_update": ["hype", "market update", "close", "morning"],
  "educational": ["education", "tutorial", "learn", "basics", "understanding"],
  "interview": ["interview", "podcast", "with", "guest"],
  "special_event": ["fomc", "fed", "earnings", "cpi", "jpow"]
}

# Technical keywords (for scoring)
TECHNICAL_TERMS = [
  "gamma", "delta", "theta", "vega", "options", "strike",
  "expiration", "volatility", "iv", "call", "put", "spread",
  "squeeze", "0dte", "spx", "vix", "skew", "flow"
]
```

### No Database Required!
All metadata is stored directly in the vector store (FAISS/ChromaDB). The enhanced metadata is added during document loading and used for in-memory filtering. This keeps the system simple and fast.

## Component Design

### 1. Enhanced Document Loader

**Modified: document_loader_faiss.py**
```python
class SimpleMetadataEnhancer:
    """Add practical metadata during document loading"""
    
    def __init__(self):
        self.category_patterns = {
            "daily_update": ["hype", "market update", "close", "morning", "am ", "pm "],
            "educational": ["education", "tutorial", "learn", "basics", "understanding", "explained"],
            "interview": ["interview", "podcast", "with", "guest", "conversation"],
            "special_event": ["fomc", "fed", "earnings", "cpi", "jpow", "powell"]
        }
        
        self.technical_terms = [
            "gamma", "delta", "theta", "vega", "options", "strike",
            "expiration", "volatility", "iv", "call", "put", "spread",
            "squeeze", "0dte", "spx", "vix", "skew", "flow", "hedge"
        ]
        
    def enhance_metadata(self, doc, video_data, caption_path=None):
        """Add simple intelligence to document metadata"""
        
        # Check caption availability
        video_id = video_data['id']['videoId']
        doc.metadata['has_captions'] = caption_path is not None and os.path.exists(caption_path)
        
        # Infer category from title
        title_lower = video_data['snippet']['title'].lower()
        doc.metadata['category'] = self._infer_category(title_lower)
        
        # Calculate quality metrics if captions exist
        if doc.metadata['has_captions']:
            # Simple quality score (words per minute)
            word_count = len(doc.page_content.split())
            duration_minutes = video_data.get('contentDetails', {}).get('duration', 600) / 60
            words_per_minute = word_count / max(duration_minutes, 1)
            
            # Normalize to 0-1 scale
            doc.metadata['caption_quality'] = min(words_per_minute / 150, 1.0)
            doc.metadata['quality_level'] = self._score_to_level(doc.metadata['caption_quality'])
            
            # Count technical terms
            content_lower = doc.page_content.lower()
            term_count = sum(content_lower.count(term) for term in self.technical_terms)
            doc.metadata['technical_score'] = min(term_count / 20, 1.0)
        else:
            doc.metadata['caption_quality'] = 0.0
            doc.metadata['quality_level'] = 'none'
            doc.metadata['technical_score'] = 0.0
            
        # Add playlist information if available
        doc.metadata['playlist_ids'] = []
        doc.metadata['playlist_titles'] = []
        
        return doc
        
    def _infer_category(self, title_lower):
        """Simple category inference from title"""
        for category, patterns in self.category_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return category
        return 'general'
        
    def _score_to_level(self, score):
        """Convert numeric score to quality level"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        elif score > 0:
            return 'low'
        else:
            return 'none'
```

### 2. Simple Filtering System

**New: src/api/filters.py**
```python
class SimpleContentFilter:
    """In-memory filtering using enhanced metadata"""
    
    def filter_documents(self, documents, filters):
        """Apply filters to document list"""
        filtered = documents
        
        # Caption filter
        if filters.get('require_captions'):
            filtered = [doc for doc in filtered if doc.metadata.get('has_captions', False)]
            
        # Category filter
        if filters.get('category'):
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('category') == filters['category']]
            
        # Quality filter
        if filters.get('min_quality_level'):
            quality_order = {'none': 0, 'low': 1, 'medium': 2, 'high': 3}
            min_level = quality_order.get(filters['min_quality_level'], 0)
            filtered = [doc for doc in filtered 
                       if quality_order.get(doc.metadata.get('quality_level', 'none'), 0) >= min_level]
            
        # Date filter
        if filters.get('date_range'):
            cutoff_date = self._get_cutoff_date(filters['date_range'])
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('published_at', '') >= cutoff_date]
            
        # Playlist filters
        if filters.get('playlist_ids'):
            filtered = [doc for doc in filtered 
                       if any(pid in doc.metadata.get('playlist_ids', []) 
                             for pid in filters['playlist_ids'])]
                             
        if filters.get('exclude_playlist_ids'):
            filtered = [doc for doc in filtered 
                       if not any(pid in doc.metadata.get('playlist_ids', []) 
                                 for pid in filters['exclude_playlist_ids'])]
            
        return filtered
        
    def _get_cutoff_date(self, date_range):
        """Convert date range to cutoff date"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        if date_range == 'last_week':
            return (now - timedelta(days=7)).isoformat()
        elif date_range == 'last_month':
            return (now - timedelta(days=30)).isoformat()
        elif date_range == 'last_year':
            return (now - timedelta(days=365)).isoformat()
        return ''
```


### 3. Vector Store Implementation

#### FAISS Approach (Current System)

**Strategy**: Simple over-fetching with in-memory filtering

```python
class FAISSFilteredRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.filter = SimpleContentFilter()
        
    def search_with_filters(self, query: str, k: int = 4, filters: dict = None):
        """Search with simple metadata filters"""
        
        # Over-fetch to ensure enough results after filtering
        over_fetch_factor = 3 if filters else 1
        
        # Get more results than needed
        raw_results = self.vector_store.similarity_search(
            query, 
            k=k * over_fetch_factor
        )
        
        # Apply filters if any
        if filters:
            filtered_results = self.filter.filter_documents(raw_results, filters)
            # Return up to k results
            return filtered_results[:k]
        
        return raw_results[:k]
```

**Performance**: Fast and simple, works with existing FAISS setup

#### ChromaDB Approach (If you migrate)

**Strategy**: Native metadata filtering

```python
class ChromaFilteredRetriever:
    def search_with_filters(self, query, k=4, filters=None):
        """Use ChromaDB's native WHERE clause"""
        
        where_clause = {}
        
        if filters:
            if filters.get('require_captions'):
                where_clause['has_captions'] = True
            if filters.get('category'):
                where_clause['category'] = filters['category']
            if filters.get('quality_level'):
                where_clause['quality_level'] = {"$in": self._get_valid_levels(filters['quality_level'])}
                
        return self.vector_store.similarity_search(query, k=k, where=where_clause)
```

### 4. API Enhancements

**New Endpoints**:
```python
# GET /api/filters/options
# Returns available filter options with counts
{
    "categories": {
        "educational": 80,
        "daily_update": 200,
        "interview": 41,
        "special_event": 20
    },
    "quality_levels": {
        "high": 120,
        "medium": 52,
        "low": 20,
        "none": 149
    },
    "caption_stats": {
        "total_videos": 341,
        "with_captions": 192,
        "coverage_percentage": 56.3
    }
}

# GET /api/playlists
# Returns playlists with video counts
{
    "playlists": [
        {
            "id": "PLxxxxxx",
            "title": "Options Education Series",
            "video_count": 30
        }
    ]
}

# POST /api/ask
# Enhanced with simple filtering
{
    "question": "How do gamma squeezes work?",
    "require_captions": true,
    "category": "educational",
    "quality_level": "high",
    "date_range": "last_year",
    "playlist_ids": ["PLxxxxxx"],
    "num_sources": 4
}
```

### 5. UI Components

**Simple Filter Panel (modify existing app.js)**
```javascript
// Add to existing UI:
// - Caption toggle checkbox
// - Category dropdown
// - Quality dropdown  
// - Date range selector
// - Playlist multi-select (Phase 3)

// Example filter panel:
// ┌─ Filters ────────────────────────────┐
// │ ☑ Require Captions (192/341 videos)  │
// │                                      │
// │ Category: [All Categories ▼]         │
// │ Quality: [Any Quality ▼]             │
// │ Date: [All Time ▼]                   │
// │                                      │
// │ Quick Presets:                       │
// │ [Educational] [Recent] [Technical]   │
// └──────────────────────────────────────┘
```

## Performance Considerations

### Simple and Fast

1. **Minimal Over-fetching**
   ```python
   # Simple 3x over-fetch for filtered queries
   over_fetch_factor = 3 if filters else 1
   ```

2. **In-Memory Filtering**
   - All filtering happens in memory after retrieval
   - No database queries needed
   - Metadata already loaded with documents

3. **Pre-computed Values**
   - Categories inferred during loading
   - Quality scores calculated once
   - No runtime analysis needed

## Implementation Strategy

### Three Simple Phases

1. **Phase 1**: Caption Tracking & Basic Metadata (2-3 days)
   - Modify document loader to add metadata
   - Add has_captions boolean
   - Infer categories from titles
   - Add basic API endpoints for filter stats
   
2. **Phase 2**: Simple Quality & Keywords (2-3 days)
   - Calculate words-per-minute quality score
   - Count technical term occurrences
   - Add quality filtering to API
   
3. **Phase 3**: Playlist Organization (2-3 days)
   - Load playlist data from YouTube API
   - Add playlist filtering
   - Create preset filter combinations

### One-Time Data Reload

After implementing Phase 1, you'll need to reload documents once to add the enhanced metadata:
```bash
# Re-run document loader with enhancements
uv run python src/data_pipeline/document_loader_faiss.py
```

This will update all documents with the new metadata fields.

## Testing Strategy

### Simple Test Cases
- Category inference from titles
- Quality score calculation
- Filter combinations
- API endpoint responses

```python
# Test metadata enhancement
def test_category_inference():
    assert infer_category("AM HYPE Market Update") == "daily_update"
    assert infer_category("Options Education: Understanding Greeks") == "educational"
    assert infer_category("Interview with Market Expert") == "interview"
```

## Key Benefits

### What You Get
1. **Accessibility**: 192/341 videos are accessible with captions
2. **Organization**: Automatic categorization without manual work
3. **Quality Filtering**: Focus on high-quality content
4. **Simple Implementation**: No complex systems needed
5. **Future Ready**: Easy to extend with more patterns

### What You Avoid
1. **Complex Analysis**: No ML or NLP needed
2. **Database Overhead**: Everything in existing vector store
3. **Long Development**: 1 week vs 4 weeks
4. **Maintenance Burden**: Simple code, easy to maintain

## Conclusion

This simplified design provides practical content filtering that addresses real user needs - accessibility, quality, and organization - without the complexity of advanced analysis systems. By using simple pattern matching and basic calculations, we can deliver 80% of the value with 20% of the effort, maintaining the system's simplicity while significantly improving the user experience.