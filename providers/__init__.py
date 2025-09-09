"""Autoplay providers for different music sources."""

from .base import BaseProvider
from .youtube import YouTubeProvider
from .spotify import SpotifyProvider
from .soundcloud import SoundCloudProvider

__all__ = [
    "BaseProvider",
    "YouTubeProvider", 
    "SpotifyProvider",
    "SoundCloudProvider"
]
