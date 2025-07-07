# Unified Content Intelligence Implementation Guide

> **Status**: 🔄 **Planning Phase** - Implementation roadmap for future development
> 
> **Current System**: Basic RAG pipeline functional with SpotGamma data (192/341 videos with captions)
> **This Document**: Step-by-step implementation plan for unified content intelligence system

## Overview

This guide provides a comprehensive implementation roadmap for building a unified content intelligence system that analyzes YouTube channels across multiple dimensions in a single, efficient pass. The unified approach delivers complete content understanding from day one, avoiding the inefficiencies of separate analysis systems.

**Core Principle**: One analysis pass captures all content dimensions - quality, organization, patterns, and relationships - providing a rich intelligence foundation for advanced retrieval.

**Prerequisites**: The current basic RAG system should be working before implementing these enhancements.

## Implementation Architecture

### Core Components

```
UnifiedContentAnalyzer/
├── analyzers/
│   ├── caption_quality.py      # Advanced caption assessment
│   ├── content_patterns.py     # Pattern recognition
│   ├── playlist_coherence.py   # Organizational analysis
│   └── relationships.py        # Content relationship discovery
├── intelligence/
│   ├── database.py            # SQLite intelligence storage
│   ├── models.py              # Intelligence data models
│   └── synthesizer.py         # Combine analysis results
├── api/
│   ├── endpoints.py           # New API endpoints
│   └── filters.py             # Multi-dimensional filtering
└── unified_analyzer.py        # Main orchestrator
```

## Implementation Phases

### Phase 1: Unified Content Analyzer Core

#### Step 1.1: Create Unified Analyzer Framework

**File**: `src/content_intelligence/unified_analyzer.py`

```python
#!/usr/bin/env python3
"""
Unified Content Intelligence Analyzer - Single pass analysis of all content dimensions.
"""
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

from .analyzers import (
    CaptionQualityAnalyzer,
    ContentPatternAnalyzer, 
    PlaylistCoherenceAnalyzer,
    RelationshipDiscoverer
)
from .intelligence import (
    ContentIntelligenceDB,
    VideoIntelligence,
    ChannelInsights
)

class UnifiedContentAnalyzer:
    """Orchestrates comprehensive content analysis across all dimensions."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize component analyzers
        self.caption_analyzer = CaptionQualityAnalyzer(config)
        self.pattern_analyzer = ContentPatternAnalyzer(config)
        self.playlist_analyzer = PlaylistCoherenceAnalyzer(config)
        self.relationship_analyzer = RelationshipDiscoverer(config)
        
        # Intelligence storage
        self.intelligence_db = ContentIntelligenceDB(config['db_path'])
        
        # Thread pool for parallel analysis
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def analyze_channel_comprehensive(self, 
                                          channel_id: str,
                                          force_refresh: bool = False) -> ChannelInsights:
        """
        Perform complete channel analysis in single pass.
        
        Returns comprehensive intelligence about the channel including:
        - Caption quality assessment for all videos
        - Content pattern recognition and categorization
        - Playlist coherence and organization analysis
        - Video relationship discovery
        - Aggregated insights and recommendations
        """
        self.logger.info(f"Starting unified analysis for channel {channel_id}")
        
        # Check cache unless forced refresh
        if not force_refresh:
            cached = self.intelligence_db.get_cached_analysis(channel_id)
            if cached and self._is_cache_valid(cached):
                self.logger.info("Returning cached analysis")
                return cached
        
        # Load all data sources
        videos = await self._load_videos()
        playlists = await self._fetch_playlists(channel_id) if self.config['analyze_playlists'] else []
        caption_files = self._scan_caption_files()
        
        # Run parallel analysis
        analysis_tasks = [
            self._analyze_captions(videos, caption_files),
            self._analyze_patterns(videos),
            self._analyze_playlists(videos, playlists),
            self._discover_relationships(videos)
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        
        # Synthesize results
        channel_insights = self._synthesize_intelligence(
            channel_id=channel_id,
            caption_analysis=results[0],
            pattern_analysis=results[1],
            playlist_analysis=results[2],
            relationships=results[3]
        )
        
        # Store in database
        self.intelligence_db.store_analysis(channel_insights)
        
        # Generate reports
        await self._generate_reports(channel_insights)
        
        return channel_insights
    
    async def _analyze_captions(self, videos: List[Dict], caption_files: Dict[str, str]) -> Dict:
        """Analyze caption quality across all videos."""
        self.logger.info("Analyzing caption quality...")
        
        caption_results = {}
        total_videos = len(videos)
        captioned_count = 0
        
        # Batch process for efficiency
        for video in videos:
            video_id = video['id']['videoId']
            
            if video_id in caption_files:
                captioned_count += 1
                
                # Detailed quality assessment
                quality_assessment = await self.caption_analyzer.assess_quality(
                    caption_file=caption_files[video_id],
                    video_metadata=video,
                    check_technical_terms=True,
                    analyze_timestamps=True,
                    check_speaker_labels=True
                )
                
                caption_results[video_id] = quality_assessment
            else:
                caption_results[video_id] = {
                    'available': False,
                    'quality_score': 0.0,
                    'issues': ['No captions available']
                }
        
        # Aggregate statistics
        quality_distribution = self._calculate_quality_distribution(caption_results)
        
        return {
            'total_videos': total_videos,
            'captioned_videos': captioned_count,
            'coverage_percentage': (captioned_count / total_videos) * 100,
            'individual_results': caption_results,
            'quality_distribution': quality_distribution,
            'recommendations': self._generate_caption_recommendations(caption_results)
        }
    
    async def _analyze_patterns(self, videos: List[Dict]) -> Dict:
        """Discover content patterns and categorize videos."""
        self.logger.info("Analyzing content patterns...")
        
        patterns = await self.pattern_analyzer.analyze(videos)
        
        return {
            'content_categories': patterns['categories'],
            'temporal_patterns': patterns['temporal'],
            'complexity_mapping': patterns['complexity'],
            'topic_clusters': patterns['clusters']
        }
    
    def _synthesize_intelligence(self, **analysis_results) -> ChannelInsights:
        """Combine all analysis results into unified intelligence."""
        self.logger.info("Synthesizing intelligence...")
        
        # Create comprehensive view
        channel_insights = ChannelInsights(
            channel_id=analysis_results['channel_id'],
            analysis_timestamp=datetime.now(),
            caption_insights=analysis_results['caption_analysis'],
            content_patterns=analysis_results['pattern_analysis'],
            playlist_insights=analysis_results['playlist_analysis'],
            relationships=analysis_results['relationships']
        )
        
        # Add cross-dimensional insights
        channel_insights.correlations = self._discover_correlations(analysis_results)
        channel_insights.recommendations = self._generate_recommendations(analysis_results)
        
        return channel_insights
    
    def _discover_correlations(self, results: Dict) -> Dict:
        """Find correlations between different analysis dimensions."""
        correlations = {}
        
        # Caption quality vs content type
        correlations['quality_by_category'] = self._correlate_quality_category(
            results['caption_analysis'],
            results['pattern_analysis']
        )
        
        # Playlist coherence vs caption coverage
        correlations['playlist_quality'] = self._correlate_playlist_quality(
            results['playlist_analysis'],
            results['caption_analysis']
        )
        
        return correlations
```

#### Step 1.2: Advanced Caption Quality Analyzer

**File**: `src/content_intelligence/analyzers/caption_quality.py`

```python
class CaptionQualityAnalyzer:
    """Advanced caption quality assessment with multiple metrics."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.technical_vocabulary = self._load_technical_vocabulary()
        self.quality_weights = {
            'completeness': 0.30,
            'technical_accuracy': 0.25,
            'formatting': 0.15,
            'timestamp_quality': 0.20,
            'coherence': 0.10
        }
    
    async def assess_quality(self, 
                           caption_file: str,
                           video_metadata: Dict,
                           **options) -> QualityAssessment:
        """Comprehensive caption quality assessment."""
        
        # Parse caption file
        caption_data = self._parse_caption_file(caption_file)
        
        # Run quality checks
        assessment_tasks = []
        
        if options.get('analyze_timestamps', True):
            assessment_tasks.append(
                self._assess_timestamp_quality(caption_data, video_metadata)
            )
        
        if options.get('check_technical_terms', True):
            assessment_tasks.append(
                self._assess_technical_accuracy(caption_data)
            )
            
        if options.get('check_speaker_labels', False):
            assessment_tasks.append(
                self._assess_speaker_identification(caption_data)
            )
        
        # Additional assessments
        assessment_tasks.extend([
            self._assess_completeness(caption_data, video_metadata),
            self._assess_formatting(caption_data),
            self._assess_coherence(caption_data)
        ])
        
        # Run assessments in parallel
        results = await asyncio.gather(*assessment_tasks)
        
        # Combine into final assessment
        return self._combine_assessments(results)
    
    async def _assess_timestamp_quality(self, caption_data, video_metadata):
        """Analyze timestamp coverage and gap detection."""
        duration = video_metadata.get('duration', 0)
        
        if not duration or not caption_data.timestamps:
            return {'score': 0.0, 'issues': ['No timestamp data']}
        
        # Calculate coverage
        covered_time = 0
        gaps = []
        
        for i in range(len(caption_data.timestamps) - 1):
            current_end = caption_data.timestamps[i]['end']
            next_start = caption_data.timestamps[i + 1]['start']
            
            gap = next_start - current_end
            if gap > 2.0:  # Gap larger than 2 seconds
                gaps.append({
                    'start': current_end,
                    'end': next_start,
                    'duration': gap
                })
        
        # Calculate score
        total_gap_time = sum(g['duration'] for g in gaps)
        coverage_ratio = 1 - (total_gap_time / duration)
        
        # Penalty for large individual gaps
        max_gap = max((g['duration'] for g in gaps), default=0)
        gap_penalty = min(max_gap / 30, 0.2)  # Max 20% penalty
        
        final_score = max(0, coverage_ratio - gap_penalty)
        
        return {
            'score': final_score,
            'coverage_percentage': coverage_ratio * 100,
            'gaps': gaps,
            'max_gap_seconds': max_gap
        }
```

#### Step 1.3: Content Intelligence Database

**File**: `src/content_intelligence/intelligence/database.py`

```python
class ContentIntelligenceDB:
    """SQLite database for storing comprehensive content intelligence."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with unified content intelligence schema."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create comprehensive intelligence tables
        cursor.executescript('''
            -- Core video intelligence table
            CREATE TABLE IF NOT EXISTS video_intelligence (
                video_id VARCHAR(32) PRIMARY KEY,
                title TEXT NOT NULL,
                published_at DATETIME,
                duration INTEGER,
                
                -- Caption intelligence
                has_captions BOOLEAN DEFAULT FALSE,
                caption_source VARCHAR(20),
                caption_quality_score REAL,
                caption_completeness REAL,
                caption_technical_accuracy REAL,
                caption_word_count INTEGER,
                caption_issues JSON,
                
                -- Content intelligence
                primary_category VARCHAR(50),
                subcategory VARCHAR(50),
                complexity_level VARCHAR(20),
                temporal_relevance VARCHAR(20),
                topics JSON,
                technical_terms JSON,
                
                -- Publishing patterns
                day_of_week VARCHAR(10),
                time_of_day VARCHAR(20),
                series_position INTEGER,
                
                -- Relationships
                related_videos JSON,
                prerequisite_videos JSON,
                
                -- Analysis metadata
                analyzed_at DATETIME,
                analysis_version VARCHAR(10)
            );
            
            -- Playlist intelligence
            CREATE TABLE IF NOT EXISTS playlist_intelligence (
                id VARCHAR(32) PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category VARCHAR(50),
                avg_caption_quality REAL,
                caption_coverage REAL,
                total_duration INTEGER,
                coherence_score REAL,
                video_count INTEGER,
                analyzed_at DATETIME
            );
            
            -- Channel insights cache
            CREATE TABLE IF NOT EXISTS channel_insights (
                channel_id VARCHAR(32) PRIMARY KEY,
                analysis_timestamp DATETIME,
                total_videos INTEGER,
                captioned_videos INTEGER,
                insights_data JSON,
                correlations JSON,
                recommendations JSON,
                cache_expires DATETIME
            );
            
            -- Performance indexes
            CREATE INDEX IF NOT EXISTS idx_quality 
                ON video_intelligence(caption_quality_score, primary_category);
            CREATE INDEX IF NOT EXISTS idx_temporal 
                ON video_intelligence(published_at, temporal_relevance);
            CREATE INDEX IF NOT EXISTS idx_category 
                ON video_intelligence(primary_category, complexity_level);
        ''')
        
        conn.commit()
        conn.close()
    
    def store_video_intelligence(self, video_id: str, intelligence: VideoIntelligence):
        """Store detailed video intelligence in database."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO video_intelligence (
                video_id, title, published_at, duration,
                has_captions, caption_source, caption_quality_score,
                caption_completeness, caption_technical_accuracy, caption_word_count,
                caption_issues, primary_category, subcategory, complexity_level,
                temporal_relevance, topics, technical_terms, day_of_week,
                time_of_day, series_position, related_videos, prerequisite_videos,
                analyzed_at, analysis_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            intelligence.title,
            intelligence.published_at,
            intelligence.duration,
            intelligence.caption_status.available,
            intelligence.caption_status.source,
            intelligence.caption_status.quality_score,
            intelligence.caption_status.completeness,
            intelligence.caption_status.technical_accuracy,
            intelligence.caption_status.word_count,
            json.dumps(intelligence.caption_status.issues),
            intelligence.content_analysis.primary_category,
            intelligence.content_analysis.subcategory,
            intelligence.content_analysis.complexity_level,
            intelligence.content_analysis.temporal_relevance,
            json.dumps(intelligence.content_analysis.topics),
            json.dumps(intelligence.content_analysis.technical_terms),
            intelligence.publishing_context.day_of_week,
            intelligence.publishing_context.time_of_day,
            intelligence.publishing_context.series_position,
            json.dumps(intelligence.relationships.related),
```

### Phase 2: Database Implementation

#### Step 2.1: Create Intelligence Database

**File**: `src/content_intelligence/intelligence/database.py`

```python
#!/usr/bin/env python3
"""
Content Intelligence Database Manager.
"""
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

class ContentIntelligenceDB:
    """Manages content intelligence storage and retrieval."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
    def _init_database(self):
        """Initialize database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Create schema
            self._create_schema(conn)
            conn.commit()
            
    def _create_schema(self, conn):
        """Create database schema for content intelligence."""
        conn.executescript("""
            -- Video Intelligence Table
            CREATE TABLE IF NOT EXISTS video_intelligence (
                video_id VARCHAR(32) PRIMARY KEY,
                title TEXT NOT NULL,
                published_at DATETIME,
                duration INTEGER,
                
                -- Caption quality metrics
                has_captions BOOLEAN DEFAULT FALSE,
                caption_source VARCHAR(20),
                caption_quality_score REAL,
                caption_completeness REAL,
                caption_technical_accuracy REAL,
                caption_formatting REAL,
                caption_timestamp_quality REAL,
                caption_coherence REAL,
                caption_word_count INTEGER,
                caption_quality_level VARCHAR(10),
                
                -- Content intelligence
                primary_category VARCHAR(50),
                subcategory VARCHAR(50),
                complexity_level VARCHAR(20),
                temporal_relevance VARCHAR(20),
                engagement_potential VARCHAR(20),
                
                -- Publishing patterns
                day_of_week VARCHAR(10),
                time_of_day VARCHAR(20),
                series_id VARCHAR(100),
                series_position INTEGER,
                
                -- Analysis metadata
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                analysis_version VARCHAR(10)
            );
            
            -- Playlist Intelligence Table
            CREATE TABLE IF NOT EXISTS playlist_intelligence (
                playlist_id VARCHAR(32) PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                playlist_category VARCHAR(50),
                video_count INTEGER DEFAULT 0,
                avg_caption_quality REAL,
                caption_coverage REAL,
                total_duration INTEGER,
                coherence_score REAL,
                last_updated DATETIME
            );
            
            -- Video-Playlist Mapping
            CREATE TABLE IF NOT EXISTS video_playlist_context (
                video_id VARCHAR(32),
                playlist_id VARCHAR(32),
                position INTEGER,
                relevance_score REAL,
                added_date DATETIME,
                PRIMARY KEY (video_id, playlist_id),
                FOREIGN KEY (video_id) REFERENCES video_intelligence(video_id),
                FOREIGN KEY (playlist_id) REFERENCES playlist_intelligence(playlist_id)
            );
            
            -- Video Relationships
            CREATE TABLE IF NOT EXISTS video_relationships (
                video_id VARCHAR(32),
                related_video_id VARCHAR(32),
                relationship_type VARCHAR(50),
                confidence REAL,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (video_id, related_video_id),
                FOREIGN KEY (video_id) REFERENCES video_intelligence(video_id),
                FOREIGN KEY (related_video_id) REFERENCES video_intelligence(video_id)
            );
            
            -- Content Clusters
            CREATE TABLE IF NOT EXISTS content_clusters (
                cluster_id VARCHAR(50) PRIMARY KEY,
                cluster_label TEXT,
                video_count INTEGER,
                top_terms TEXT,
                avg_quality_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Video-Cluster Mapping
            CREATE TABLE IF NOT EXISTS video_cluster_mapping (
                video_id VARCHAR(32),
                cluster_id VARCHAR(50),
                membership_score REAL,
                PRIMARY KEY (video_id, cluster_id),
                FOREIGN KEY (video_id) REFERENCES video_intelligence(video_id),
                FOREIGN KEY (cluster_id) REFERENCES content_clusters(cluster_id)
            );
            
            -- Aggregated Insights Cache
            CREATE TABLE IF NOT EXISTS content_insights (
                insight_type VARCHAR(50) PRIMARY KEY,
                insight_data JSON,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Technical Terms Found
            CREATE TABLE IF NOT EXISTS video_technical_terms (
                video_id VARCHAR(32),
                term VARCHAR(100),
                frequency INTEGER DEFAULT 1,
                PRIMARY KEY (video_id, term),
                FOREIGN KEY (video_id) REFERENCES video_intelligence(video_id)
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_video_quality 
                ON video_intelligence(has_captions, caption_quality_score, primary_category);
            CREATE INDEX IF NOT EXISTS idx_temporal 
                ON video_intelligence(published_at, temporal_relevance);
            CREATE INDEX IF NOT EXISTS idx_complexity 
                ON video_intelligence(complexity_level, primary_category);
            CREATE INDEX IF NOT EXISTS idx_playlist_videos 
                ON video_playlist_context(playlist_id, position);
            CREATE INDEX IF NOT EXISTS idx_relationships 
                ON video_relationships(video_id, relationship_type);
            CREATE INDEX IF NOT EXISTS idx_terms 
                ON video_technical_terms(term);
        """)
        
    def store_video_intelligence(self, video_id: str, intelligence: Dict):
        """Store comprehensive video intelligence."""
        with sqlite3.connect(self.db_path) as conn:
            # Main video intelligence
            conn.execute("""
                INSERT OR REPLACE INTO video_intelligence (
                    video_id, title, published_at, duration,
                    has_captions, caption_source, caption_quality_score,
                    caption_completeness, caption_technical_accuracy,
                    caption_formatting, caption_timestamp_quality,
                    caption_coherence, caption_word_count, caption_quality_level,
                    primary_category, subcategory, complexity_level,
                    temporal_relevance, engagement_potential,
                    day_of_week, time_of_day, series_id, series_position,
                    analyzed_at, analysis_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """, (
                video_id,
                intelligence.get('title'),
                intelligence.get('published_at'),
                intelligence.get('duration'),
                intelligence.get('caption_status', {}).get('available', False),
                intelligence.get('caption_status', {}).get('source'),
                intelligence.get('caption_status', {}).get('quality_score'),
                intelligence.get('caption_status', {}).get('quality_factors', {}).get('completeness'),
                intelligence.get('caption_status', {}).get('quality_factors', {}).get('technical_accuracy'),
                intelligence.get('caption_status', {}).get('quality_factors', {}).get('formatting'),
                intelligence.get('caption_status', {}).get('quality_factors', {}).get('timestamp_quality'),
                intelligence.get('caption_status', {}).get('quality_factors', {}).get('coherence'),
                intelligence.get('caption_status', {}).get('word_count'),
                intelligence.get('caption_status', {}).get('quality_level'),
                intelligence.get('content_analysis', {}).get('primary_category'),
                intelligence.get('content_analysis', {}).get('subcategory'),
                intelligence.get('content_analysis', {}).get('complexity_level'),
                intelligence.get('content_analysis', {}).get('temporal_relevance'),
                intelligence.get('content_analysis', {}).get('engagement_potential'),
                intelligence.get('publishing_context', {}).get('day_of_week'),
                intelligence.get('publishing_context', {}).get('time_of_day'),
                intelligence.get('publishing_context', {}).get('series_id'),
                intelligence.get('publishing_context', {}).get('series_position'),
                '1.0'
            ))
            
            # Store technical terms
            if 'technical_terms' in intelligence.get('caption_status', {}):
                for term in intelligence['caption_status']['technical_terms']:
                    conn.execute("""
                        INSERT OR REPLACE INTO video_technical_terms (video_id, term)
                        VALUES (?, ?)
                    """, (video_id, term))
                    
            # Store playlist memberships
            for playlist in intelligence.get('playlist_membership', []):
                conn.execute("""
                    INSERT OR REPLACE INTO video_playlist_context 
                    (video_id, playlist_id, position, relevance_score)
                    VALUES (?, ?, ?, ?)
                """, (
                    video_id,
                    playlist['id'],
                    playlist.get('position'),
                    playlist.get('relevance_score', 1.0)
                ))
                
            # Store relationships
            for related_id in intelligence.get('publishing_context', {}).get('related_videos', []):
                conn.execute("""
                    INSERT OR IGNORE INTO video_relationships 
                    (video_id, related_video_id, relationship_type, confidence)
                    VALUES (?, ?, 'similar_topic', 0.8)
                """, (video_id, related_id))
                
            conn.commit()
            
    def get_video_intelligence(self, video_id: str) -> Optional[Dict]:
        """Retrieve comprehensive video intelligence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get main intelligence
            row = conn.execute(
                "SELECT * FROM video_intelligence WHERE video_id = ?",
                (video_id,)
            ).fetchone()
            
            if not row:
                return None
                
            intelligence = dict(row)
            
            # Get technical terms
            terms = conn.execute(
                "SELECT term FROM video_technical_terms WHERE video_id = ?",
                (video_id,)
            ).fetchall()
            intelligence['technical_terms'] = [t['term'] for t in terms]
            
            # Get playlist memberships
            playlists = conn.execute("""
                SELECT p.*, vpc.position, vpc.relevance_score
                FROM video_playlist_context vpc
                JOIN playlist_intelligence p ON vpc.playlist_id = p.playlist_id
                WHERE vpc.video_id = ?
            """, (video_id,)).fetchall()
            intelligence['playlists'] = [dict(p) for p in playlists]
            
            # Get relationships
            relationships = conn.execute("""
                SELECT related_video_id, relationship_type, confidence
                FROM video_relationships
                WHERE video_id = ?
            """, (video_id,)).fetchall()
            intelligence['relationships'] = [dict(r) for r in relationships]
            
            return intelligence
            
    def get_channel_insights(self) -> Dict:
        """Generate comprehensive channel insights."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            insights = {
                'total_videos': 0,
                'captioned_videos': 0,
                'caption_coverage': 0.0,
                'quality_distribution': {},
                'category_breakdown': {},
                'complexity_distribution': {},
                'temporal_patterns': {},
                'top_playlists': [],
                'content_clusters': [],
                'recommendations': []
            }
            
            # Basic stats
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN has_captions = 1 THEN 1 ELSE 0 END) as captioned,
                    AVG(caption_quality_score) as avg_quality
                FROM video_intelligence
            """).fetchone()
            
            insights['total_videos'] = stats['total']
            insights['captioned_videos'] = stats['captioned']
            insights['caption_coverage'] = stats['captioned'] / max(stats['total'], 1)
            insights['avg_caption_quality'] = stats['avg_quality']
            
            # Quality distribution
            quality_dist = conn.execute("""
                SELECT caption_quality_level, COUNT(*) as count
                FROM video_intelligence
                WHERE has_captions = 1
                GROUP BY caption_quality_level
            """).fetchall()
            insights['quality_distribution'] = {q['caption_quality_level']: q['count'] 
                                              for q in quality_dist}
            
            # Category breakdown with caption coverage
            categories = conn.execute("""
                SELECT 
                    primary_category,
                    COUNT(*) as total,
                    SUM(CASE WHEN has_captions = 1 THEN 1 ELSE 0 END) as captioned,
                    AVG(caption_quality_score) as avg_quality
                FROM video_intelligence
                GROUP BY primary_category
                ORDER BY total DESC
            """).fetchall()
            
            insights['category_breakdown'] = [
                {
                    'category': cat['primary_category'],
                    'total': cat['total'],
                    'captioned': cat['captioned'],
                    'coverage': cat['captioned'] / max(cat['total'], 1),
                    'avg_quality': cat['avg_quality']
                }
                for cat in categories
            ]
            
            # Top playlists by quality
            playlists = conn.execute("""
                SELECT * FROM playlist_intelligence
                ORDER BY avg_caption_quality DESC, caption_coverage DESC
                LIMIT 10
            """).fetchall()
            insights['top_playlists'] = [dict(p) for p in playlists]
            
            # Generate recommendations
            insights['recommendations'] = self._generate_recommendations(insights)
            
            return insights
            
    def _generate_recommendations(self, insights: Dict) -> List[Dict]:
        """Generate actionable recommendations based on insights."""
        recommendations = []
        
        # Caption coverage recommendations
        if insights['caption_coverage'] < 0.7:
            recommendations.append({
                'type': 'caption_coverage',
                'priority': 'high',
                'message': f"Only {insights['caption_coverage']*100:.1f}% of videos have captions. "
                          f"Consider adding captions to improve accessibility.",
                'impact': 'accessibility'
            })
            
        # Quality improvement recommendations
        low_quality = insights['quality_distribution'].get('low', 0) + \
                     insights['quality_distribution'].get('poor', 0)
        if low_quality > insights['captioned_videos'] * 0.2:
            recommendations.append({
                'type': 'quality_improvement',
                'priority': 'medium',
                'message': f"{low_quality} videos have low-quality captions. "
                          f"Review and improve caption accuracy and formatting.",
                'impact': 'search_quality'
            })
            
        # Category-specific recommendations
        for category in insights['category_breakdown']:
            if category['coverage'] < 0.5 and category['total'] > 10:
                recommendations.append({
                    'type': 'category_captions',
                    'priority': 'medium',
                    'message': f"{category['category']} videos have only {category['coverage']*100:.1f}% "
                              f"caption coverage. Prioritize captioning this content.",
                    'impact': 'content_accessibility',
                    'category': category['category']
                })
                
        return recommendations
```

### Phase 3: API Integration

#### Step 3.1: Enhanced API Endpoints

**File**: `src/api/content_intelligence_endpoints.py`

```python
#!/usr/bin/env python3
"""
Content Intelligence API endpoints for FastAPI.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from ..content_intelligence import UnifiedContentAnalyzer, ContentIntelligenceDB

router = APIRouter(prefix="/api/intelligence", tags=["content-intelligence"])

# Initialize components
analyzer = UnifiedContentAnalyzer(config={})
intel_db = ContentIntelligenceDB("data/content_intelligence.db")

class ChannelAnalysisRequest(BaseModel):
    force_refresh: bool = False
    include_details: bool = True

class VideoIntelligenceResponse(BaseModel):
    video_id: str
    title: str
    has_captions: bool
    caption_quality: Optional[float]
    quality_level: Optional[str]
    category: str
    complexity: str
    playlists: List[str]

@router.post("/analyze")
async def analyze_channel(request: ChannelAnalysisRequest):
    """
    Run comprehensive channel analysis.
    """
    try:
        # Check if analysis exists and is recent
        if not request.force_refresh:
            existing = intel_db.get_channel_insights()
            if existing and existing.get('total_videos') > 0:
                return {
                    "status": "existing",
                    "message": "Using cached analysis",
                    "insights": existing
                }
        
        # Run full analysis
        intelligence = await analyzer.analyze_channel_comprehensive(
            channel_id="UCRa4yF0KVctjFkaKWAKvopg",  # SpotGamma
            force_refresh=request.force_refresh
        )
        
        return {
            "status": "completed",
            "message": "Analysis complete",
            "insights": intelligence.to_dict() if request.include_details else None,
            "summary": {
                "total_videos": intelligence.total_videos,
                "captioned_videos": intelligence.captioned_videos,
                "avg_quality": intelligence.avg_caption_quality
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_channel_insights():
    """
    Get current channel insights and recommendations.
    """
    insights = intel_db.get_channel_insights()
    
    if not insights or insights['total_videos'] == 0:
        return {
            "status": "no_data",
            "message": "No analysis data available. Run /analyze first."
        }
        
    return insights

@router.get("/caption-report")
async def get_caption_report(
    format: str = Query("summary", regex="^(summary|detailed|csv)$")
):
    """
    Get caption coverage report in various formats.
    """
    insights = intel_db.get_channel_insights()
    
    if format == "summary":
        return {
            "total_videos": insights['total_videos'],
            "captioned_videos": insights['captioned_videos'],
            "coverage_percentage": insights['caption_coverage'] * 100,
            "quality_distribution": insights['quality_distribution'],
            "by_category": insights['category_breakdown']
        }
        
    elif format == "detailed":
        # Get all videos with caption status
        # Implementation would query the database for detailed video list
        pass
        
    elif format == "csv":
        # Generate CSV data
        # Implementation would format as CSV
        pass

@router.get("/video/{video_id}")
async def get_video_intelligence(video_id: str):
    """
    Get detailed intelligence for a specific video.
    """
    intelligence = intel_db.get_video_intelligence(video_id)
    
    if not intelligence:
        raise HTTPException(status_code=404, detail="Video not found")
        
    return intelligence

@router.get("/recommendations")
async def get_recommendations(
    category: Optional[str] = None,
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$")
):
    """
    Get actionable recommendations for content improvement.
    """
    insights = intel_db.get_channel_insights()
    recommendations = insights.get('recommendations', [])
    
    # Filter recommendations
    if category:
        recommendations = [r for r in recommendations 
                         if r.get('category') == category]
    if priority:
        recommendations = [r for r in recommendations 
                         if r.get('priority') == priority]
                         
    return {
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }
```

#### Step 3.2: Enhanced Main API Integration

**File**: `src/api/main.py` (additions)

```python
# Add to existing imports
from .content_intelligence_endpoints import router as intelligence_router

# Add router
app.include_router(intelligence_router)

# Enhance the /ask endpoint with intelligence filtering
class EnhancedAskRequest(BaseModel):
    question: str
    num_sources: int = 4
    search_type: str = "similarity"
    temperature: float = 0.7
    stream: bool = False
    # New intelligence filters
    require_captions: bool = False
    min_caption_quality: str = "low"  # low, medium, high
    categories: Optional[List[str]] = None
    complexity_levels: Optional[List[str]] = None
    playlist_ids: Optional[List[str]] = None
    exclude_playlist_ids: Optional[List[str]] = None

@app.post("/api/ask/intelligent")
async def ask_with_intelligence(request: EnhancedAskRequest):
    """
    Enhanced question answering with content intelligence filtering.
    """
    # Build retrieval filters
    filters = {
        'require_captions': request.require_captions,
        'min_caption_quality': request.min_caption_quality,
        'categories': request.categories,
        'complexity_levels': request.complexity_levels,
        'playlist_ids': request.playlist_ids,
        'exclude_playlist_ids': request.exclude_playlist_ids
    }
    
    # Use enhanced retriever
    rag_engine = IntelligentRAGEngine(filters=filters)
    
    # Process question
    if request.stream:
        return StreamingResponse(
            rag_engine.ask_stream(request.question, request.num_sources),
            media_type="text/event-stream"
        )
    else:
        result = rag_engine.ask(request.question, request.num_sources)
        return result
```

### Phase 4: Testing Strategy

#### Unit Tests

**File**: `test/test_unified_analyzer.py`

```python
import pytest
from src.content_intelligence import UnifiedContentAnalyzer

@pytest.mark.asyncio
async def test_comprehensive_analysis():
    """Test full channel analysis."""
    analyzer = UnifiedContentAnalyzer(config={})
    
    # Run analysis
    intelligence = await analyzer.analyze_channel_comprehensive(
        channel_id="test_channel"
    )
    
    # Verify all dimensions analyzed
    assert intelligence.total_videos > 0
    assert hasattr(intelligence, 'caption_insights')
    assert hasattr(intelligence, 'content_patterns')
    assert hasattr(intelligence, 'playlist_insights')
    assert hasattr(intelligence, 'relationships')
    
def test_caption_quality_assessment():
    """Test caption quality scoring."""
    from src.content_intelligence.analyzers import CaptionQualityAnalyzer
    
    analyzer = CaptionQualityAnalyzer({})
    quality = analyzer.assess_quality(
        caption_file=Path("test_caption.vtt"),
        video_metadata={'duration': 600}
    )
    
    assert 0 <= quality['quality_score'] <= 1
    assert quality['quality_level'] in ['high', 'medium', 'low', 'poor']
```

#### Integration Test

**File**: `test/test_intelligence_integration.py`

```python
import asyncio
from src.content_intelligence import UnifiedContentAnalyzer
from src.api.content_intelligence_endpoints import router

async def test_full_intelligence_pipeline():
    """Test complete intelligence analysis pipeline."""
    
    # 1. Run analysis
    analyzer = UnifiedContentAnalyzer(config={})
    intelligence = await analyzer.analyze_channel_comprehensive(
        channel_id="UCRa4yF0KVctjFkaKWAKvopg"  # SpotGamma
    )
    
    print(f"\nAnalysis Complete:")
    print(f"Total Videos: {intelligence.total_videos}")
    print(f"Captioned Videos: {intelligence.captioned_videos} ({intelligence.caption_coverage*100:.1f}%)")
    print(f"\nQuality Distribution:")
    for level, count in intelligence.quality_distribution.items():
        print(f"  {level}: {count} videos")
        
    print(f"\nCategory Breakdown:")
    for cat in intelligence.category_breakdown[:5]:
        print(f"  {cat['category']}: {cat['total']} videos, "
              f"{cat['coverage']*100:.1f}% captioned")
              
    print(f"\nTop Recommendations:")
    for rec in intelligence.recommendations[:3]:
        print(f"  [{rec['priority']}] {rec['message']}")
        
    assert intelligence.total_videos == 341
    assert intelligence.captioned_videos == 192
    assert 0.5 < intelligence.caption_coverage < 0.6

if __name__ == "__main__":
    asyncio.run(test_full_intelligence_pipeline())
```

## Implementation Roadmap

### Week 1: Foundation
1. **Day 1-2**: Implement UnifiedContentAnalyzer core framework
2. **Day 3-4**: Build CaptionQualityAnalyzer with advanced metrics
3. **Day 5-7**: Create ContentPatternAnalyzer and relationship discovery

### Week 2: Intelligence Layer
1. **Day 8-9**: Implement SQLite intelligence database
2. **Day 10-11**: Build database manager and query interfaces
3. **Day 12-14**: Create channel insights generation and recommendations

### Week 3: Integration
1. **Day 15-16**: Develop API endpoints for intelligence access
2. **Day 17-18**: Enhance RAG retrieval with multi-dimensional filtering
3. **Day 19-21**: Build frontend filter UI components

### Week 4: Polish & Deploy
1. **Day 22-23**: Comprehensive testing and performance optimization
2. **Day 24-25**: Documentation and user guides
3. **Day 26-28**: Production deployment and monitoring setup

## Key Benefits

### Immediate Value
- **56% Caption Coverage Analysis**: Instantly identify which 149 videos lack captions
- **Quality Assessment**: Understand caption quality distribution across content
- **Content Categorization**: Automatic organization of 341 videos into meaningful categories
- **Actionable Insights**: Prioritized recommendations for content improvement

### Long-term Impact
- **Improved Accessibility**: Clear path to 100% caption coverage
- **Better Search Quality**: Quality-aware retrieval improves answer accuracy
- **Content Strategy**: Data-driven decisions about content organization
- **User Experience**: Multi-dimensional filtering for precise content discovery

## Conclusion

The Unified Content Intelligence system transforms RAG-YouTube from a simple search tool into an intelligent content discovery platform. By analyzing all content dimensions in a single pass, we create a rich intelligence foundation that:

1. **Understands Content Deeply**: Beyond keywords to quality, relationships, and context
2. **Enables Precise Retrieval**: Multi-dimensional filtering for exact user needs
3. **Drives Continuous Improvement**: Actionable insights and recommendations
4. **Scales Efficiently**: Single-pass analysis with comprehensive caching

This implementation provides immediate value for the SpotGamma channel while creating a robust framework for any YouTube content knowledge base.