# Content Filtering Technical Reference

## API Reference

### Endpoints

#### GET `/api/filters/options`

Returns available filter options and statistics.

**Response Format**:
```json
{
  "total_documents": 2413,
  "categories": {
    "daily_update": 45,
    "educational": 78,
    "interview": 23,
    "special_event": 89,
    "uncategorized": 156
  },
  "quality_levels": {
    "high": 34,
    "medium": 67,
    "low": 89,
    "none": 201
  },
  "caption_coverage": {
    "with_captions": 192,
    "without_captions": 149,
    "percentage": 56.3
  },
  "date_range": {
    "earliest": "2023-01-15",
    "latest": "2024-12-20"
  }
}
```

#### POST `/api/ask`

Accepts filter parameters in the request body.

**Request Format**:
```json
{
  "question": "What is gamma?",
  "num_sources": 4,
  "filters": {
    "require_captions": true,
    "categories": ["educational"],
    "quality_levels": ["high", "medium"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  }
}
```

## Data Structures

### Enhanced Metadata Schema

```python
{
    # Original fields
    "video_id": "abc123",
    "title": "Understanding Options Greeks",
    "description": "...",
    "url": "https://youtube.com/watch?v=abc123",
    "published_date": "2024-03-15",
    "duration": 900,  # seconds
    
    # Enhanced fields
    "has_captions": true,
    "category": "educational",
    "quality_score": "high",
    "words_per_minute": 145,
    "technical_keyword_count": 8,
    "word_count": 2175
}
```

### Filter Object Schema

```typescript
interface Filters {
  require_captions?: boolean;
  categories?: string[];
  quality_levels?: string[];
  date_from?: string;  // ISO date format
  date_to?: string;    // ISO date format
}
```

## Class Reference

### MetadataEnhancer

```python
class MetadataEnhancer:
    """Enhances video metadata with inferred categories and quality scores."""
    
    CATEGORY_PATTERNS: Dict[str, List[str]]
    TECHNICAL_KEYWORDS: List[str]
    
    def enhance_metadata(self, metadata: Dict) -> Dict:
        """Main entry point for metadata enhancement."""
    
    def _infer_category(self, title: str) -> str:
        """Infer category from video title using pattern matching."""
    
    def _calculate_quality(self, content: str, duration: int) -> Dict:
        """Calculate quality metrics based on transcript density."""
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and normalize date strings."""
    
    def get_filter_statistics(self, documents: List[Dict]) -> Dict:
        """Calculate statistics for filter options."""
```

### DocumentFilter

```python
class DocumentFilter:
    """Filters documents based on metadata criteria."""
    
    def __init__(self):
        self.filters = {}
    
    def set_filters(self, filters: Dict[str, Any]):
        """Set active filters."""
    
    def apply_filters(self, documents: List[Dict]) -> List[Dict]:
        """Apply filters to document list."""
    
    def calculate_over_fetch(self, num_requested: int, active_filters: bool) -> int:
        """Calculate how many documents to fetch when filtering."""
    
    def has_active_filters(self) -> bool:
        """Check if any filters are active."""
```

## Configuration

### Category Patterns

Categories are inferred using regex patterns defined in `metadata_enhancer.py`:

```python
CATEGORY_PATTERNS = {
    'daily_update': [
        r'daily.*update',
        r'market.*update',
        r'daily.*market',
        r'morning.*update',
        r'closing.*bell',
        r'market.*close',
        r'today.*market'
    ],
    'educational': [
        r'what.*is',
        r'how.*to',
        r'tutorial',
        r'guide',
        r'explain',
        r'learn',
        r'basics',
        r'introduction'
    ],
    'interview': [
        r'interview',
        r'conversation.*with',
        r'talks.*with',
        r'discussion.*with',
        r'q\s*&\s*a',
        r'ask.*me.*anything'
    ],
    'special_event': [
        r'opex',
        r'fomc',
        r'earnings',
        r'live.*stream',
        r'special.*event',
        r'breaking'
    ]
}
```

### Quality Thresholds

```python
# Words per minute thresholds
HIGH_WPM = 120
MEDIUM_WPM = 80
LOW_WPM = 40

# Technical keyword thresholds
HIGH_KEYWORDS = 5
MEDIUM_KEYWORDS = 2
```

### Technical Keywords

```python
TECHNICAL_KEYWORDS = [
    # Greeks
    'gamma', 'delta', 'theta', 'vega', 'rho',
    
    # Options terms
    'implied volatility', 'iv', 'options', 'calls', 'puts',
    'strike', 'expiration', 'assignment', 'exercise',
    
    # Market terms
    'support', 'resistance', 'breakout', 'trend',
    'bullish', 'bearish', 'squeeze', 'momentum',
    
    # Technical indicators
    'rsi', 'macd', 'moving average', 'bollinger',
    'fibonacci', 'pivot', 'vwap', 'volume'
]
```

## Filter Logic Details

### AND Logic Implementation

All filters use AND logic - a document must pass ALL active filters:

```python
def _passes_all_filters(self, doc_metadata):
    # Caption filter
    if self.filters.get('require_captions'):
        if not doc_metadata.get('has_captions'):
            return False
    
    # Category filter
    if self.filters.get('categories'):
        if doc_metadata.get('category') not in self.filters['categories']:
            return False
    
    # Quality filter
    if self.filters.get('quality_levels'):
        if doc_metadata.get('quality_score') not in self.filters['quality_levels']:
            return False
    
    # Date range filter
    if self.filters.get('date_from'):
        if doc_metadata.get('published_date') < self.filters['date_from']:
            return False
    
    if self.filters.get('date_to'):
        if doc_metadata.get('published_date') > self.filters['date_to']:
            return False
    
    return True
```

### Over-Fetching Strategy

The system requests extra documents when filters are active:

```python
def calculate_over_fetch(self, num_requested: int, active_filters: bool) -> int:
    """
    When filters are active, fetch 3x the requested documents
    to ensure we have enough after filtering.
    """
    if active_filters:
        return min(num_requested * 3, 100)  # Cap at 100 for performance
    return num_requested
```

## Performance Characteristics

- **Metadata Enhancement**: O(1) per document
- **Filter Application**: O(n) where n is number of documents
- **Memory Usage**: ~100 bytes additional metadata per document
- **Response Time Impact**: <50ms for typical queries

## Integration Points

1. **Document Loading**: Metadata enhanced during initial load
2. **Vector Search**: Standard similarity search unaffected
3. **Result Filtering**: Applied post-search, pre-ranking
4. **Response Generation**: Uses filtered documents only

## Error Handling

Common error scenarios and handling:

1. **Missing Metadata Fields**: Use sensible defaults
2. **Invalid Date Formats**: Fall back to original string
3. **Pattern Matching Failures**: Assign "uncategorized"
4. **Empty Filter Results**: Return message about refining filters