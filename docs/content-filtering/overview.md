# Content Filtering System Overview

## Introduction

The RAG-YouTube content filtering system enables precise control over which documents are used for answer generation. This system was designed to improve search relevance by allowing users to filter content based on various metadata attributes.

## Architecture

### Core Components

1. **Metadata Enhancement** (`src/data_pipeline/metadata_enhancer.py`)
   - Processes raw video metadata during document loading
   - Infers categories from video titles and descriptions
   - Calculates quality scores based on transcript analysis
   - Normalizes data formats for consistent filtering

2. **Document Filtering** (`src/api/filters.py`)
   - In-memory filtering of retrieved documents
   - Implements over-fetching strategy for quality results
   - Provides filter statistics for UI display

3. **RAG Engine Integration** (`src/api/rag_engine.py`)
   - Applies filters during document retrieval
   - Manages over-fetching when filters are active
   - Provides filter statistics endpoint

4. **Web Interface** (`static/app.js`, `static/index.html`)
   - User-friendly filter controls
   - Real-time filter statistics
   - Persistent filter state during session

## Filter Types

### 1. Caption Availability Filter
- **Purpose**: Exclude videos without transcripts
- **UI**: Checkbox "Require captions"
- **Implementation**: Checks `has_captions` metadata field

### 2. Category Filter
- **Purpose**: Filter by content type
- **Categories**:
  - `daily_update`: Market updates, daily analysis
  - `educational`: Tutorials, explainers
  - `interview`: Conversations, Q&A sessions
  - `special_event`: OPEX, earnings, major events
  - `uncategorized`: Videos that don't match patterns

### 3. Quality Score Filter
- **Purpose**: Filter by content density and technical depth
- **Levels**:
  - `high`: 120+ WPM, 5+ technical keywords
  - `medium`: 80+ WPM, 2+ technical keywords
  - `low`: 40+ WPM
  - `none`: Below thresholds

### 4. Date Range Filter
- **Purpose**: Limit results to specific time periods
- **UI**: Date picker inputs for start/end dates
- **Format**: ISO date format (YYYY-MM-DD)

## Technical Implementation

### Category Inference

Categories are inferred using pattern matching on video titles:

```python
CATEGORY_PATTERNS = {
    'daily_update': [
        r'daily.*update',
        r'market.*update',
        r'daily.*market',
        # ... more patterns
    ],
    'educational': [
        r'what.*is',
        r'how.*to',
        r'tutorial',
        # ... more patterns
    ]
}
```

### Quality Scoring

Quality scores are calculated based on:
1. **Words Per Minute (WPM)**: Transcript word count / video duration
2. **Technical Keyword Density**: Count of domain-specific terms

```python
TECHNICAL_KEYWORDS = [
    'gamma', 'delta', 'theta', 'vega', 'implied volatility',
    'options', 'calls', 'puts', 'strike', 'expiration',
    # ... more keywords
]
```

### Over-Fetching Strategy

When filters are active, the system requests 3x the desired number of documents:

```python
def calculate_over_fetch(num_requested, active_filters):
    if active_filters:
        return num_requested * 3
    return num_requested
```

This ensures sufficient documents remain after filtering.

## Data Flow

1. **Document Loading Phase**:
   ```
   Video Metadata → Metadata Enhancer → Enhanced Metadata → Vector Store
   ```

2. **Search Phase**:
   ```
   User Query → RAG Engine → Vector Search (3x docs) → Filter → Results
   ```

## Performance Considerations

- **In-Memory Filtering**: No additional database queries
- **Efficient Metadata**: Minimal storage overhead
- **Lazy Statistics**: Calculated on-demand
- **Cached Embeddings**: Filters don't affect vector search

## Configuration

No configuration required - the system automatically:
- Infers categories from content
- Calculates quality scores
- Tracks caption availability
- Determines date ranges from data