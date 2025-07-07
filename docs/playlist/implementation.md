# Simple Content Filtering Implementation Guide

> **Status**: 🔄 **Planning Phase** - Ready for implementation
> 
> **Current System**: Basic RAG pipeline functional with SpotGamma data (192/341 videos with captions)
> **This Document**: Step-by-step implementation plan for practical content filtering

## Overview

This guide provides a simple, practical implementation plan for adding content filtering to RAG-YouTube. By enhancing metadata during document loading and adding basic UI filters, we can dramatically improve the user experience with minimal effort.

**Core Principle**: Enhance existing document metadata with simple calculations and pattern matching. No new infrastructure needed.

**Prerequisites**: The current basic RAG system should be working. You'll reload documents once after Phase 1.

## Implementation Architecture

### Modified Components

```
src/
├── data_pipeline/
│   └── document_loader_faiss.py  # Add metadata enhancement
├── api/
│   ├── main.py                   # Add filter endpoints
│   ├── filters.py (new)          # Simple filtering logic
│   └── rag_engine.py             # Add filter support
└── static/
    ├── index.html                # Add filter UI
    └── app.js                    # Add filter logic
```

No new databases or complex systems - just enhancements to existing code.

## Implementation Phases

### Phase 1: Caption Tracking & Basic Metadata (2-3 days)

#### Step 1.1: Create Metadata Enhancer

**File**: `src/data_pipeline/metadata_enhancer.py` (new)

```python
#!/usr/bin/env python3
"""
Simple metadata enhancement for content filtering.
"""
import os
from typing import Dict, Optional

class SimpleMetadataEnhancer:
    """Add practical metadata during document loading."""
    
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
            "squeeze", "0dte", "spx", "vix", "skew", "flow", "hedge",
            "hedging", "dealer", "positioning", "exposure", "dix", "gex"
        ]
        
    def enhance_metadata(self, doc, video_data: Dict, caption_path: Optional[str] = None):
        """Add simple intelligence to document metadata."""
        
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
            
            # Get duration from contentDetails if available
            duration_seconds = 600  # default 10 minutes
            if 'contentDetails' in video_data and 'duration' in video_data['contentDetails']:
                # Parse ISO 8601 duration (e.g., "PT10M30S")
                duration_str = video_data['contentDetails']['duration']
                duration_seconds = self._parse_duration(duration_str)
            
            duration_minutes = duration_seconds / 60
            words_per_minute = word_count / max(duration_minutes, 1)
            
            # Normalize to 0-1 scale (150 words/minute = 1.0)
            doc.metadata['caption_quality'] = min(words_per_minute / 150, 1.0)
            doc.metadata['quality_level'] = self._score_to_level(doc.metadata['caption_quality'])
            doc.metadata['word_count'] = word_count
            doc.metadata['words_per_minute'] = round(words_per_minute, 1)
            
            # Count technical terms
            content_lower = doc.page_content.lower()
            term_count = sum(content_lower.count(term) for term in self.technical_terms)
            doc.metadata['technical_score'] = min(term_count / 20, 1.0)
            doc.metadata['technical_terms_found'] = term_count
        else:
            doc.metadata['caption_quality'] = 0.0
            doc.metadata['quality_level'] = 'none'
            doc.metadata['technical_score'] = 0.0
            doc.metadata['word_count'] = 0
            doc.metadata['words_per_minute'] = 0
            doc.metadata['technical_terms_found'] = 0
            
        # Add duration for future use
        doc.metadata['duration_seconds'] = duration_seconds if 'duration_seconds' in locals() else 600
        
        # Placeholder for playlist information (Phase 3)
        doc.metadata['playlist_ids'] = []
        doc.metadata['playlist_titles'] = []
        
        return doc
        
    def _infer_category(self, title_lower: str) -> str:
        """Simple category inference from title."""
        for category, patterns in self.category_patterns.items():
            if any(pattern in title_lower for pattern in patterns):
                return category
        return 'general'
        
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to quality level."""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        elif score > 0:
            return 'low'
        else:
            return 'none'
            
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        # Simple parser for YouTube durations like "PT10M30S"
        import re
        
        # Extract hours, minutes, seconds
        hours = 0
        minutes = 0
        seconds = 0
        
        # Match patterns
        h_match = re.search(r'(\d+)H', duration_str)
        m_match = re.search(r'(\d+)M', duration_str)
        s_match = re.search(r'(\d+)S', duration_str)
        
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))
        if s_match:
            seconds = int(s_match.group(1))
            
        return hours * 3600 + minutes * 60 + seconds
```

#### Step 1.2: Modify Document Loader

**File**: `src/data_pipeline/document_loader_faiss.py` (modify existing)

Add imports at the top:
```python
from .metadata_enhancer import SimpleMetadataEnhancer
```

Modify the document loading section:
```python
# Initialize enhancer
enhancer = SimpleMetadataEnhancer()

# In the loop where documents are created:
for video in videos_data:
    video_id = video['id']['videoId']
    
    # ... existing code to load caption ...
    
    # Create document
    doc = Document(
        page_content=caption_text,
        metadata={
            "source": video_id,
            "title": video['snippet']['title'],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": video['snippet']['publishedAt']
        }
    )
    
    # Enhance metadata
    caption_path = f"captions/{video_id}.txt"  # or wherever captions are stored
    doc = enhancer.enhance_metadata(doc, video, caption_path)
    
    documents.append(doc)
```

#### Step 1.3: Add Filter Statistics API

**File**: `src/api/main.py` (add to existing)

```python
@app.get("/api/filters/options")
async def get_filter_options():
    """Get available filter options with counts."""
    
    # Get all documents from vector store
    # This is a simple implementation - in production you might cache this
    all_docs = rag_engine.vector_store.get_all_documents()  # You'll need to implement this
    
    # Count categories
    categories = {}
    quality_levels = {}
    caption_count = 0
    
    for doc in all_docs:
        # Category counts
        category = doc.metadata.get('category', 'general')
        categories[category] = categories.get(category, 0) + 1
        
        # Quality level counts
        quality = doc.metadata.get('quality_level', 'none')
        quality_levels[quality] = quality_levels.get(quality, 0) + 1
        
        # Caption count
        if doc.metadata.get('has_captions', False):
            caption_count += 1
    
    return {
        "categories": categories,
        "quality_levels": quality_levels,
        "caption_stats": {
            "total_videos": len(all_docs),
            "with_captions": caption_count,
            "coverage_percentage": round((caption_count / len(all_docs)) * 100, 1) if all_docs else 0
        }
    }
```

#### Step 1.4: Add Caption Filter to UI

**File**: `static/index.html` (modify existing)

Add filter section above the search box:
```html
<div class="filter-section">
    <h3>Filters</h3>
    <div class="filter-row">
        <label>
            <input type="checkbox" id="requireCaptions" />
            Require Captions <span id="captionCount">(loading...)</span>
        </label>
    </div>
</div>
```

**File**: `static/app.js` (modify existing)

Add filter loading:
```javascript
// Load filter options on page load
async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filters/options');
        const data = await response.json();
        
        // Update caption count
        const captionSpan = document.getElementById('captionCount');
        captionSpan.textContent = `(${data.caption_stats.with_captions}/${data.caption_stats.total_videos} videos)`;
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', loadFilterOptions);

// Modify the askQuestion function to include filters
async function askQuestion() {
    const question = document.getElementById('question').value;
    const requireCaptions = document.getElementById('requireCaptions').checked;
    
    const requestBody = {
        question: question,
        num_sources: 4,
        require_captions: requireCaptions
    };
    
    // ... rest of existing code ...
}
```

### Phase 2: Simple Quality & Keywords (2-3 days)

#### Step 2.1: Create Filter Logic

**File**: `src/api/filters.py` (new)

```python
#!/usr/bin/env python3
"""
Simple content filtering logic.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class SimpleContentFilter:
    """In-memory filtering using enhanced metadata."""
    
    def filter_documents(self, documents: List, filters: Dict) -> List:
        """Apply filters to document list."""
        filtered = documents
        
        # Caption filter
        if filters.get('require_captions'):
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('has_captions', False)]
            
        # Category filter
        if filters.get('category'):
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('category') == filters['category']]
            
        # Quality filter
        if filters.get('quality_level'):
            quality_order = {'none': 0, 'low': 1, 'medium': 2, 'high': 3}
            min_level = quality_order.get(filters['quality_level'], 0)
            filtered = [doc for doc in filtered 
                       if quality_order.get(doc.metadata.get('quality_level', 'none'), 0) >= min_level]
            
        # Date filter
        if filters.get('date_range'):
            cutoff_date = self._get_cutoff_date(filters['date_range'])
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('published_at', '') >= cutoff_date]
            
        # Technical score filter (optional)
        if filters.get('min_technical_score'):
            filtered = [doc for doc in filtered 
                       if doc.metadata.get('technical_score', 0) >= filters['min_technical_score']]
            
        # Playlist filters (Phase 3)
        if filters.get('playlist_ids'):
            filtered = [doc for doc in filtered 
                       if any(pid in doc.metadata.get('playlist_ids', []) 
                             for pid in filters['playlist_ids'])]
                             
        if filters.get('exclude_playlist_ids'):
            filtered = [doc for doc in filtered 
                       if not any(pid in doc.metadata.get('playlist_ids', []) 
                                 for pid in filters['exclude_playlist_ids'])]
            
        return filtered
        
    def _get_cutoff_date(self, date_range: str) -> str:
        """Convert date range to cutoff date."""
        now = datetime.now()
        
        if date_range == 'last_week':
            cutoff = now - timedelta(days=7)
        elif date_range == 'last_month':
            cutoff = now - timedelta(days=30)
        elif date_range == 'last_year':
            cutoff = now - timedelta(days=365)
        else:
            return ''
            
        return cutoff.isoformat()
```

#### Step 2.2: Enhance RAG Engine

**File**: `src/api/rag_engine.py` (modify existing)

Add imports:
```python
from .filters import SimpleContentFilter
```

Modify the RAGEngine class:
```python
class RAGEngine:
    def __init__(self, config: Config):
        # ... existing init code ...
        self.filter = SimpleContentFilter()
        
    def ask(self, question: str, num_sources: int = 4, filters: Optional[Dict] = None):
        """Enhanced ask method with filtering."""
        
        # Determine over-fetch factor based on filters
        over_fetch_factor = 3 if filters else 1
        
        # Get more documents than needed
        raw_docs = self.vector_store.similarity_search(
            question, 
            k=num_sources * over_fetch_factor
        )
        
        # Apply filters if any
        if filters:
            docs = self.filter.filter_documents(raw_docs, filters)
            # Limit to requested number
            docs = docs[:num_sources]
        else:
            docs = raw_docs[:num_sources]
            
        # Continue with existing logic...
        context = self._format_context(docs)
        # etc...
```

#### Step 2.3: Update API Endpoints

**File**: `src/api/main.py` (modify existing)

Update the ask endpoint:
```python
from pydantic import BaseModel
from typing import Optional, List

class AskRequest(BaseModel):
    question: str
    num_sources: int = 4
    # Filters
    require_captions: Optional[bool] = False
    category: Optional[str] = None
    quality_level: Optional[str] = None  # high, medium, low
    date_range: Optional[str] = None     # last_week, last_month, last_year
    min_technical_score: Optional[float] = None
    # Phase 3
    playlist_ids: Optional[List[str]] = None
    exclude_playlist_ids: Optional[List[str]] = None

@app.post("/api/ask")
async def ask_question(request: AskRequest):
    """Enhanced ask endpoint with filtering."""
    
    # Build filter dict
    filters = {}
    if request.require_captions:
        filters['require_captions'] = True
    if request.category:
        filters['category'] = request.category
    if request.quality_level:
        filters['quality_level'] = request.quality_level
    if request.date_range:
        filters['date_range'] = request.date_range
    if request.min_technical_score:
        filters['min_technical_score'] = request.min_technical_score
    if request.playlist_ids:
        filters['playlist_ids'] = request.playlist_ids
    if request.exclude_playlist_ids:
        filters['exclude_playlist_ids'] = request.exclude_playlist_ids
        
    # Use enhanced ask method
    result = rag_engine.ask(
        request.question, 
        request.num_sources,
        filters=filters if filters else None
    )
    
    return result
```

#### Step 2.4: Enhance UI with More Filters

**File**: `static/index.html` (modify)

Replace the filter section:
```html
<div class="filter-section">
    <h3>Filters</h3>
    
    <div class="filter-row">
        <label>
            <input type="checkbox" id="requireCaptions" />
            Require Captions <span id="captionCount">(loading...)</span>
        </label>
    </div>
    
    <div class="filter-row">
        <label>Category:</label>
        <select id="categoryFilter">
            <option value="">All Categories</option>
            <option value="educational">Educational</option>
            <option value="daily_update">Daily Updates</option>
            <option value="interview">Interviews</option>
            <option value="special_event">Special Events</option>
        </select>
    </div>
    
    <div class="filter-row">
        <label>Quality:</label>
        <select id="qualityFilter">
            <option value="">Any Quality</option>
            <option value="high">High Quality</option>
            <option value="medium">Medium Quality</option>
            <option value="low">Low Quality</option>
        </select>
    </div>
    
    <div class="filter-row">
        <label>Date:</label>
        <select id="dateFilter">
            <option value="">All Time</option>
            <option value="last_week">Last 7 Days</option>
            <option value="last_month">Last 30 Days</option>
            <option value="last_year">Last Year</option>
        </select>
    </div>
    
    <!-- Quick Presets -->
    <div class="filter-row presets">
        <label>Quick Filters:</label>
        <button onclick="applyPreset('educational')">Educational</button>
        <button onclick="applyPreset('recent')">Recent</button>
        <button onclick="applyPreset('technical')">Technical</button>
    </div>
</div>
```

**File**: `static/style.css` (add)

```css
.filter-section {
    background: #f5f5f5;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 5px;
}

.filter-row {
    margin-bottom: 10px;
}

.filter-row label {
    display: inline-block;
    width: 100px;
}

.filter-row select {
    width: 200px;
}

.presets button {
    margin-left: 10px;
    padding: 5px 15px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

.presets button:hover {
    background: #0056b3;
}
```

**File**: `static/app.js` (modify)

Update filter loading and question asking:
```javascript
// Update loadFilterOptions to show category counts
async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filters/options');
        const data = await response.json();
        
        // Update caption count
        const captionSpan = document.getElementById('captionCount');
        captionSpan.textContent = `(${data.caption_stats.with_captions}/${data.caption_stats.total_videos} videos)`;
        
        // Optionally update category dropdown with counts
        const categorySelect = document.getElementById('categoryFilter');
        // Could dynamically add options with counts here
        
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Update askQuestion to include all filters
async function askQuestion() {
    const question = document.getElementById('question').value;
    
    const requestBody = {
        question: question,
        num_sources: 4,
        require_captions: document.getElementById('requireCaptions').checked,
        category: document.getElementById('categoryFilter').value || null,
        quality_level: document.getElementById('qualityFilter').value || null,
        date_range: document.getElementById('dateFilter').value || null
    };
    
    // ... rest of existing code ...
}

// Add preset function
function applyPreset(preset) {
    switch(preset) {
        case 'educational':
            document.getElementById('categoryFilter').value = 'educational';
            document.getElementById('qualityFilter').value = 'high';
            document.getElementById('requireCaptions').checked = true;
            break;
        case 'recent':
            document.getElementById('dateFilter').value = 'last_week';
            document.getElementById('categoryFilter').value = 'daily_update';
            break;
        case 'technical':
            document.getElementById('requireCaptions').checked = true;
            document.getElementById('qualityFilter').value = 'high';
            // Could add technical score filter if exposed
            break;
    }
}
```

### Phase 3: Playlist Organization (2-3 days)

#### Step 3.1: Fetch Playlist Data

**File**: `src/data_pipeline/playlist_fetcher.py` (new)

```python
#!/usr/bin/env python3
"""
Fetch playlist data from YouTube API.
"""
import os
import json
from typing import List, Dict
from googleapiclient.discovery import build

class PlaylistFetcher:
    """Fetch playlists and video mappings from YouTube."""
    
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def fetch_channel_playlists(self, channel_id: str) -> List[Dict]:
        """Fetch all playlists for a channel."""
        playlists = []
        next_page_token = None
        
        while True:
            request = self.youtube.playlists().list(
                part='snippet,contentDetails',
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get('items', []):
                playlist = {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'video_count': item['contentDetails']['itemCount'],
                    'videos': []  # Will be populated later
                }
                playlists.append(playlist)
                
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        return playlists
        
    def fetch_playlist_videos(self, playlist_id: str) -> List[str]:
        """Fetch all video IDs in a playlist."""
        video_ids = []
        next_page_token = None
        
        while True:
            request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
                
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        return video_ids
        
    def fetch_all_playlists_with_videos(self, channel_id: str) -> Dict:
        """Fetch all playlists and their video mappings."""
        print(f"Fetching playlists for channel {channel_id}...")
        playlists = self.fetch_channel_playlists(channel_id)
        
        # Create video to playlist mapping
        video_to_playlists = {}
        
        for playlist in playlists:
            print(f"Fetching videos for playlist: {playlist['title']}")
            video_ids = self.fetch_playlist_videos(playlist['id'])
            playlist['videos'] = video_ids
            
            # Build reverse mapping
            for video_id in video_ids:
                if video_id not in video_to_playlists:
                    video_to_playlists[video_id] = []
                video_to_playlists[video_id].append({
                    'id': playlist['id'],
                    'title': playlist['title']
                })
                
        return {
            'playlists': playlists,
            'video_to_playlists': video_to_playlists
        }

# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python playlist_fetcher.py CHANNEL_ID")
        sys.exit(1)
        
    channel_id = sys.argv[1]
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        sys.exit(1)
        
    fetcher = PlaylistFetcher(api_key)
    data = fetcher.fetch_all_playlists_with_videos(channel_id)
    
    # Save to file
    with open('playlists.json', 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"\nSaved {len(data['playlists'])} playlists to playlists.json")
    print(f"Total videos mapped: {len(data['video_to_playlists'])}")
```

#### Step 3.2: Update Document Loader with Playlists

**File**: `src/data_pipeline/document_loader_faiss.py` (modify)

Add playlist loading:
```python
# At the beginning of the main function
# Load playlist data if available
playlist_data = {}
if os.path.exists('playlists.json'):
    with open('playlists.json', 'r') as f:
        playlist_json = json.load(f)
        playlist_data = playlist_json.get('video_to_playlists', {})
    print(f"Loaded playlist data for {len(playlist_data)} videos")

# In the document creation loop, after enhancing metadata:
# Add playlist information
if video_id in playlist_data:
    doc.metadata['playlist_ids'] = [p['id'] for p in playlist_data[video_id]]
    doc.metadata['playlist_titles'] = [p['title'] for p in playlist_data[video_id]]
```

#### Step 3.3: Add Playlist API Endpoint

**File**: `src/api/main.py` (add)

```python
@app.get("/api/playlists")
async def get_playlists():
    """Get available playlists with video counts."""
    
    # Load playlist data
    if not os.path.exists('playlists.json'):
        return {"playlists": [], "message": "No playlist data available"}
        
    with open('playlists.json', 'r') as f:
        data = json.load(f)
        
    # Format for frontend
    playlists = []
    for playlist in data.get('playlists', []):
        playlists.append({
            "id": playlist['id'],
            "title": playlist['title'],
            "video_count": playlist['video_count'],
            "description": playlist.get('description', '')[:100]  # First 100 chars
        })
        
    return {"playlists": playlists}
```

#### Step 3.4: Add Playlist Filter to UI

**File**: `static/index.html` (add to filter section)

```html
<!-- Add after the date filter -->
<div class="filter-row" id="playlistSection" style="display: none;">
    <label>Playlists:</label>
    <select id="playlistFilter" multiple size="4">
        <!-- Options will be loaded dynamically -->
    </select>
    <br>
    <small>Hold Ctrl/Cmd to select multiple</small>
</div>
```

**File**: `static/app.js` (modify)

Add playlist loading:
```javascript
// Add to loadFilterOptions function
async function loadFilterOptions() {
    try {
        // ... existing code ...
        
        // Load playlists
        const playlistResponse = await fetch('/api/playlists');
        const playlistData = await playlistResponse.json();
        
        if (playlistData.playlists && playlistData.playlists.length > 0) {
            const playlistSelect = document.getElementById('playlistFilter');
            const playlistSection = document.getElementById('playlistSection');
            
            // Show playlist section
            playlistSection.style.display = 'block';
            
            // Add options
            playlistData.playlists.forEach(playlist => {
                const option = document.createElement('option');
                option.value = playlist.id;
                option.textContent = `${playlist.title} (${playlist.video_count} videos)`;
                playlistSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Update askQuestion to include playlists
async function askQuestion() {
    const question = document.getElementById('question').value;
    
    // Get selected playlists
    const playlistSelect = document.getElementById('playlistFilter');
    const selectedPlaylists = Array.from(playlistSelect.selectedOptions)
        .map(option => option.value);
    
    const requestBody = {
        question: question,
        num_sources: 4,
        require_captions: document.getElementById('requireCaptions').checked,
        category: document.getElementById('categoryFilter').value || null,
        quality_level: document.getElementById('qualityFilter').value || null,
        date_range: document.getElementById('dateFilter').value || null,
        playlist_ids: selectedPlaylists.length > 0 ? selectedPlaylists : null
    };
    
    // ... rest of existing code ...
}
```

## Testing & Deployment

### Testing

**Test Metadata Enhancement**:
```python
# test/test_metadata_enhancer.py
from src.data_pipeline.metadata_enhancer import SimpleMetadataEnhancer

def test_category_inference():
    enhancer = SimpleMetadataEnhancer()
    
    assert enhancer._infer_category("am hype market update") == "daily_update"
    assert enhancer._infer_category("options education: understanding greeks") == "educational"
    assert enhancer._infer_category("interview with market expert") == "interview"
    assert enhancer._infer_category("fomc decision analysis") == "special_event"
    assert enhancer._infer_category("random video title") == "general"

def test_quality_scoring():
    enhancer = SimpleMetadataEnhancer()
    
    # Test quality levels
    assert enhancer._score_to_level(0.9) == "high"
    assert enhancer._score_to_level(0.6) == "medium"
    assert enhancer._score_to_level(0.3) == "low"
    assert enhancer._score_to_level(0.0) == "none"
```

**Test Filtering**:
```python
# test/test_filters.py
from src.api.filters import SimpleContentFilter

def test_caption_filter():
    filter = SimpleContentFilter()
    
    docs = [
        Mock(metadata={'has_captions': True}),
        Mock(metadata={'has_captions': False}),
    ]
    
    filtered = filter.filter_documents(docs, {'require_captions': True})
    assert len(filtered) == 1
    assert filtered[0].metadata['has_captions'] == True
```

### Deployment Steps

#### Step 1: Initial Setup
```bash
# 1. Implement Phase 1 code changes
# 2. Test the metadata enhancer
uv run python -m pytest test/test_metadata_enhancer.py

# 3. Reload documents with enhanced metadata
uv run python src/data_pipeline/document_loader_faiss.py

# 4. Start server and test
./run_fastapi.sh
```

#### Step 2: Verify Filtering
```bash
# Test the new API endpoint
curl http://localhost:8000/api/filters/options

# Should return:
# {
#   "categories": {...},
#   "quality_levels": {...},
#   "caption_stats": {...}
# }
```

#### Step 3: Fetch Playlists (Phase 3)
```bash
# Get SpotGamma channel ID from any video URL
CHANNEL_ID="UCRa4yF0KVctjFkaKWAKvopg"  # SpotGamma

# Fetch playlists
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/playlist_fetcher.py $CHANNEL_ID

# Reload documents with playlist data
uv run python src/data_pipeline/document_loader_faiss.py
```

## Implementation Timeline

### Phase 1: Caption & Categories (Day 1-2)
- **Day 1**: 
  - Create metadata_enhancer.py
  - Modify document_loader_faiss.py
  - Add filter statistics API
- **Day 2**:
  - Add caption checkbox to UI
  - Test and reload documents
  - Verify filtering works

### Phase 2: Quality & Keywords (Day 3-4)
- **Day 3**:
  - Create filters.py
  - Enhance RAG engine
  - Update API endpoints
- **Day 4**:
  - Add dropdowns to UI
  - Implement presets
  - Test combined filtering

### Phase 3: Playlists (Day 5-6)
- **Day 5**:
  - Create playlist_fetcher.py
  - Fetch SpotGamma playlists
  - Update document loader
- **Day 6**:
  - Add playlist API
  - Add playlist UI
  - Test full system

### Final Day: Polish (Day 7)
- Documentation
- Performance testing
- User guide

## Key Benefits Summary

### What You Get
1. **Accessibility**: Filter for 192 captioned videos
2. **Organization**: Automatic categorization
3. **Quality Focus**: High-quality content discovery
4. **Playlist Support**: YouTube's existing structure
5. **Simple Implementation**: 1 week, minimal complexity

### What You Avoid
1. **Complex Databases**: Everything in vector store
2. **ML/NLP Systems**: Simple pattern matching
3. **Long Development**: Days not weeks
4. **Maintenance Burden**: Easy to understand code

## Common Issues & Solutions

### Issue: Duration not available
Some videos might not have duration in contentDetails. Solution:
```python
# Use a reasonable default
duration_seconds = video_data.get('contentDetails', {}).get('duration', 600)
```

### Issue: Filter returns no results
When filters are too restrictive:
```python
# Increase over-fetch factor
over_fetch_factor = 5 if very_restrictive else 3
```

### Issue: Playlist API quota
YouTube API has quotas. Solution:
- Cache playlists.json
- Only fetch when needed
- Reuse existing data

## Conclusion

This simplified implementation provides practical content filtering that solves real user problems - accessibility, organization, and quality discovery - without the complexity of advanced systems. By using simple patterns and existing data, we deliver significant value with minimal effort and maintenance.