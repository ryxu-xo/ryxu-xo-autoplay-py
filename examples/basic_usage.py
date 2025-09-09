"""
Basic usage example of the autoplay package.
"""

import asyncio
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig


async def main():
    """Basic autoplay example."""
    # Create autoplay instance with optimized config
    config = AutoplayConfig(
        max_retries=1,
        timeout=5000,
        rate_limit_delay=500,
        max_recommendations=5,
        max_tracks=10,
        enable_radio_mode=False,
        max_history_size=50
    )
    
    autoplay = LavalinkAutoplay(config)
    
    # Set up event listeners
    def on_success(data):
        print(f"[Autoplay] Success: {data['source']} - {data['result'].url}")
    
    def on_error(data):
        print(f"[Autoplay] Error: {data['source']} - {data['error']}")
    
    autoplay.events.on('success', on_success)
    autoplay.events.on('error', on_error)
    
    # Example track info
    track_info = LavalinkTrackInfo(
        title="YUKON",
        author="Justin Bieber",
        identifier="29iva9idM6rFCPUlu7Rhxl",
        uri="https://open.spotify.com/track/29iva9idM6rFCPUlu7Rhxl",
        source_name="spotify"
    )
    
    guild_id = "123456789"
    
    # Get next track
    result = await autoplay.get_next_track(track_info, guild_id)
    
    if result.success:
        print(f"Next track: {result.url}")
        print(f"Track ID: {result.track_id}")
        print(f"Source: {result.source}")
        if result.metadata:
            print(f"Metadata: {result.metadata}")
    else:
        print(f"Autoplay failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
