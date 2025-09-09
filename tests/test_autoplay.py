"""
Tests for the main autoplay class.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig, AutoplaySource


@pytest.fixture
def autoplay():
    """Create an autoplay instance for testing."""
    config = AutoplayConfig(
        max_retries=1,
        timeout=5000,
        rate_limit_delay=500,
        max_recommendations=5,
        max_tracks=10,
        enable_radio_mode=False,
        max_history_size=50
    )
    return LavalinkAutoplay(config)


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


@pytest.mark.asyncio
async def test_get_next_track_success(autoplay, track_info):
    """Test successful track retrieval."""
    # Mock the provider
    mock_provider = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_result.url = "https://open.spotify.com/track/next123"
    mock_result.track_id = "next123"
    mock_result.source = AutoplaySource.SPOTIFY
    mock_result.metadata = {"test": "data"}
    
    mock_provider.get_next_track = AsyncMock(return_value=mock_result)
    autoplay.providers[AutoplaySource.SPOTIFY] = mock_provider
    
    guild_id = "123456789"
    result = await autoplay.get_next_track(track_info, guild_id)
    
    assert result.success is True
    assert result.url == "https://open.spotify.com/track/next123"
    assert result.track_id == "next123"
    assert result.source == AutoplaySource.SPOTIFY
    assert result.metadata == {"test": "data"}


@pytest.mark.asyncio
async def test_get_next_track_failure(autoplay, track_info):
    """Test failed track retrieval."""
    # Mock the provider to return failure
    mock_provider = Mock()
    mock_result = Mock()
    mock_result.success = False
    mock_result.error = "No tracks found"
    mock_result.source = AutoplaySource.SPOTIFY
    
    mock_provider.get_next_track = AsyncMock(return_value=mock_result)
    autoplay.providers[AutoplaySource.SPOTIFY] = mock_provider
    
    guild_id = "123456789"
    result = await autoplay.get_next_track(track_info, guild_id)
    
    assert result.success is False
    assert result.error == "No tracks found"
    assert result.source == AutoplaySource.SPOTIFY


@pytest.mark.asyncio
async def test_get_next_track_no_track_info(autoplay):
    """Test with no track info."""
    guild_id = "123456789"
    result = await autoplay.get_next_track(None, guild_id)
    
    assert result.success is False
    assert result.error == "No track info provided"


@pytest.mark.asyncio
async def test_get_next_track_for_source(autoplay, track_info):
    """Test getting next track for specific source."""
    # Mock the provider
    mock_provider = Mock()
    mock_result = Mock()
    mock_result.success = True
    mock_result.url = "https://youtube.com/watch?v=next123"
    mock_result.track_id = "next123"
    mock_result.source = AutoplaySource.YOUTUBE
    
    mock_provider.get_next_track = AsyncMock(return_value=mock_result)
    autoplay.providers[AutoplaySource.YOUTUBE] = mock_provider
    
    guild_id = "123456789"
    result = await autoplay.get_next_track_for_source(track_info, AutoplaySource.YOUTUBE, guild_id)
    
    assert result.success is True
    assert result.url == "https://youtube.com/watch?v=next123"
    assert result.track_id == "next123"
    assert result.source == AutoplaySource.YOUTUBE


def test_map_source_name(autoplay):
    """Test source name mapping."""
    # Test various source name formats
    assert autoplay.map_source_name("spotify") == AutoplaySource.SPOTIFY
    assert autoplay.map_source_name("youtube") == AutoplaySource.YOUTUBE
    assert autoplay.map_source_name("soundcloud") == AutoplaySource.SOUNDCLOUD
    assert autoplay.map_source_name("sp") == AutoplaySource.SPOTIFY
    assert autoplay.map_source_name("yt") == AutoplaySource.YOUTUBE
    assert autoplay.map_source_name("sc") == AutoplaySource.SOUNDCLOUD
    assert autoplay.map_source_name("spsearch") == AutoplaySource.SPOTIFY
    assert autoplay.map_source_name("ytsearch") == AutoplaySource.YOUTUBE
    assert autoplay.map_source_name("scsearch") == AutoplaySource.SOUNDCLOUD


def test_track_history(autoplay):
    """Test track history functionality."""
    guild_id = "123456789"
    track_id = "test123"
    
    # Test adding to history
    autoplay.add_to_history(guild_id, track_id)
    assert autoplay.is_in_history(guild_id, track_id) is True
    
    # Test clearing history
    autoplay.clear_history(guild_id)
    assert autoplay.is_in_history(guild_id, track_id) is False
    
    # Test clearing all history
    autoplay.add_to_history(guild_id, track_id)
    autoplay.clear_history()
    assert autoplay.is_in_history(guild_id, track_id) is False


def test_set_eura(autoplay):
    """Test setting Euralink instance."""
    mock_eura = Mock()
    autoplay.set_eura(mock_eura)
    
    assert autoplay.eura == mock_eura
    assert autoplay.providers[AutoplaySource.YOUTUBE].eura == mock_eura
    assert autoplay.providers[AutoplaySource.SPOTIFY].eura == mock_eura
