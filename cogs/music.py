import asyncio
import datetime as dt
from logging import NOTSET
import random
import re
import typing as t
from enum import Enum

import discord
import wavelink
from discord.ext import commands

from data.const import *

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidRepeatMode(commands.CommandError):
    pass


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
        if mode == "no repeat":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "repeat one":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "repeat all":
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
                description=f"{NOTE} Added `{tracks[0].title}` to the queue.",
                color=MAIN)
            em.set_image(url=tracks[0].thumb)
            await ctx.send(embed=em)
        else:
            if (track := await self.get_first_track(tracks)) is not None:
                self.queue.add(track)
                em = discord.Embed(
                    description=f"{NOTE} Added `{track.title}` to the queue.",
                    color=MAIN)
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
            title=f"Halfnote's Searches",
            description=(
                "\n".join(
                    f"**{i + 1}) **[{t.title}](https://www.youtube.com/watch?v={t.ytid}) ({t.length//60000}:{str(t.length%60).zfill(2)})"
                    for i, t in enumerate(tracks[:15])
                )
            ),
            colour=MAIN,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_footer(text=f"Halfnote's Searches")

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
            em = discord.Embed(
                description=f"{ERROR} Commands are not available in DMs.",
                color=RED)
            await ctx.send(embed=em)
            return False

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

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(name="connect", aliases=["join", "c", 'conn'])
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        em = discord.Embed(
                description=f"{NOTE} Connected to `{channel.name}`.",
                color=MAIN)
        await ctx.send(embed=em)

    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            em = discord.Embed(
                    description=f"{ERROR} Already connected to a channel.",
                    color=RED)
            await ctx.send(embed=em)
        elif isinstance(exc, NoVoiceChannel):
            em = discord.Embed(
                    description=f"{ERROR} You are not in a voice channel.",
                    color=RED)
            await ctx.send(embed=em)

    @commands.command(name="disconnect", aliases=["leave", 'd', 'dconn'])
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        em = discord.Embed(
                description=f"{NOTE} Disconnected.",
                color=MAIN)
        await ctx.send(embed=em)

    @commands.command(name="play", aliases=['p', 'pl'])
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)

        if query is None:
            if player.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            em = discord.Embed(
                description=f"{NOTE} Playing.",
                color=MAIN)
            await ctx.send(embed=em)

        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} No songs to play as the queue is empty.",
                color=RED)
            await ctx.send(embed=em)
        elif isinstance(exc, NoVoiceChannel):
            em = discord.Embed(
                description=f"{ERROR} You are not in a voice channel.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="pause", aliases=['ps'])
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        if player.is_paused:
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        em = discord.Embed(
                description=f"{NOTE} Paused.",
                color=MAIN)
        await ctx.send(embed=em)

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            em = discord.Embed(
                description=f"{ERROR} Player is already paused.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="stop", aliases=['stp'])
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        em = discord.Embed(
                description=f"{NOTE} Stopped playing music.",
                color=MAIN)
        await ctx.send(embed=em)

    @commands.command(name="next", aliases=["skip", 'n', 'nxt'])
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        em = discord.Embed(
                description=f"{NOTE} Skipped to next track.",
                color=MAIN)
        await ctx.send(embed=em)

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} Could not skip to next track as queue is empty.",
                color=RED)
            await ctx.send(embed=em)
        elif isinstance(exc, NoMoreTracks):
            em = discord.Embed(
                description=f"{ERROR} There are no more tracks in the queue.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="previous", aliases=['prev', 'prvs'])
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        em = discord.Embed(
                description=f"{NOTE} Playing previous track in the queue.",
                color=MAIN)
        await ctx.send(embed=em)

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} Could not skip to previous track as queue is empty.",
                color=RED)
            await ctx.send(embed=em)
        elif isinstance(exc, NoPreviousTracks):
            em = discord.Embed(
                description=f"{ERROR} There are no previous tracks in the queue.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="shuffle", aliases=['shffl', 'sf'])
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.shuffle()
        em = discord.Embed(
            description=f"{NOTE} Shuffled the queue.",
            color=MAIN)
        await ctx.send(embed=em)

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} Queue is empty, and cannot be shuffled.",
                color=RED)
            await ctx.send(embed=em)


    @commands.command(name="repeat", aliases=['r', 'rpt'])
    async def repeat(self, ctx, mode: t.Optional[str]):
        if mode:
            mode = mode.lower()
            if mode in ('one', 'once'):
                mode = '1'
            if mode not in ("none", "1", "all"):
                raise InvalidRepeatMode
            else:
                em = discord.Embed(
                    description=f"{NOTE} Set repeat mode to `{mode}`.",
                    color=MAIN)
                await ctx.send(embed=em)
                return
        
        em = discord.Embed(
            title='Choose a repeat mode',
            color=MAIN)
        em.add_field(name=f"Repeat Modes", value=f"{NO_REPEAT} - `Nothing will be repeated`"
                          f"\n{REPEAT_ONE} - `Track will be repeated`\n{REPEAT_ALL} - `Queue will be repeated`")
        em.set_thumbnail(url=self.bot.user.avatar_url)
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
                mode = 'no repeat'

            elif str(reaction.emoji) == REPEAT_ONE:
                player.queue.set_repeat_mode('1')
                mode = 'repeat one'

            elif str(reaction.emoji) == REPEAT_ALL:
                player.queue.set_repeat_mode('all')
                mode = 'repeat all'

        em = discord.Embed(
            description=f"{NOTE} Set repeat mode to `{mode}`.",
            color=MAIN)
        await ctx.send(embed=em)

    @repeat.error
    async def repeat_error(self, ctx, exc):
        if isinstance(exc, InvalidRepeatMode):
            em = discord.Embed(
                description=f"{ERROR} Invalid repeat mode specified.",
                color=RED)
            await ctx.send(embed=em)
        elif isinstance(exc, commands.MissingRequiredArgument):
            em = discord.Embed(
                description=f"{ERROR} No repeat mode was given.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="queue", aliases=['q'])
    async def queue_command(self, ctx):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Halfnote's Queue",
            colour=MAIN,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(    
            name="Current Track",
            value=f"[{player.queue.current_track.title}](https://www.youtube.com/watch?v={player.queue.current_track.ytid})"
                  if player.queue.current_track else "No tracks are playing right now.", inline=False
        )
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Upcomming Tracks",
                value="\n".join(f"[{t.title}](https://www.youtube.com/watch?v={t.ytid})" for t in upcoming[:10]),
                inline=False
            )
        await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} Queue is currently empty.",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(
        name='search',
        aliases=['srch', 'sr', 's'])
    async def search(self, ctx, *, query):
        player = self.get_player(ctx)
        query = query.strip("<>")
        if not re.match(URL_REGEX, query):
            query = f"ytsearch:{query}"

        await player.search_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command(
        name='remove',
        aliases=['rmv', 'rm'])
    async def remove(self, ctx, *, track_id: int):
        


    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            return
                    
        if isinstance(exc, QueueIsEmpty):
            return
            
        if isinstance(exc, NoTracksFound):
            return
            
        if isinstance(exc, InvalidRepeatMode):
            return
            
        if isinstance(exc, NoVoiceChannel):
            return
            
        if isinstance(exc, NoMoreTracks):
            return
            
        if isinstance(exc, NoPreviousTracks):
            return
            
        if isinstance(exc, PlayerIsAlreadyPaused):
            return

        if isinstance(exc, commands.MissingRequiredArgument):
            return

        else:
            raise exc
            

def setup(bot):
    bot.add_cog(Music(bot))