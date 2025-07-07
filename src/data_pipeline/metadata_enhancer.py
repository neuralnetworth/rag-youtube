"""
Metadata enhancer for YouTube video documents.
Adds additional metadata like category inference, quality scoring, and caption tracking.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MetadataEnhancer:
    """Enhances document metadata with categories, quality scores, and other attributes."""
    
    # Category patterns for title matching
    CATEGORY_PATTERNS = {
        "daily_update": [
            r"market\s*(update|outlook|recap|review)",
            r"daily\s*(update|recap|market)",
            r"(monday|tuesday|wednesday|thursday|friday)\s*(update|market|recap)",
            r"(am|pm)\s*(update|market|outlook)",
            r"open\s*interest",
            r"gamma\s*(update|levels)",
            r"0dte|zero\s*dte"
        ],
        "educational": [
            r"(what|how|why|when)\s+(is|are|does|do)",
            r"explained|explaining|explains",
            r"introduction\s+to",
            r"tutorial|guide|basics",
            r"learn|learning|lesson",
            r"101|beginner|fundamental",
            r"understanding|understand"
        ],
        "interview": [
            r"interview|conversation|chat\s+with",
            r"q\s*&\s*a|q\s*and\s*a",
            r"ask\s+me\s+anything|ama",
            r"guest|featuring|with\s+\w+\s+\w+",
            r"discussion|discussing"
        ],
        "special_event": [
            r"fomc|fed\s*(meeting|decision)",
            r"earnings|opex|options\s*expiration",
            r"special\s*(event|report|update)",
            r"breaking|alert|urgent",
            r"year\s*(end|review)|annual",
            r"holiday|christmas|thanksgiving"
        ]
    }
    
    # Technical keywords for quality scoring
    TECHNICAL_KEYWORDS = [
        "gamma", "delta", "theta", "vega", "implied volatility", "iv",
        "options chain", "strike price", "expiration", "hedging",
        "dealer positioning", "market maker", "volatility surface",
        "put/call ratio", "open interest", "volume", "skew",
        "vix", "vwap", "standard deviation", "probability"
    ]
    
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for better performance."""
        compiled = {}
        for category, patterns in self.CATEGORY_PATTERNS.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def enhance_metadata(self, doc_metadata: Dict) -> Dict:
        """
        Enhance document metadata with additional fields.
        
        Args:
            doc_metadata: Original metadata dict with at least 'title', 'video_id', 
                         'channel_id', 'published_at' fields
        
        Returns:
            Enhanced metadata dict with additional fields
        """
        enhanced = doc_metadata.copy()
        
        # Add caption availability (will be updated during document loading)
        enhanced['has_captions'] = enhanced.get('has_captions', False)
        
        # Infer category from title
        enhanced['category'] = self._infer_category(enhanced.get('title', ''))
        
        # Calculate quality score if content is available
        if 'content' in enhanced:
            quality_data = self._calculate_quality(
                enhanced['content'],
                enhanced.get('duration', 0)
            )
            enhanced.update(quality_data)
        else:
            enhanced['quality_score'] = 'unknown'
            enhanced['words_per_minute'] = 0
            enhanced['technical_keyword_count'] = 0
        
        # Parse and format date
        if 'published_at' in enhanced:
            enhanced['published_date'] = self._parse_date(enhanced['published_at'])
        
        # Add enhancement timestamp
        enhanced['metadata_enhanced_at'] = datetime.utcnow().isoformat()
        
        return enhanced
    
    def _infer_category(self, title: str) -> str:
        """
        Infer video category from title using pattern matching.
        
        Args:
            title: Video title
            
        Returns:
            Category string or 'uncategorized'
        """
        if not title:
            return 'uncategorized'
        
        # Check each category's patterns
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(title):
                    return category
        
        return 'uncategorized'
    
    def _calculate_quality(self, content: str, duration: int) -> Dict:
        """
        Calculate quality metrics for the content.
        
        Args:
            content: Video transcript content
            duration: Video duration in seconds
            
        Returns:
            Dict with quality_score, words_per_minute, technical_keyword_count
        """
        if not content or not duration:
            return {
                'quality_score': 'none',
                'words_per_minute': 0,
                'technical_keyword_count': 0
            }
        
        # Calculate words per minute
        word_count = len(content.split())
        minutes = duration / 60.0
        wpm = int(word_count / minutes) if minutes > 0 else 0
        
        # Count technical keywords
        content_lower = content.lower()
        tech_count = sum(
            1 for keyword in self.TECHNICAL_KEYWORDS 
            if keyword in content_lower
        )
        
        # Determine quality score
        if wpm >= 120 and tech_count >= 5:
            quality_score = 'high'
        elif wpm >= 80 and tech_count >= 2:
            quality_score = 'medium'
        elif wpm >= 40:
            quality_score = 'low'
        else:
            quality_score = 'none'
        
        return {
            'quality_score': quality_score,
            'words_per_minute': wpm,
            'technical_keyword_count': tech_count
        }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse and format date string to YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Formatted date string or original if parsing fails
        """
        try:
            # Try parsing ISO format first
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            return dt.strftime('%Y-%m-%d')
        except Exception:
            # Return original if parsing fails
            return date_str
    
    def get_filter_statistics(self, documents: List[Dict]) -> Dict:
        """
        Calculate statistics for available filters.
        
        Args:
            documents: List of documents with metadata
            
        Returns:
            Dict with filter statistics
        """
        stats = {
            'total_documents': len(documents),
            'categories': {},
            'quality_levels': {},
            'caption_coverage': {
                'with_captions': 0,
                'without_captions': 0,
                'percentage': 0
            },
            'date_range': {
                'earliest': None,
                'latest': None
            }
        }
        
        # Initialize counters
        for category in list(self.CATEGORY_PATTERNS.keys()) + ['uncategorized']:
            stats['categories'][category] = 0
        
        for quality in ['high', 'medium', 'low', 'none', 'unknown']:
            stats['quality_levels'][quality] = 0
        
        # Process documents
        earliest_date = None
        latest_date = None
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            
            # Category counts
            category = metadata.get('category', 'uncategorized')
            if category in stats['categories']:
                stats['categories'][category] += 1
            
            # Quality counts
            quality = metadata.get('quality_score', 'unknown')
            if quality in stats['quality_levels']:
                stats['quality_levels'][quality] += 1
            
            # Caption coverage
            if metadata.get('has_captions', False):
                stats['caption_coverage']['with_captions'] += 1
            else:
                stats['caption_coverage']['without_captions'] += 1
            
            # Date range
            pub_date = metadata.get('published_date')
            if pub_date:
                if not earliest_date or pub_date < earliest_date:
                    earliest_date = pub_date
                if not latest_date or pub_date > latest_date:
                    latest_date = pub_date
        
        # Calculate caption percentage
        if stats['total_documents'] > 0:
            stats['caption_coverage']['percentage'] = round(
                100 * stats['caption_coverage']['with_captions'] / stats['total_documents'],
                1
            )
        
        # Set date range
        stats['date_range']['earliest'] = earliest_date
        stats['date_range']['latest'] = latest_date
        
        return stats