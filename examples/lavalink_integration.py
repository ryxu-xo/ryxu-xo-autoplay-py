"""
Lavalink.py integration example for the autoplay package.
Based on the official Lavalink.py example from https://github.com/Devoxin/Lavalink.py
"""

import re
import discord
import lavalink
from discord.ext import commands
from lavalink.events import TrackStartEvent, TrackEndEvent, QueueEndEvent
from lavalink.errors import ClientError
from lavalink.server import LoadType

from autoplay import LavalinkAutoplay, LavalinkTrackInfo, AutoplayConfig

url_rx = re.compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(discord.VoiceProtocol):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.guild_id = channel.guild.id
        self._destroyed = False

        if not hasattr(self.client, 'lavalink'):
            # Instantiate a client if one doesn't exist.
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                          region='us', name='default-node')

        # Create a shortcut to the Lavalink client here.
        self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        channel_id = data['channel_id']

        if not channel_id:
            await self._destroy()
            return

        self.channel = self.client.get_channel(int(channel_id))

        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }

        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that would set channel_id
        # to None doesn't get dispatched after the disconnect
        player.channel_id = None
        await self._destroy()

    async def _destroy(self):
        self.cleanup()

        if self._destroyed:
            # Idempotency handling, if `disconnect()` is called, the changed voice state
            # could cause this to run a second time.
            return

        self._destroyed = True

        try:
            await self.lavalink.player_manager.destroy(self.guild_id)
        except ClientError:
            pass


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host='localhost', port=2333, password='youshallnotpass',
                                  region='us', name='default-node')

        self.lavalink: lavalink.Client = bot.lavalink
        self.lavalink.add_event_hooks(self)
        
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
        self.autoplay.set_lavalink_client(self.lavalink)

    def cog_unload(self):
        """
        This will remove any registered event hooks when the cog is unloaded.
        They will subsequently be registered again once the cog is loaded.

        This effectively allows for event handlers to be updated when the cog is reloaded.
        """
        self.lavalink._event_hooks.clear()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    async def create_player(ctx: commands.Context):
        """
        A check that is invoked before any commands marked with `@commands.check(create_player)` can run.

        This function will try to create a player for the guild associated with this Context, or raise
        an error which will be relayed to the user if one cannot be created.
        """
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        player = ctx.bot.lavalink.player_manager.create(ctx.guild.id)
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play',)

        voice_client = ctx.voice_client

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Check if we're in a voice channel. If we are, tell the user to join our voice channel.
            if voice_client is not None:
                raise commands.CommandInvokeError('You need to join my voice channel first.')

            # Otherwise, tell them to join any voice channel to begin playing music.
            raise commands.CommandInvokeError('Join a voicechannel first.')

        voice_channel = ctx.author.voice.channel

        if voice_client is None:
            if not should_connect:
                raise commands.CommandInvokeError("I'm not playing music.")

            permissions = voice_channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            if voice_channel.user_limit > 0:
                # A limit of 0 means no limit. Anything higher means that there is a member limit which we need to check.
                # If it's full, and we don't have "move members" permissions, then we cannot join it.
                if len(voice_channel.members) >= voice_channel.user_limit and not ctx.me.guild_permissions.move_members:
                    raise commands.CommandInvokeError('Your voice channel is full!')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        elif voice_client.channel.id != voice_channel.id:
            raise commands.CommandInvokeError('You need to be in my voicechannel.')

        return True

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
        guild_id = event.player.guild_id
        channel_id = event.player.fetch('channel')
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return await self.lavalink.player_manager.destroy(guild_id)

        channel = guild.get_channel(channel_id)

        if channel:
            await channel.send('Now playing: {} by {}'.format(event.track.title, event.track.author))

    @lavalink.listener(TrackEndEvent)
    async def on_track_end(self, event: TrackEndEvent):
        player = event.player
        guild_id = player.guild_id
        
        print(f'[Lavalink] Track ended: {event.track.title} - Reason: {event.reason}')

        # Check if queue is empty and we should autoplay
        if not player.queue:
            print(f'[Lavalink] Queue ended for guild {guild_id}')
            print(f'[Autoplay] Starting autoplay for guild {guild_id}')

            # Create track info from the ended track
            track_info = LavalinkTrackInfo(
                title=event.track.title,
                author=event.track.author,
                identifier=event.track.identifier,
                uri=event.track.uri,
                source_name=event.track.source
            )

            print(f'[Autoplay] Track info: {track_info.__dict__}')

            # Get next track using autoplay
            result = await self.autoplay.get_next_track(track_info, str(guild_id))

            if result.success:
                print(f'[Autoplay] Found next track: {result.url}')
                print(f'[Autoplay] Source: {result.source}')
                if result.metadata:
                    print(f'[Autoplay] Metadata: {result.metadata}')

                # Search for the track using Lavalink
                try:
                    tracks = await player.node.get_tracks(result.url)
                    if tracks and tracks.tracks:
                        track = tracks.tracks[0]
                        track.extra["requester"] = "autoplay"
                        player.add(track=track)
                        await player.play()
                        print(f'[Lavalink] Playing: {track.title} by {track.author}')
                    else:
                        print(f'[Autoplay] Failed to resolve autoplay URL: {result.url}')
                except Exception as e:
                    print(f'[Autoplay] Error playing autoplay track: {str(e)}')
            else:
                print(f'[Autoplay] No autoplay result: {result.error}')

    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        guild_id = event.player.guild_id
        guild = self.bot.get_guild(guild_id)

        if guild is not None:
            await guild.voice_client.disconnect(force=True)

    @commands.command(aliases=['p'])
    @commands.check(create_player)
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        embed = discord.Embed(color=discord.Color.blurple())

        # Valid load_types are:
        #   TRACK    - direct URL to a track
        #   PLAYLIST - direct URL to playlist
        #   SEARCH   - query prefixed with either "ytsearch:" or "scsearch:". This could possibly be expanded with plugins.
        #   EMPTY    - no results for the query (result.tracks will be empty)
        #   ERROR    - the track encountered an exception during loading
        if results.load_type == LoadType.EMPTY:
            return await ctx.send("I couldn't find any tracks for that query.")
        elif results.load_type == LoadType.PLAYLIST:
            tracks = results.tracks

            # Add all of the tracks from the playlist to the queue.
            for track in tracks:
                # requester isn't necessary but it helps keep track of who queued what.
                # You can store additional metadata by passing it as a kwarg (i.e. key=value)
                # Requester can be set with `track.requester = ctx.author.id`. Any other extra attributes
                # must be set via track.extra.
                track.extra["requester"] = ctx.author.id
                player.add(track=track)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
        else:
            track = results.tracks[0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track.title}]({track.uri})'

            # requester isn't necessary but it helps keep track of who queued what.
            # You can store additional metadata by passing it as a kwarg (i.e. key=value)
            # Requester can be set with `track.requester = ctx.author.id`. Any other extra attributes
            # must be set via track.extra.
            track.extra["requester"] = ctx.author.id

            player.add(track=track)

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=['dc'])
    @commands.check(create_player)
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # The necessary voice channel checks are handled in "create_player."
        # We don't need to duplicate code checking them again.

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        await ctx.send('✳ | Disconnected.')

    @commands.command()
    async def autoplaytest(self, ctx):
        """Test autoplay functionality."""
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel!")
            return

        # Get current track
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
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
        result = await self.autoplay.get_next_track(track_info, guild_id)

        if result.success:
            await ctx.send(f"✅ Autoplay test successful!\nNext track: {result.url}")
        else:
            await ctx.send(f"❌ Autoplay test failed: {result.error}")

    @commands.command()
    async def clearhistory(self, ctx):
        """Clear autoplay history for this guild."""
        guild_id = str(ctx.guild.id)
        self.autoplay.clear_history(guild_id)
        await ctx.send("✅ Autoplay history cleared for this guild!")


def setup(bot):
    bot.add_cog(Music(bot))
