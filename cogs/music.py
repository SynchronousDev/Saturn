import asyncio
import datetime as dt
import random
import re
import typing as t
from enum import Enum

import discord
import wavelink
from discord.ext import commands

from assets import *

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])) "


class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2

class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "one":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            em = discord.Embed(
                description=f"{CHECK} Added `{tracks[0].title}` to the queue.",
                color=GREEN)
            em.set_image(url=tracks[0].thumb)
            await ctx.send(embed=em)
        else:
            if (track := await self.get_first_track(tracks)) is not None:
                self.queue.add(track)
                em = discord.Embed(
                    description=f"{CHECK} Added `{track.title}` to the queue.",
                    color=GREEN)
                em.set_image(url=track.thumb)
                await ctx.send(embed=em)

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def get_first_track(self, tracks):
        if len(tracks):
            return tracks[0]
        else:
            return NoTracksFound

    async def search_tracks(self, ctx, tracks):
        embed = discord.Embed(
            title=f"Selenium's Searches",
            description=(
                "\n".join(
                    f"**{i + 1}) **[{t.title}](https://www.youtube.com/watch?v={t.ytid}) "
                    f"({t.length//60000}:{str(t.length%60).zfill(2)}) "
                    for i, t in enumerate(tracks[:15])
                )
            ),
            colour=MAIN,
            timestamp=dt.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Selenium's Searches")

        await ctx.send(embed=embed)

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f"Wavelink node [{node.identifier}] ready.")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            if ctx.command in self.bot.get_cog('Music').walk_commands():
                em = discord.Embed(
                    description=f"{ERROR} Commands are not available in DMs.",
                    color=RED)
                await ctx.send(embed=em)
                return False

            else:
                return True

        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": 2333,
                "rest_uri": "http://127.0.0.1:2333",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "us-east",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    # noinspection PyTypeChecker
    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(name="connect", aliases=["join", "c", 'conn'],
                      description='Connect to a voice channel.')
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx)
        em = discord.Embed(
                description=f"{CHECK} Connected to `{channel.name}`.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="disconnect", aliases=["leave", 'd', 'dconn'],
                      description='Disconnect from a voice channel.')
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        em = discord.Embed(
                description=f"{CHECK} Disconnected.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="play", aliases=['pl'],
                      descrption='Play some music.')
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)

        if query is None:
            if player.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            em = discord.Embed(
                description=f"{CHECK} Playing.",
                color=GREEN)
            await ctx.send(embed=em)

        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command(name="pause", aliases=['ps'],
                      description='Pause the currently playing music.')
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        if player.is_paused:
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        em = discord.Embed(
                description=f"{CHECK} Paused.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="stop", aliases=['stp'],
                      description='Stop the currently playing music.')
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        em = discord.Embed(
                description=f"{CHECK} Stopped playing music.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="next", aliases=["skip", 'n', 'nxt'],
                      description='Skip to the next song in the queue.')
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        em = discord.Embed(
                description=f"{CHECK} Skipped to next track.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="previous", aliases=['prev', 'prvs'],
                      description='Play the previous song in the queue.')
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        em = discord.Embed(
                description=f"{CHECK} Playing previous track in the queue.",
                color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="shuffle", aliases=['shffl', 'sf'],
                      description='Shuffles the queue.')
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.shuffle()
        em = discord.Embed(
            description=f"{CHECK} Shuffled the queue.",
            color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="repeat", aliases=['r', 'rpt'],
                      description='Set a song\'s repeat mode.')
    async def repeat(self, ctx, mode: t.Optional[str]):
        if mode:
            mode = mode.lower()
            if mode in ('one', 'once'):
                mode = '1'
            if mode not in ("none", "1", "all"):
                raise InvalidRepeatMode
            else:
                em = discord.Embed(
                    description=f"{CHECK} Set repeat mode to `{mode}`.",
                    color=GREEN)
                await ctx.send(embed=em)
                return
        
        em = discord.Embed(
            title='Choose a repeat mode',
            description='React to the emoji you want to set.',
            color=MAIN)
        msg = await ctx.send(embed=em)
        await msg.add_reaction(NO_REPEAT)
        await msg.add_reaction(REPEAT_ONE)
        await msg.add_reaction(REPEAT_ALL)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in (NO_REPEAT, REPEAT_ONE, REPEAT_ALL)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)

        except asyncio.TimeoutError:
            em = discord.Embed(
                description=f"{ERROR} User did not respond in time.",
                color=RED)
            await ctx.send(embed=em)
            return

        else:
            player = self.get_player(ctx)
            if str(reaction.emoji) == NO_REPEAT:
                player.queue.set_repeat_mode('none')
                mode = 'none'

            elif str(reaction.emoji) == REPEAT_ONE:
                player.queue.set_repeat_mode('1')
                mode = 'one'

            elif str(reaction.emoji) == REPEAT_ALL:
                player.queue.set_repeat_mode('all')
                mode = 'all'

        em = discord.Embed(
            description=f"{CHECK} Set repeat mode to `{mode}`.",
            color=GREEN)
        await ctx.send(embed=em)

    @commands.command(name="queue", aliases=['q'],
                      description='See your song queue.')
    async def queue_command(self, ctx):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Selenium's Queue",
            colour=MAIN,
            timestamp=dt.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(    
            name="Currently Playing",
            value=f"[{player.queue.current_track.title}](https://www.youtube.com/watch?v="
                  f"{player.queue.current_track.ytid})"
                  if player.queue.current_track else "No tracks are playing right now.", inline=False
        )
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Upcomming",
                value="\n".join(f"[{t.title}](https://www.youtube.com/watch?v={t.ytid})" for t in upcoming[:10]),
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(
        name='search',
        aliases=['srch', 'sr'],
        description='Search for some music.')
    async def search(self, ctx, *, query):
        player = self.get_player(ctx)
        query = query.strip("<>")
        if not re.match(URL_REGEX, query):
            query = f"ytsearch:{query}"

        await player.search_tracks(ctx, await self.wavelink.get_tracks(query))

    # TODO Add the ability to remove tracks from queue
    # TODO Reformat some stuff lol

def setup(bot):
    bot.add_cog(Music(bot))