"""
Wavelink integration example for the autoplay package.
"""

import asyncio
import logging
from typing import cast

import discord
from discord.ext import commands
import wavelink

from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig, AutoplaySource


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True

        discord.utils.setup_logging(level=logging.INFO)
        super().__init__(command_prefix="?", intents=intents)
        
        # Initialize autoplay
        self.autoplay = LavalinkAutoplay(AutoplayConfig(
            max_retries=1,
            timeout=5000,
            rate_limit_delay=500,
            max_recommendations=5,
            max_tracks=10,
            enable_radio_mode=False,
            max_history_size=50
        ))
        
        # Set up autoplay event listeners
        self.autoplay.events.on('success', self.on_autoplay_success)
        self.autoplay.events.on('error', self.on_autoplay_error)

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri="ws://localhost:2333", password="youshallnotpass")]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

    async def on_ready(self) -> None:
        logging.info("Logged in: %s | %s", self.user, self.user.id)
        logging.info("[Wavelink + Autoplay] Bot is ready! Try: ?play YUKON")

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logging.info("Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed)
        # Set the Wavelink pool as the "eura" instance for autoplay
        self.autoplay.set_lavalink_client(wavelink.Pool)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing")
        embed.description = f"**{track.title}** by `{track.author}`"

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)

        await player.home.send(embed=embed)

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

        track: wavelink.Playable = payload.track
        reason: str = payload.reason

        logging.info(f"[Wavelink] Track ended: {track.title} - Reason: {reason}")

        # Check if queue is empty and autoplay is enabled
        if not player.queue and player.autoplay == wavelink.AutoPlayMode.enabled:
            logging.info(f"[Wavelink] Queue ended for guild {player.guild.id}")
            logging.info(f"[Autoplay] Starting autoplay for guild {player.guild.id}")

            # Create track info from the ended track
            track_info = LavalinkTrackInfo(
                title=track.title,
                author=track.author,
                identifier=track.identifier,
                uri=track.uri,
                source_name=track.source
            )

            logging.info(f"[Autoplay] Track info: {track_info.__dict__}")

            # Get next track using autoplay
            result = await self.autoplay.get_next_track(track_info, str(player.guild.id))

            if result.success:
                logging.info(f"[Autoplay] Found next track: {result.url}")
                logging.info(f"[Autoplay] Source: {result.source}")
                if result.metadata:
                    logging.info(f"[Autoplay] Metadata: {result.metadata}")

                # Search for the track using Wavelink
                try:
                    tracks = await wavelink.Playable.search(result.url)
                    if tracks and not isinstance(tracks, wavelink.Playlist):
                        next_track = tracks[0]
                        await player.queue.put_wait(next_track)
                        await player.play(player.queue.get(), volume=30)
                        logging.info(f"[Wavelink] Playing: {next_track.title} by {next_track.author}")
                    else:
                        logging.error(f"[Autoplay] Failed to resolve autoplay URL: {result.url}")
                except Exception as e:
                    logging.error(f"[Autoplay] Error playing autoplay track: {str(e)}")
            else:
                logging.info(f"[Autoplay] No autoplay result: {result.error}")

    def on_autoplay_success(self, data):
        """Handle autoplay success events."""
        logging.info(f"[Autoplay] Success: {data['source']} - {data['result'].url}")

    def on_autoplay_error(self, data):
        """Handle autoplay error events."""
        logging.info(f"[Autoplay] Error: {data['source']} - {data['error']}")


bot: Bot = Bot()


@bot.command()
async def play(ctx: commands.Context, *, query: str) -> None:
    """Play a song with the given query."""
    if not ctx.guild:
        return

    player: wavelink.Player
    player = cast(wavelink.Player, ctx.voice_client)

    if not player:
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        except AttributeError:
            await ctx.send("Please join a voice channel first before using this command.")
            return
        except discord.ClientException:
            await ctx.send("I was unable to join this voice channel. Please try again.")
            return

    # Turn on AutoPlay to enabled mode
    player.autoplay = wavelink.AutoPlayMode.enabled

    # Lock the player to this channel
    if not hasattr(player, "home"):
        player.home = ctx.channel
    elif player.home != ctx.channel:
        await ctx.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
        return

    # Search for tracks
    tracks: wavelink.Search = await wavelink.Playable.search(query)
    if not tracks:
        await ctx.send(f"{ctx.author.mention} - Could not find any tracks with that query. Please try again.")
        return

    if isinstance(tracks, wavelink.Playlist):
        added: int = await player.queue.put_wait(tracks)
        await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
    else:
        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)
        await ctx.send(f"Added **`{track}`** to the queue.")

    if not player.playing:
        await player.play(player.queue.get(), volume=30)

    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass


@bot.command()
async def skip(ctx: commands.Context) -> None:
    """Skip the current song."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.skip(force=True)
    await ctx.message.add_reaction("\u2705")


@bot.command()
async def autoplaytest(ctx: commands.Context) -> None:
    """Test autoplay functionality."""
    if not ctx.voice_client:
        await ctx.send("Not connected to a voice channel!")
        return

    # Get current track
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player.current:
        await ctx.send("No track currently playing!")
        return

    # Create track info from current track
    track_info = LavalinkTrackInfo(
        title=player.current.title,
        author=player.current.author,
        identifier=player.current.identifier,
        uri=player.current.uri,
        source_name=player.current.source
    )

    guild_id = str(ctx.guild.id)
    result = await bot.autoplay.get_next_track(track_info, guild_id)

    if result.success:
        await ctx.send(f"✅ Autoplay test successful!\nNext track: {result.url}")
    else:
        await ctx.send(f"❌ Autoplay test failed: {result.error}")


@bot.command()
async def autoplaysource(ctx: commands.Context, source: str) -> None:
    """Test autoplay for a specific source."""
    if not ctx.voice_client:
        await ctx.send("Not connected to a voice channel!")
        return

    # Map source string to enum
    source_map = {
        'youtube': AutoplaySource.YOUTUBE,
        'spotify': AutoplaySource.SPOTIFY,
        'soundcloud': AutoplaySource.SOUNDCLOUD
    }

    if source.lower() not in source_map:
        await ctx.send("Invalid source! Use: youtube, spotify, or soundcloud")
        return

    # Get current track
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player.current:
        await ctx.send("No track currently playing!")
        return

    # Create track info from current track
    track_info = LavalinkTrackInfo(
        title=player.current.title,
        author=player.current.author,
        identifier=player.current.identifier,
        uri=player.current.uri,
        source_name=source.lower()
    )

    guild_id = str(ctx.guild.id)
    result = await bot.autoplay.get_next_track_for_source(track_info, source_map[source.lower()], guild_id)

    if result.success:
        await ctx.send(f"✅ {source.title()} autoplay test successful!\nNext track: {result.url}")
    else:
        await ctx.send(f"❌ {source.title()} autoplay test failed: {result.error}")


@bot.command()
async def clearhistory(ctx: commands.Context) -> None:
    """Clear autoplay history for this guild."""
    guild_id = str(ctx.guild.id)
    bot.autoplay.clear_history(guild_id)
    await ctx.send("✅ Autoplay history cleared for this guild!")


@bot.command()
async def nightcore(ctx: commands.Context) -> None:
    """Set the filter to a nightcore style."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    filters: wavelink.Filters = player.filters
    filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
    await player.set_filters(filters)

    await ctx.message.add_reaction("\u2705")


@bot.command(name="toggle", aliases=["pause", "resume"])
async def pause_resume(ctx: commands.Context) -> None:
    """Pause or Resume the Player depending on its current state."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.pause(not player.paused)
    await ctx.message.add_reaction("\u2705")


@bot.command()
async def volume(ctx: commands.Context, value: int) -> None:
    """Change the volume of the player."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.set_volume(value)
    await ctx.message.add_reaction("\u2705")


@bot.command(aliases=["dc"])
async def disconnect(ctx: commands.Context) -> None:
    """Disconnect the Player."""
    player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
    if not player:
        return

    await player.disconnect()
    await ctx.message.add_reaction("\u2705")


@bot.command()
async def help(ctx: commands.Context) -> None:
    """Show help message."""
    embed = discord.Embed(
        title="🎵 Wavelink Autoplay Bot Commands",
        description="Commands for the Wavelink autoplay bot",
        color=0x00ff00
    )
    
    embed.add_field(
        name="?play <query>",
        value="Play a song",
        inline=False
    )
    
    embed.add_field(
        name="?skip",
        value="Skip the current song",
        inline=False
    )
    
    embed.add_field(
        name="?autoplaytest",
        value="Test autoplay functionality",
        inline=False
    )
    
    embed.add_field(
        name="?autoplaysource <source>",
        value="Test autoplay for specific source (youtube/spotify/soundcloud)",
        inline=False
    )
    
    embed.add_field(
        name="?clearhistory",
        value="Clear autoplay history for this guild",
        inline=False
    )
    
    embed.add_field(
        name="?nightcore",
        value="Apply nightcore filter",
        inline=False
    )
    
    embed.add_field(
        name="?toggle / ?pause / ?resume",
        value="Pause or resume playback",
        inline=False
    )
    
    embed.add_field(
        name="?volume <value>",
        value="Change volume (0-100)",
        inline=False
    )
    
    embed.add_field(
        name="?disconnect / ?dc",
        value="Disconnect from voice channel",
        inline=False
    )
    
    await ctx.send(embed=embed)


async def main() -> None:
    async with bot:
        await bot.start("BOT_TOKEN_HERE")


if __name__ == "__main__":
    asyncio.run(main())
