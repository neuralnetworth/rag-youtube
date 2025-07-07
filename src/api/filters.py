"""
Filter logic for in-memory document filtering.
Supports filtering by caption availability, category, quality, and date range.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentFilter:
    """Handles filtering of documents based on various criteria."""
    
    def __init__(self):
        self.filters = {}
    
    def set_filters(self, filters: Dict[str, Any]) -> None:
        """
        Set active filters.
        
        Args:
            filters: Dictionary of filter criteria
                - require_captions: bool
                - categories: List[str] (empty list means all)
                - quality_levels: List[str] (empty list means all)
                - date_from: str (YYYY-MM-DD)
                - date_to: str (YYYY-MM-DD)
                - playlists: List[str] (playlist IDs, empty means all)
        """
        self.filters = filters
    
    def apply_filters(self, documents: List[Dict[str, Any]], over_fetch_factor: int = 3) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of documents.
        
        Args:
            documents: List of documents with metadata
            over_fetch_factor: How many extra documents to request when filtering
            
        Returns:
            Filtered list of documents
        """
        if not self.filters:
            return documents
        
        filtered = []
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            
            # Check caption requirement
            if self.filters.get('require_captions', False):
                if not metadata.get('has_captions', False):
                    continue
            
            # Check categories
            categories = self.filters.get('categories', [])
            if categories:
                doc_category = metadata.get('category', 'uncategorized')
                if doc_category not in categories:
                    continue
            
            # Check quality levels
            quality_levels = self.filters.get('quality_levels', [])
            if quality_levels:
                doc_quality = metadata.get('quality_score', 'unknown')
                if doc_quality not in quality_levels:
                    continue
            
            # Check date range
            date_from = self.filters.get('date_from')
            date_to = self.filters.get('date_to')
            
            if date_from or date_to:
                pub_date = metadata.get('published_date')
                if not pub_date:
                    continue
                
                if date_from and pub_date < date_from:
                    continue
                
                if date_to and pub_date > date_to:
                    continue
            
            # Check playlists (for future use)
            playlists = self.filters.get('playlists', [])
            if playlists:
                doc_playlists = metadata.get('playlists', [])
                if not any(playlist_id in doc_playlists for playlist_id in playlists):
                    continue
            
            # Document passed all filters
            filtered.append(doc)
        
        return filtered
    
    def calculate_over_fetch(self, num_requested: int, active_filters: bool = False) -> int:
        """
        Calculate how many documents to fetch when filters are active.
        
        Args:
            num_requested: Number of documents requested by user
            active_filters: Whether any filters are active
            
        Returns:
            Number of documents to fetch from vector store
        """
        if not active_filters:
            return num_requested
        
        # Over-fetch by 3x when filters are active
        # This ensures we have enough documents after filtering
        return min(num_requested * 3, 20)  # Cap at 20 to avoid too much processing
    
    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        if not self.filters:
            return False
        
        # Check each filter type
        if self.filters.get('require_captions', False):
            return True
        
        if self.filters.get('categories', []):
            return True
        
        if self.filters.get('quality_levels', []):
            return True
        
        if self.filters.get('date_from') or self.filters.get('date_to'):
            return True
        
        if self.filters.get('playlists', []):
            return True
        
        return False
    
    def get_filter_summary(self) -> str:
        """Get a human-readable summary of active filters."""
        if not self.has_active_filters():
            return "No filters active"
        
        parts = []
        
        if self.filters.get('require_captions', False):
            parts.append("Captions required")
        
        if categories := self.filters.get('categories', []):
            parts.append(f"Categories: {', '.join(categories)}")
        
        if quality_levels := self.filters.get('quality_levels', []):
            parts.append(f"Quality: {', '.join(quality_levels)}")
        
        date_from = self.filters.get('date_from')
        date_to = self.filters.get('date_to')
        if date_from and date_to:
            parts.append(f"Date range: {date_from} to {date_to}")
        elif date_from:
            parts.append(f"After: {date_from}")
        elif date_to:
            parts.append(f"Before: {date_to}")
        
        if playlists := self.filters.get('playlists', []):
            parts.append(f"{len(playlists)} playlist(s)")
        
        return " | ".join(parts)