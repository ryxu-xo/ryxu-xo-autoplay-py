"""
Tests for autoplay providers.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from autoplay.providers import YouTubeProvider, SpotifyProvider, SoundCloudProvider
from autoplay.types import LavalinkTrackInfo, AutoplaySource


@pytest.fixture
def track_info():
    """Create a track info instance for testing."""
    return LavalinkTrackInfo(
        title="Test Song",
        author="Test Artist",
        identifier="test123",
        uri="https://open.spotify.com/track/test123",
        source_name="spotify"
    )


@pytest.fixture
def youtube_provider():
    """Create a YouTube provider for testing."""
    return YouTubeProvider()


@pytest.fixture
def spotify_provider():
    """Create a Spotify provider for testing."""
    return SpotifyProvider()


@pytest.fixture
def soundcloud_provider():
    """Create a SoundCloud provider for testing."""
    return SoundCloudProvider()


def test_youtube_provider_creation(youtube_provider):
    """Test YouTube provider creation."""
    assert youtube_provider.source == AutoplaySource.YOUTUBE
    assert youtube_provider.eura is None


def test_spotify_provider_creation(spotify_provider):
    """Test Spotify provider creation."""
    assert spotify_provider.source == AutoplaySource.SPOTIFY
    assert spotify_provider.eura is None


def test_soundcloud_provider_creation(soundcloud_provider):
    """Test SoundCloud provider creation."""
    assert soundcloud_provider.source == AutoplaySource.SOUNDCLOUD


def test_youtube_provider_set_eura(youtube_provider):
    """Test setting Euralink instance for YouTube provider."""
    mock_eura = Mock()
    youtube_provider.set_eura(mock_eura)
    assert youtube_provider.eura == mock_eura


def test_spotify_provider_set_eura(spotify_provider):
    """Test setting Euralink instance for Spotify provider."""
    mock_eura = Mock()
    spotify_provider.set_eura(mock_eura)
    assert spotify_provider.eura == mock_eura


def test_youtube_provider_create_search_query(youtube_provider, track_info):
    """Test creating search query from track info."""
    query = youtube_provider.create_search_query(track_info)
    assert "Test Song" in query
    assert "Test Artist" in query


def test_spotify_provider_extract_track_id(spotify_provider):
    """Test extracting track ID from query."""
    track_id = spotify_provider.extract_track_id_from_query("mix:track:abc123")
    assert track_id == "abc123"
    
    track_id = spotify_provider.extract_track_id_from_query("invalid query")
    assert track_id is None


def test_soundcloud_provider_extract_track_id(soundcloud_provider):
    """Test extracting track ID from SoundCloud URL."""
    track_id = soundcloud_provider.extract_track_id("https://soundcloud.com/user/track-123")
    assert track_id == "123"
    
    track_id = soundcloud_provider.extract_track_id("https://invalid-url.com")
    assert track_id is None


def test_provider_validate_track_info(youtube_provider, track_info):
    """Test track info validation."""
    assert youtube_provider.validate_track_info(track_info) is True
    
    # Test with invalid track info
    invalid_track = LavalinkTrackInfo(
        title="",
        author="Test Artist",
        identifier="test123",
        uri="https://spotify.com/track/test123",
        source_name="spotify"
    )
    assert youtube_provider.validate_track_info(invalid_track) is False
    
    # Test with None track info
    assert youtube_provider.validate_track_info(None) is False


def test_provider_create_success_result(youtube_provider):
    """Test creating success result."""
    result = youtube_provider.create_success_result(
        "https://youtube.com/watch?v=test123",
        "test123",
        {"test": "data"}
    )
    
    assert result.success is True
    assert result.url == "https://youtube.com/watch?v=test123"
    assert result.track_id == "test123"
    assert result.source == AutoplaySource.YOUTUBE
    assert result.metadata == {"test": "data"}


def test_provider_create_error_result(youtube_provider):
    """Test creating error result."""
    result = youtube_provider.create_error_result("Test error", {"test": "data"})
    
    assert result.success is False
    assert result.error == "Test error"
    assert result.source == AutoplaySource.YOUTUBE
    assert result.metadata == {"test": "data"}


def test_provider_handle_error(youtube_provider):
    """Test handling exceptions."""
    error = Exception("Test exception")
    result = youtube_provider.handle_error(error, {"test": "data"})
    
    assert result.success is False
    assert result.error == "Test exception"
    assert result.source == AutoplaySource.YOUTUBE
    assert result.metadata == {"test": "data"}
