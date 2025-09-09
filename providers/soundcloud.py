"""
SoundCloud autoplay provider.
"""

import re
from typing import Optional, Set, Dict, Any, List
from .base import BaseProvider
from ..types import LavalinkTrackInfo, AutoplayResult, AutoplaySource
from ..utils.autoplay_apis import sc_auto_play, shuffle_in_place


class SoundCloudProvider(BaseProvider):
    """SoundCloud autoplay provider using web scraping."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(AutoplaySource.SOUNDCLOUD, config)
    
    def extract_track_id(self, url: str) -> Optional[str]:
        """Extract track ID from SoundCloud URL."""
        match = re.search(r'/tracks/(\d+)', url)
        return match.group(1) if match else None
    
    async def get_soundcloud_autoplay_tracks(self, track_info: LavalinkTrackInfo, 
                                           exclude_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Get SoundCloud autoplay tracks using web scraping."""
        try:
            base_url = track_info.uri
            if not base_url:
                return []
            
            # Get recommended track URL
            recommended_url = await sc_auto_play(base_url)
            
            if not recommended_url:
                return []
            
            # Check if track should be excluded
            exclude_ids = exclude_ids or set()
            track_id = self.extract_track_id(recommended_url)
            
            if track_id and track_id in exclude_ids:
                return []
            
            # Extract basic info from URL
            track_name = recommended_url.split('/')[-1].replace('-', ' ').title()
            
            return [{
                'identifier': track_id or '',
                'title': track_name,
                'author': track_info.author or 'Unknown Artist',
                'uri': recommended_url,
                'length': 0
            }]
            
        except Exception as e:
            print(f"[SoundCloud] Error getting autoplay tracks: {str(e)}")
            return []
    
    async def get_next_track(self, track_info: LavalinkTrackInfo, 
                           exclude_ids: Optional[Set[str]] = None) -> AutoplayResult:
        """Get the next SoundCloud track for autoplay."""
        if not self.validate_track_info(track_info):
            return self.create_error_result("Invalid track info provided")
        
        try:
            tracks = await self.get_soundcloud_autoplay_tracks(track_info, exclude_ids)
            
            if not tracks:
                return self.create_error_result("No SoundCloud autoplay tracks found")
            
            # Select the first (and only) track
            selected_track = tracks[0]
            
            metadata = {
                'original_url': track_info.uri,
                'recommended_url': selected_track['uri'],
                'track_name': selected_track['title'],
                'total_found': len(tracks)
            }
            
            return self.create_success_result(
                url=selected_track['uri'],
                track_id=selected_track['identifier'],
                metadata=metadata
            )
            
        except Exception as e:
            return self.handle_error(e)
