"""
Type definitions and data classes for the autoplay package.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Set, Union
from enum import Enum


class AutoplaySource(Enum):
    """Supported autoplay sources."""
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    SOUNDCLOUD = "soundcloud"


@dataclass
class LavalinkTrackInfo:
    """Lavalink track information structure."""
    title: str
    author: str
    identifier: str
    uri: str
    source_name: str
    length: Optional[int] = None
    is_seekable: Optional[bool] = None
    is_stream: Optional[bool] = None
    position: Optional[int] = None
    artwork_url: Optional[str] = None
    isrc: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AutoplayResult:
    """Result of an autoplay operation."""
    success: bool
    url: Optional[str] = None
    track_id: Optional[str] = None
    source: Optional[AutoplaySource] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AutoplayConfig:
    """Configuration for the autoplay system."""
    max_retries: int = 1
    timeout: int = 5000
    rate_limit_delay: int = 500
    max_recommendations: int = 5
    max_tracks: int = 10
    enable_radio_mode: bool = False
    max_history_size: int = 50


@dataclass
class ProviderConfig:
    """Configuration for individual providers."""
    timeout: int = 5000
    max_sockets: int = 5
    max_free_sockets: int = 2
    retries: int = 1
    retry_delay: int = 100


class AutoplayError(Exception):
    """Base exception for autoplay errors."""
    pass


class RateLimitError(AutoplayError):
    """Exception raised when rate limited."""
    pass


class TimeoutError(AutoplayError):
    """Exception raised when operation times out."""
    pass


class ProviderError(AutoplayError):
    """Exception raised by providers."""
    pass
