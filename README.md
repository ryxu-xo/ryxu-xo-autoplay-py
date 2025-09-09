# ryxu-xo-autoplay (Python)

A high-performance autoplay API for Lavalink clients with source-to-source continuity, optimized for low CPU/RAM usage and fast response times.

## Features

- 🎵 **Source-to-Source Autoplay**: Spotify → Spotify, YouTube → YouTube, SoundCloud → SoundCloud
- ⚡ **High Performance**: Optimized for low CPU/RAM usage with fast response times
- 🔄 **Intelligent Repeat Prevention**: Track history system prevents playing the same songs repeatedly
- 🎯 **Universal Lavalink Support**: Works with any Lavalink client (Euralink, erela.js, discord-player, etc.)
- 🛡️ **Robust Error Handling**: Comprehensive error handling with retry logic
- 📊 **Event System**: Real-time events for success, errors, and rate limiting
- 🔧 **Configurable**: Highly configurable timeouts, retries, and limits

## Installation

### From PyPI (when published)
```bash
pip install ryxu-xo-autoplay
```

### Development Installation
```bash
git clone https://github.com/ryxu-xo/ryxu-xo-autoplay.git
cd ryxu-xo-autoplay/python\ version
pip install -e .
```

## Quick Start

```python
import asyncio
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig

async def main():
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
    else:
        print(f"Autoplay failed: {result.error}")

asyncio.run(main())
```

## Configuration

```python
from autoplay import AutoplayConfig

config = AutoplayConfig(
    max_retries=1,           # Number of retries for failed requests
    timeout=5000,            # Request timeout in milliseconds
    rate_limit_delay=500,    # Delay between requests to prevent rate limiting
    max_recommendations=5,   # Maximum number of recommendations to fetch
    max_tracks=10,           # Maximum number of tracks to consider
    enable_radio_mode=False, # Enable YouTube radio mode (less variety)
    max_history_size=50      # Maximum number of tracks to remember per guild
)
```

## Source-to-Source Autoplay

The package automatically detects the source of the current track and finds similar tracks from the same source:

- **Spotify** → Uses Lavalink `sprec` source for recommendations
- **YouTube** → Uses Lavalink `ytsearch` to find similar tracks
- **SoundCloud** → Uses web scraping to find recommended tracks

## Wavelink Integration

```python
import discord
from discord.ext import commands
import wavelink
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig

# Bot setup
bot = commands.Bot(command_prefix='?', intents=discord.Intents.default())

# Autoplay setup
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

@bot.event
async def on_ready():
    # Initialize Wavelink
    nodes = [wavelink.Node(uri="ws://localhost:2333", password="youshallnotpass")]
    await wavelink.Pool.connect(nodes=nodes, client=bot, cache_capacity=100)
    autoplay.set_eura(wavelink.Pool)

@bot.event
async def on_wavelink_track_end(payload):
    player = payload.player
    if not player.queue and player.autoplay == wavelink.AutoPlayMode.enabled:
        # Create track info from the ended track
        track_info = LavalinkTrackInfo(
            title=payload.track.title,
            author=payload.track.author,
            identifier=payload.track.identifier,
            uri=payload.track.uri,
            source_name=payload.track.source
        )
        
        # Get next track
        result = await autoplay.get_next_track(track_info, str(player.guild.id))
        
        if result.success:
            tracks = await wavelink.Playable.search(result.url)
            if tracks and not isinstance(tracks, wavelink.Playlist):
                await player.queue.put_wait(tracks[0])
                await player.play(player.queue.get())
```

## Other Lavalink Clients

### erela.js (JavaScript)
```javascript
const { LavalinkAutoplay } = require('ryxu-xo-autoplay');

const autoplay = new LavalinkAutoplay({
    maxRetries: 1,
    timeout: 5000,
    rateLimitDelay: 500,
    maxRecommendations: 5,
    maxTracks: 10,
    enableRadioMode: false,
    maxHistorySize: 50
});

// Set your Lavalink client
autoplay.setEura(yourErelaClient);

// Use in track end event
player.on('trackEnd', async (player, track, reason) => {
    if (!player.queue.length) {
        const result = await autoplay.getNextTrack(track, player.guild.id);
        if (result.success) {
            player.play(result.url);
        }
    }
});
```

### discord-player (JavaScript)
```javascript
const { LavalinkAutoplay } = require('ryxu-xo-autoplay');

const autoplay = new LavalinkAutoplay({
    maxRetries: 1,
    timeout: 5000,
    rateLimitDelay: 500,
    maxRecommendations: 5,
    maxTracks: 10,
    enableRadioMode: false,
    maxHistorySize: 50
});

// Set your Lavalink client
autoplay.setEura(player);

// Use in track end event
player.events.on('playerFinish', async (queue, track) => {
    if (!queue.tracks.length) {
        const result = await autoplay.getNextTrack(track, queue.guild.id);
        if (result.success) {
            queue.addTrack(result.url);
        }
    }
});
```

### Lavalink.py (Python)
```python
import discord
from discord.ext import commands
import lavalink
from lavalink.events import TrackEndEvent, QueueEndEvent
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Initialize Lavalink
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                  region='us', name='default-node')
        
        self.lavalink = bot.lavalink
        self.lavalink.add_event_hooks(self)
        
        # Initialize autoplay
        self.autoplay = LavalinkAutoplay(AutoplayConfig(
            max_retries=1,
            timeout=5000,
            rate_limit_delay=500,
            max_history_size=50
        ))
        self.autoplay.set_eura(self.lavalink)

    @lavalink.listener(TrackEndEvent)
    async def on_track_end(self, event: TrackEndEvent):
        player = event.player
        if not player.queue:
            # Create track info from the ended track
            track_info = LavalinkTrackInfo(
                title=event.track.title,
                author=event.track.author,
                identifier=event.track.identifier,
                uri=event.track.uri,
                source_name=event.track.source
            )
            
            # Get next track using autoplay
            result = await self.autoplay.get_next_track(track_info, str(player.guild_id))
            
            if result.success:
                # Search for the track using Lavalink
                tracks = await player.node.get_tracks(result.url)
                if tracks and tracks.tracks:
                    track = tracks.tracks[0]
                    track.extra["requester"] = "autoplay"
                    player.add(track=track)
                    await player.play()

    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        guild_id = event.player.guild_id
        guild = self.bot.get_guild(guild_id)
        if guild is not None:
            await guild.voice_client.disconnect(force=True)
```

### Wavelink (Python) - **Archived**
> **Note**: [Wavelink is no longer maintained](https://github.com/PythonistaGuild/Wavelink) as of April 2025. Consider using Lavalink.py or other alternatives.

```python
import wavelink
from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig

# Wavelink integration (deprecated)
autoplay = LavalinkAutoplay(AutoplayConfig(
    max_retries=1,
    timeout=5000,
    rate_limit_delay=500,
    max_history_size=50
))

@bot.event
async def on_wavelink_track_end(payload):
    player = payload.player
    if not player.queue and player.autoplay == wavelink.AutoPlayMode.enabled:
        track_info = LavalinkTrackInfo(
            title=payload.track.title,
            author=payload.track.author,
            identifier=payload.track.identifier,
            uri=payload.track.uri,
            source_name=payload.track.source
        )
        
        result = await autoplay.get_next_track(track_info, str(player.guild.id))
        if result.success:
            tracks = await wavelink.Playable.search(result.url)
            if tracks and not isinstance(tracks, wavelink.Playlist):
                await player.queue.put_wait(tracks[0])
                await player.play(player.queue.get())
```

## Event System

```python
# Set up event listeners
def on_success(data):
    print(f"Autoplay success: {data['source']} - {data['result'].url}")

def on_error(data):
    print(f"Autoplay error: {data['source']} - {data['error']}")

autoplay.events.on('success', on_success)
autoplay.events.on('error', on_error)
```

## API Reference

### LavalinkAutoplay

Main autoplay class.

#### Methods

- `get_next_track(track_info: LavalinkTrackInfo, guild_id: str) -> AutoplayResult`
  - Get the next track for autoplay based on the current track
  
- `get_next_track_for_source(track_info: LavalinkTrackInfo, source: AutoplaySource, guild_id: str) -> AutoplayResult`
  - Get the next track for a specific source
  
- `set_eura(lavalink_instance)`
  - Set the Lavalink client instance for track resolution
  
- `clear_history(guild_id: Optional[str] = None)`
  - Clear track history for a guild or all guilds

### LavalinkTrackInfo

Track information structure.

```python
LavalinkTrackInfo(
    title="Song Title",
    author="Artist Name",
    identifier="track_id",
    uri="https://...",
    source_name="spotify"  # or "youtube", "soundcloud"
)
```

### AutoplayResult

Result of an autoplay operation.

```python
AutoplayResult(
    success=True,
    url="https://...",
    track_id="track_id",
    source=AutoplaySource.SPOTIFY,
    metadata={...}
)
```

## Performance Optimizations

The package is optimized for high performance and low resource usage:

- **Reduced Timeouts**: 5-second timeouts instead of 8 seconds
- **Fewer Retries**: 1 retry instead of 2 for faster failure recovery
- **Lower Rate Limits**: 500ms delays instead of 1000ms
- **Connection Pooling**: Efficient HTTP connection reuse
- **Memory Management**: Limited response sizes and history tracking
- **Async Operations**: Non-blocking I/O operations

## Error Handling

The package provides comprehensive error handling:

- `AutoplayError`: Base exception for autoplay errors
- `RateLimitError`: Raised when rate limited
- `TimeoutError`: Raised when operations timeout
- `ProviderError`: Raised by individual providers

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=autoplay
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For support and questions:
- Create an issue on GitHub
- Join our Discord server (if available)

---

**Note**: Many Lavalink clients have their own autoplay systems. This package is an alternative implementation with additional features, optimizations, and cross-client compatibility.
