"""
ryxu-xo-autoplay - Python version
A high-performance autoplay API for Lavalink clients with source-to-source continuity.
"""

from .autoplay import LavalinkAutoplay
from .types import LavalinkTrackInfo, AutoplayResult, AutoplayConfig
from .providers import YouTubeProvider, SpotifyProvider, SoundCloudProvider

__version__ = "1.0.0"
__author__ = "ryxu-xo"

__all__ = [
    "LavalinkAutoplay",
    "LavalinkTrackInfo", 
    "AutoplayResult",
    "AutoplayConfig",
    "YouTubeProvider",
    "SpotifyProvider", 
    "SoundCloudProvider"
]
