"""
Base provider class for all autoplay providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Set, Dict, Any
from ..types import LavalinkTrackInfo, AutoplayResult, AutoplaySource, ProviderError


class BaseProvider(ABC):
    """Abstract base class for all autoplay providers."""
    
    def __init__(self, source: AutoplaySource, config: Optional[Dict[str, Any]] = None):
        self.source = source
        self.config = config or {}
    
    def create_success_result(self, url: str, track_id: Optional[str] = None, 
                            metadata: Optional[Dict[str, Any]] = None) -> AutoplayResult:
        """Create a successful autoplay result."""
        result = AutoplayResult(
            success=True,
            url=url,
            source=self.source
        )
        
        if track_id is not None:
            result.track_id = track_id
        if metadata is not None:
            result.metadata = metadata
            
        return result
    
    def create_error_result(self, error: str, metadata: Optional[Dict[str, Any]] = None) -> AutoplayResult:
        """Create an error autoplay result."""
        result = AutoplayResult(
            success=False,
            error=error,
            source=self.source
        )
        
        if metadata is not None:
            result.metadata = metadata
            
        return result
    
    def handle_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> AutoplayResult:
        """Handle an exception and create an error result."""
        error_msg = str(error)
        return self.create_error_result(error_msg, metadata)
    
    def validate_track_info(self, track_info: LavalinkTrackInfo) -> bool:
        """Validate that track info has required fields for this provider."""
        if not track_info or not track_info.title or not track_info.author:
            return False
        return True
    
    @abstractmethod
    async def get_next_track(self, track_info: LavalinkTrackInfo, 
                           exclude_ids: Optional[Set[str]] = None) -> AutoplayResult:
        """Get the next track for autoplay."""
        pass
