"""
Main autoplay class for Lavalink clients.
"""

import asyncio
from typing import Optional, Dict, Any, Set
from .types import LavalinkTrackInfo, AutoplayResult, AutoplayConfig, AutoplaySource
from .events import AutoplayEventEmitter
from .providers import YouTubeProvider, SpotifyProvider, SoundCloudProvider


class LavalinkAutoplay:
    """Main autoplay class for Lavalink clients."""
    
    def __init__(self, config: Optional[AutoplayConfig] = None, eura_instance=None):
        self.config = config or AutoplayConfig()
        self.eura = eura_instance
        self.events = AutoplayEventEmitter()
        
        # Initialize providers
        self.providers = {
            AutoplaySource.YOUTUBE: YouTubeProvider(),
            AutoplaySource.SPOTIFY: SpotifyProvider(),
            AutoplaySource.SOUNDCLOUD: SoundCloudProvider()
        }
        
        # Set Euralink instance for providers that need it
        if self.eura:
            self.providers[AutoplaySource.YOUTUBE].set_eura(self.eura)
            self.providers[AutoplaySource.SPOTIFY].set_eura(self.eura)
        
        # Track history to prevent repeats
        self.track_history: Dict[str, Set[str]] = {}
    
    def set_eura(self, eura_instance):
        """Set the Euralink instance for track resolution."""
        self.eura = eura_instance
        self.providers[AutoplaySource.YOUTUBE].set_eura(eura_instance)
        self.providers[AutoplaySource.SPOTIFY].set_eura(eura_instance)
    
    def map_source_name(self, source_name: str, track_info: Optional[LavalinkTrackInfo] = None) -> AutoplaySource:
        """Map various source name formats to AutoplaySource enum."""
        if not source_name:
            # Try to detect from URL if available
            if track_info and track_info.uri:
                uri = track_info.uri.lower()
                if 'youtube.com' in uri or 'youtu.be' in uri:
                    return AutoplaySource.YOUTUBE
                elif 'spotify.com' in uri:
                    return AutoplaySource.SPOTIFY
                elif 'soundcloud.com' in uri:
                    return AutoplaySource.SOUNDCLOUD
            return AutoplaySource.YOUTUBE  # Default fallback
        
        source_lower = source_name.lower()
        
        # Handle various naming conventions
        if source_lower in ['youtube', 'yt', 'ytsearch', 'ytmsearch']:
            return AutoplaySource.YOUTUBE
        elif source_lower in ['spotify', 'sp', 'spsearch', 'sprec']:
            return AutoplaySource.SPOTIFY
        elif source_lower in ['soundcloud', 'sc', 'scsearch']:
            return AutoplaySource.SOUNDCLOUD
        
        return AutoplaySource.YOUTUBE  # Default fallback
    
    def add_to_history(self, guild_id: str, track_id: str) -> None:
        """Add a track to the history for a guild."""
        if not guild_id or not track_id:
            return
        
        if guild_id not in self.track_history:
            self.track_history[guild_id] = set()
        
        self.track_history[guild_id].add(track_id)
        
        # Limit history size
        if len(self.track_history[guild_id]) > self.config.max_history_size:
            # Remove oldest entries (convert to list, remove first, convert back)
            history_list = list(self.track_history[guild_id])
            self.track_history[guild_id] = set(history_list[-self.config.max_history_size:])
    
    def is_in_history(self, guild_id: str, track_id: str) -> bool:
        """Check if a track is in the history for a guild."""
        if not guild_id or not track_id:
            return False
        return track_id in self.track_history.get(guild_id, set())
    
    def clear_history(self, guild_id: Optional[str] = None) -> None:
        """Clear track history for a guild or all guilds."""
        if guild_id:
            self.track_history.pop(guild_id, None)
        else:
            self.track_history.clear()
    
    async def get_next_track(self, track_info: LavalinkTrackInfo, guild_id: str) -> AutoplayResult:
        """Get the next track for autoplay based on the current track."""
        try:
            if not track_info:
                return AutoplayResult(success=False, error="No track info provided")
            
            # Map source name to AutoplaySource
            source = self.map_source_name(track_info.source_name, track_info)
            
            # Get exclude IDs for this guild
            exclude_ids = self.track_history.get(guild_id, set())
            
            # Get provider for the source
            provider = self.providers.get(source)
            if not provider:
                return AutoplayResult(success=False, error=f"No provider for source: {source}")
            
            # Get next track from provider
            result = await provider.get_next_track(track_info, exclude_ids)
            
            if result.success and result.track_id:
                # Add to history
                self.add_to_history(guild_id, result.track_id)
                
                # Emit success event
                self.events.emit('success', {
                    'source': source.value,
                    'track_info': track_info,
                    'result': result
                })
            else:
                # Emit error event
                self.events.emit('error', {
                    'source': source.value,
                    'track_info': track_info,
                    'error': result.error
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Autoplay error: {str(e)}"
            self.events.emit('error', {
                'source': track_info.source_name if track_info else 'unknown',
                'track_info': track_info,
                'error': error_msg
            })
            return AutoplayResult(success=False, error=error_msg)
    
    async def get_next_track_for_source(self, track_info: LavalinkTrackInfo, 
                                      source: AutoplaySource, guild_id: str) -> AutoplayResult:
        """Get the next track for a specific source."""
        try:
            if not track_info:
                return AutoplayResult(success=False, error="No track info provided")
            
            # Get exclude IDs for this guild
            exclude_ids = self.track_history.get(guild_id, set())
            
            # Get provider for the source
            provider = self.providers.get(source)
            if not provider:
                return AutoplayResult(success=False, error=f"No provider for source: {source}")
            
            # Get next track from provider
            result = await provider.get_next_track(track_info, exclude_ids)
            
            if result.success and result.track_id:
                # Add to history
                self.add_to_history(guild_id, result.track_id)
                
                # Emit success event
                self.events.emit('success', {
                    'source': source.value,
                    'track_info': track_info,
                    'result': result
                })
            else:
                # Emit error event
                self.events.emit('error', {
                    'source': source.value,
                    'track_info': track_info,
                    'error': result.error
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Autoplay error for {source.value}: {str(e)}"
            self.events.emit('error', {
                'source': source.value,
                'track_info': track_info,
                'error': error_msg
            })
            return AutoplayResult(success=False, error=error_msg)
