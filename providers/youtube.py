"""
YouTube autoplay provider.
"""

import re
from typing import Optional, Set, Dict, Any, List
from .base import BaseProvider
from ..types import LavalinkTrackInfo, AutoplayResult, AutoplaySource


class YouTubeProvider(BaseProvider):
    """YouTube autoplay provider using Euralink search."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(AutoplaySource.YOUTUBE, config)
        self.eura = None  # Will be set by the main autoplay class
    
    def set_eura(self, eura_instance):
        """Set the Euralink instance for track resolution."""
        self.eura = eura_instance
    
    def create_search_query(self, track_info: LavalinkTrackInfo) -> str:
        """Create a search query from track info."""
        title = track_info.title or ""
        author = track_info.author or ""
        
        # Clean up the query
        query = f"{title} {author}".strip()
        query = re.sub(r'[^\w\s-]', '', query)  # Remove special chars except spaces and hyphens
        query = re.sub(r'\s+', ' ', query)  # Normalize spaces
        
        return query
    
    async def get_youtube_autoplay_tracks(self, track_info: LavalinkTrackInfo, 
                                        exclude_ids: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """Get YouTube autoplay tracks using Euralink search."""
        if not self.eura:
            return []
        
        try:
            query = self.create_search_query(track_info)
            if not query:
                return []
            
            # Use Euralink to search for similar tracks
            results = await self.eura.search(query, source="ytsearch")
            
            if not results or not results.tracks:
                return []
            
            tracks = []
            exclude_ids = exclude_ids or set()
            
            for track in results.tracks[:10]:  # Limit to 10 results
                if hasattr(track, 'info') and track.info:
                    track_id = getattr(track.info, 'identifier', None)
                    if track_id and track_id not in exclude_ids:
                        tracks.append({
                            'identifier': track_id,
                            'title': getattr(track.info, 'title', ''),
                            'author': getattr(track.info, 'author', ''),
                            'uri': getattr(track.info, 'uri', ''),
                            'length': getattr(track.info, 'length', 0)
                        })
            
            return tracks[:5]  # Return up to 5 tracks
            
        except Exception as e:
            print(f"[YouTube] Error getting autoplay tracks: {str(e)}")
            return []
    
    async def get_next_track(self, track_info: LavalinkTrackInfo, 
                           exclude_ids: Optional[Set[str]] = None) -> AutoplayResult:
        """Get the next YouTube track for autoplay."""
        if not self.validate_track_info(track_info):
            return self.create_error_result("Invalid track info provided")
        
        try:
            tracks = await self.get_youtube_autoplay_tracks(track_info, exclude_ids)
            
            if not tracks:
                return self.create_error_result("No YouTube autoplay tracks found")
            
            # Select a random track
            import random
            selected_track = random.choice(tracks)
            
            metadata = {
                'video_id': selected_track['identifier'],
                'title': selected_track['title'],
                'author': selected_track['author'],
                'total_found': len(tracks)
            }
            
            return self.create_success_result(
                url=selected_track['uri'],
                track_id=selected_track['identifier'],
                metadata=metadata
            )
            
        except Exception as e:
            return self.handle_error(e)
