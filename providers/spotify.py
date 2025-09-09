"""
Spotify autoplay provider.
"""

import re
from typing import Optional, Set, Dict, Any, List
from .base import BaseProvider
from ..types import LavalinkTrackInfo, AutoplayResult, AutoplaySource
from ..utils.autoplay_apis import sp_auto_play, shuffle_in_place


class SpotifyProvider(BaseProvider):
    """Spotify autoplay provider using sprec source via Lavalink."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(AutoplaySource.SPOTIFY, config)
        self.eura = None  # Will be set by the main autoplay class
    
    def set_eura(self, eura_instance):
        """Set the Euralink instance for track resolution."""
        self.eura = eura_instance
    
    def extract_track_id_from_query(self, query: str) -> Optional[str]:
        """Extract track ID from a mix:track: query."""
        match = re.search(r'mix:track:([a-zA-Z0-9]+)', query)
        return match.group(1) if match else None
    
    async def resolve_with_lavalink(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Resolve track using Lavalink sprec source."""
        if not self.eura:
            return None
        
        try:
            # Use sprec source for Spotify recommendations
            query = f"sprec:{track_id}"
            results = await self.eura.search(query, source="sprec")
            
            if not results or not results.tracks:
                return None
            
            # Get the first track from results
            track = results.tracks[0]
            
            # Extract track info from the track object
            if hasattr(track, 'info') and track.info:
                return {
                    'identifier': getattr(track.info, 'identifier', ''),
                    'title': getattr(track.info, 'title', ''),
                    'author': getattr(track.info, 'author', ''),
                    'uri': getattr(track.info, 'uri', ''),
                    'length': getattr(track.info, 'length', 0)
                }
            
            return None
            
        except Exception as e:
            print(f"[Spotify] Error resolving with Lavalink: {str(e)}")
            return None
    
    async def get_spotify_autoplay_tracks(self, track_info: LavalinkTrackInfo, 
                                        exclude_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Get Spotify autoplay tracks using Lavalink sprec."""
        if not self.eura:
            return []
        
        try:
            track_id = track_info.identifier
            if not track_id:
                return []
            
            # Get recommendations using Lavalink
            selected_track = await self.resolve_with_lavalink(track_id)
            
            if not selected_track:
                return []
            
            # Check if track should be excluded
            exclude_ids = exclude_ids or set()
            if selected_track['identifier'] in exclude_ids:
                return []
            
            return [selected_track]
            
        except Exception as e:
            print(f"[Spotify] Error getting autoplay tracks: {str(e)}")
            return []
    
    async def get_next_track(self, track_info: LavalinkTrackInfo, 
                           exclude_ids: Optional[Set[str]] = None) -> AutoplayResult:
        """Get the next Spotify track for autoplay."""
        if not self.validate_track_info(track_info):
            return self.create_error_result("Invalid track info provided")
        
        try:
            tracks = await self.get_spotify_autoplay_tracks(track_info, exclude_ids)
            
            if not tracks:
                return self.create_error_result("No Spotify autoplay tracks found")
            
            # Select the first (and only) track
            selected_track = tracks[0]
            
            metadata = {
                'original_track_id': track_info.identifier,
                'selected_track_id': selected_track['identifier'],
                'track_name': selected_track['title'],
                'artists': selected_track['author'],
                'total_found': len(tracks)
            }
            
            return self.create_success_result(
                url=selected_track['uri'],
                track_id=selected_track['identifier'],
                metadata=metadata
            )
            
        except Exception as e:
            return self.handle_error(e)
