#!/usr/bin/env python3
"""
YouTube Playlist Fetcher

This module retrieves playlist information for YouTube videos and associates videos with their playlists.
Uses the YouTube Data API v3 to fetch playlist data for a channel.
"""
import os
import sys
import json
from typing import Dict, List, Optional, Set
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class PlaylistFetcher:
    """Fetches and manages YouTube playlist information."""
    
    def __init__(self, api_key: str = None):
        """Initialize the playlist fetcher with YouTube API key."""
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key) if api_key else None
        self.playlists = {}
        self.video_to_playlists = {}  # Map video_id -> list of playlist_ids
        
    def get_channel_playlists(self, channel_id: str) -> List[Dict]:
        """
        Get all playlists for a channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            List of playlist information dictionaries
        """
        print(f'[playlist_fetcher] Getting playlists for channel {channel_id}...')
        
        playlists = []
        next_page_token = None
        
        try:
            while True:
                request = self.youtube.playlists().list(
                    part="id,snippet,contentDetails",
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    playlist_info = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'published_at': item['snippet']['publishedAt'],
                        'item_count': item['contentDetails']['itemCount'],
                        'thumbnails': item['snippet'].get('thumbnails', {})
                    }
                    playlists.append(playlist_info)
                    self.playlists[item['id']] = playlist_info
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except HttpError as e:
            print(f"[playlist_fetcher] Error fetching playlists: {e}")
            return []
            
        print(f'[playlist_fetcher] Found {len(playlists)} playlists')
        return playlists
    
    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        Get all video IDs in a playlist.
        
        Args:
            playlist_id: YouTube playlist ID
            
        Returns:
            List of video IDs in the playlist
        """
        video_ids = []
        next_page_token = None
        
        try:
            while True:
                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_ids.append(video_id)
                    
                    # Update video-to-playlist mapping
                    if video_id not in self.video_to_playlists:
                        self.video_to_playlists[video_id] = []
                    self.video_to_playlists[video_id].append(playlist_id)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except HttpError as e:
            print(f"[playlist_fetcher] Error fetching playlist items: {e}")
            return []
            
        return video_ids
    
    def build_playlist_mapping(self, channel_id: str) -> Dict[str, List[str]]:
        """
        Build a complete mapping of videos to playlists for a channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dictionary mapping video_id -> list of playlist_ids
        """
        print(f'[playlist_fetcher] Building playlist mapping for channel {channel_id}...')
        
        # First, get all playlists
        playlists = self.get_channel_playlists(channel_id)
        
        # Then, get videos for each playlist
        for playlist in playlists:
            playlist_id = playlist['id']
            print(f'[playlist_fetcher] Processing playlist: {playlist["title"]} ({playlist["item_count"]} videos)')
            self.get_playlist_videos(playlist_id)
        
        print(f'[playlist_fetcher] Mapping complete: {len(self.video_to_playlists)} videos across {len(self.playlists)} playlists')
        return self.video_to_playlists
    
    def get_video_playlists(self, video_id: str) -> List[Dict]:
        """
        Get all playlists that contain a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of playlist information dictionaries
        """
        playlist_ids = self.video_to_playlists.get(video_id, [])
        return [self.playlists[pid] for pid in playlist_ids if pid in self.playlists]
    
    def save_playlist_data(self, output_dir: str = '.'):
        """
        Save playlist data to JSON files.
        
        Args:
            output_dir: Directory to save the JSON files
        """
        # Save playlists
        playlists_path = os.path.join(output_dir, 'playlists.json')
        with open(playlists_path, 'w') as f:
            json.dump(list(self.playlists.values()), f, indent=2)
        print(f'[playlist_fetcher] Saved playlists to {playlists_path}')
        
        # Save video-to-playlist mapping
        mapping_path = os.path.join(output_dir, 'video_playlist_mapping.json')
        with open(mapping_path, 'w') as f:
            json.dump(self.video_to_playlists, f, indent=2)
        print(f'[playlist_fetcher] Saved video-playlist mapping to {mapping_path}')
    
    def load_playlist_data(self, input_dir: str = '.') -> bool:
        """
        Load playlist data from JSON files.
        
        Args:
            input_dir: Directory containing the JSON files
            
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            # Load playlists
            playlists_path = os.path.join(input_dir, 'playlists.json')
            if os.path.exists(playlists_path):
                with open(playlists_path, 'r') as f:
                    playlists_list = json.load(f)
                    self.playlists = {p['id']: p for p in playlists_list}
                print(f'[playlist_fetcher] Loaded {len(self.playlists)} playlists')
            
            # Load video-to-playlist mapping
            mapping_path = os.path.join(input_dir, 'video_playlist_mapping.json')
            if os.path.exists(mapping_path):
                with open(mapping_path, 'r') as f:
                    self.video_to_playlists = json.load(f)
                print(f'[playlist_fetcher] Loaded mapping for {len(self.video_to_playlists)} videos')
            
            return True
            
        except Exception as e:
            print(f"[playlist_fetcher] Error loading playlist data: {e}")
            return False


def main():
    """Main function to fetch playlist data for a channel."""
    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Check for API key
    if 'GOOGLE_API_KEY' not in os.environ:
        print('Error: GOOGLE_API_KEY environment variable not set')
        print('Usage: GOOGLE_API_KEY=XXXX python playlist_fetcher.py')
        sys.exit(1)
    
    # Load channel info to get channel ID
    if not os.path.exists('channel_info.json'):
        print('Error: channel_info.json not found. Run list_videos.py first.')
        sys.exit(1)
    
    with open('channel_info.json', 'r') as f:
        channel_info = json.load(f)
    
    channel_id = channel_info['id']
    channel_name = channel_info['snippet']['title']
    
    print(f'[playlist_fetcher] Fetching playlists for channel: {channel_name} ({channel_id})')
    
    # Initialize fetcher and build mapping
    fetcher = PlaylistFetcher(os.environ['GOOGLE_API_KEY'])
    fetcher.build_playlist_mapping(channel_id)
    
    # Save the data
    fetcher.save_playlist_data()
    
    # Print summary statistics
    print(f'\n[playlist_fetcher] Summary:')
    print(f'  - Total playlists: {len(fetcher.playlists)}')
    print(f'  - Total videos with playlist info: {len(fetcher.video_to_playlists)}')
    
    # Show top playlists by video count
    sorted_playlists = sorted(fetcher.playlists.values(), key=lambda p: p['item_count'], reverse=True)
    print(f'\n[playlist_fetcher] Top playlists by video count:')
    for i, playlist in enumerate(sorted_playlists[:5]):
        print(f'  {i+1}. {playlist["title"]} - {playlist["item_count"]} videos')


if __name__ == '__main__':
    main()