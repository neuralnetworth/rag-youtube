# Practical Content Filtering Feature Specification

> **Status**: 🔄 **Planning Phase** - Simplified enhancement ready for implementation
> 
> **Current System**: Basic RAG with SpotGamma channel data (192/341 videos with captions)
> **This Document**: Feature specification for practical filtering using simple metadata enhancement

## Overview

This feature introduces practical content filtering by enhancing video metadata during document loading. Using simple pattern matching and basic calculations, we add caption availability tracking, title-based categorization, quality scoring, and playlist organization. This lightweight approach dramatically improves the user experience without complex infrastructure.

## Motivation

Current issues that simple filtering can solve:

### Accessibility Gap
- **56% Caption Coverage**: Only 192 of 341 videos have captions
- **Mixed Results**: Queries return both accessible and inaccessible content
- **No Visibility**: Users can't filter for captioned content

### Content Organization
- **Flat Structure**: All 341 videos treated equally
- **No Categories**: Daily updates mixed with educational content
- **Quality Unknown**: No way to find high-quality transcriptions

### Simple Solutions
- **Caption Filter**: Let users see only accessible content
- **Title Categories**: Infer content type from video titles
- **Basic Quality**: Score captions by words-per-minute
- **Playlist Groups**: Use YouTube's existing organization

With minimal effort, we can provide powerful filtering that addresses real user needs.

## User Stories

### Story 1: Accessibility-First User
**As a** hearing-impaired trader  
**I want to** see only videos with captions  
**So that** I can access all content

**Solution**: Simple checkbox "Require Captions" filters to 192 accessible videos

### Story 2: Educational Focus
**As a** beginner learning options  
**I want to** see educational content, not daily market updates  
**So that** I can learn fundamentals

**Solution**: Category dropdown filters "educational" content (~80 videos)

### Story 3: Quality Seeker
**As a** researcher  
**I want to** find videos with detailed, high-quality captions  
**So that** I can search and cite specific content

**Solution**: Quality filter shows videos with "high" caption quality (150+ words/minute)

### Story 4: Recent Content
**As a** active trader  
**I want to** see only recent market updates  
**So that** I get current information

**Solution**: Date filter "Last 7 days" + category "daily_update"

### Story 5: Organized Learning
**As a** systematic learner  
**I want to** follow structured playlists  
**So that** I learn in the right order

**Solution**: Playlist filter to follow "Options Education Series"

## Feature Capabilities

### Phase 1: Caption & Category Basics
- **Caption Tracking**: Boolean flag for each video (has_captions: true/false)
- **Title Categories**: Automatic categorization from title patterns
  - "daily_update": Market updates, AM/PM HYPE
  - "educational": Tutorials, education series
  - "interview": Podcasts and conversations
  - "special_event": FOMC, earnings, major events
- **Basic Stats**: Show counts for each filter option
- **Simple API**: New endpoints for filter options

### Phase 2: Quality & Keywords
- **Quality Score**: Words-per-minute calculation
  - High: 150+ words/minute
  - Medium: 50-150 words/minute  
  - Low: <50 words/minute
- **Technical Keywords**: Count occurrences of options terminology
- **Enhanced Filtering**: Combine multiple filter dimensions
- **Filter Preview**: Show result count before searching

### Phase 3: Playlist Organization  
- **Playlist Data**: Load from YouTube API
- **Video Mapping**: Track which videos belong to which playlists
- **Playlist Filter**: Include/exclude specific playlists
- **Smart Presets**: Pre-configured filter combinations
  - "Educational": category=educational + high quality + has captions
  - "Recent": last 7 days + daily updates
  - "Technical": high technical score + has captions

## Benefits

### Immediate Value
1. **Accessibility**: 192 videos become discoverable by caption status
2. **Organization**: Automatic categorization without manual tagging
3. **Quality Focus**: Find videos with comprehensive transcripts
4. **Time Savings**: Filter out irrelevant content types
5. **Simple UI**: Intuitive checkboxes and dropdowns

### For Different Users
- **Hearing-Impaired**: 100% accessible results with caption filter
- **Beginners**: Educational content without market noise
- **Researchers**: High-quality captions for detailed analysis
- **Active Traders**: Recent updates in specific categories
- **Content Creators**: See which content needs captions

### Technical Benefits
1. **No Infrastructure**: Uses existing vector store
2. **Fast Implementation**: 1 week total development
3. **Low Maintenance**: Simple pattern matching
4. **Future-Proof**: Easy to add new patterns/categories

## Success Metrics

### Usage Metrics
1. **Filter Adoption**: % of queries using filters (target: 30%+)
2. **Caption Filter Usage**: % using "Require Captions" (target: 20%+)
3. **Category Distribution**: Which categories are most searched

### Quality Metrics
4. **Result Relevance**: Higher satisfaction with filtered results
5. **Accessibility Coverage**: % of results that are accessible
6. **Query Efficiency**: Fewer follow-up queries needed

### Technical Metrics
7. **Performance**: Filtering adds <100ms to query time
8. **Accuracy**: 90%+ correct category inference
9. **Coverage**: 95%+ videos successfully categorized

## Example Use Cases

### Current SpotGamma Data
```
Total: 341 videos
├── With Captions: 192 (56.3%)
├── Categories (estimated):
│   ├── Daily Updates: ~200 videos
│   ├── Educational: ~80 videos  
│   ├── Interviews: ~41 videos
│   └── Special Events: ~20 videos
└── Quality Distribution (of captioned):
    ├── High Quality: ~120 videos
    ├── Medium Quality: ~52 videos
    └── Low Quality: ~20 videos
```

### Filter Examples

1. **Accessibility First**
   - Query: "What is gamma?"
   - Filters: ☑ Require Captions
   - Result: 192 accessible videos (instead of all 341)

2. **Educational Focus**
   - Query: "Options basics"
   - Filters: Category = "Educational", ☑ Require Captions
   - Result: ~75 educational videos with captions

3. **High Quality Research**
   - Query: "Gamma squeeze examples"
   - Filters: Quality = "High", ☑ Require Captions
   - Result: ~120 videos with detailed transcripts

4. **Recent Updates**
   - Query: "Market analysis"
   - Filters: Date = "Last 7 days", Category = "Daily Update"
   - Result: This week's market updates only

5. **Quick Presets**
   - Click "Educational" preset
   - Auto-applies: Educational + High Quality + Captions
   - Perfect for structured learning

## Feature Comparison

| Capability | Current System | With Simple Filtering |
|------------|----------------|----------------------|
| **Caption Tracking** | Unknown | ✓ has_captions flag |
| **Accessibility** | Mixed results | ✓ Filter for captions only |
| **Categories** | None | ✓ Inferred from titles |
| **Quality** | Unknown | ✓ Words-per-minute score |
| **Date Filtering** | None | ✓ Recent content filter |
| **Technical Content** | Unknown | ✓ Keyword scoring |
| **Playlists** | Not used | ✓ Filter by playlist (Phase 3) |
| **UI** | Search only | ✓ Filter checkboxes/dropdowns |
| **Implementation** | - | 1 week |
| **Maintenance** | - | Minimal |

## Implementation Approach

### Three Simple Phases

**Phase 1: Caption & Categories** (2-3 days)
- Modify document_loader_faiss.py to add metadata
- Add caption detection and category inference
- Create filter statistics API endpoint
- Add caption checkbox to UI

**Phase 2: Quality & Keywords** (2-3 days)
- Calculate quality scores during loading
- Count technical term occurrences
- Add quality and category dropdowns
- Enhance API with combined filtering

**Phase 3: Playlists** (2-3 days)
- Fetch playlist data from YouTube API
- Map videos to playlists
- Add playlist multi-select filter
- Create filter presets

### Why This Works
- **Incremental Value**: Each phase provides immediate benefits
- **Low Risk**: Simple changes to existing code
- **User Testing**: Get feedback after each phase
- **Maintainable**: Easy to understand and modify

## Future Possibilities

Once the basic system is working, you could consider:

1. **More Categories**: Add patterns as you discover them
2. **Better Quality Metrics**: Refine the scoring algorithm
3. **More Keywords**: Expand technical term list
4. **Smart Defaults**: Learn from user behavior
5. **Export Filters**: Save/share filter combinations

But these are optional - the basic system provides tremendous value as-is.

## Conclusion

Practical Content Filtering transforms RAG-YouTube from a basic search tool into an accessible, organized knowledge base. By adding simple metadata during document loading, we solve real user problems:

- **Accessibility**: Hearing-impaired users can find content they can actually use
- **Organization**: Beginners aren't overwhelmed by daily market noise
- **Quality**: Researchers can find detailed, searchable transcripts
- **Efficiency**: Everyone saves time with focused results

Best of all, this requires no complex infrastructure - just smart use of existing data. The result is a dramatically improved user experience with minimal development effort.