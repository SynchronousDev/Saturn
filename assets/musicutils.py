import random
from datetime import datetime as dt
from enum import Enum

import discord
import spotipy
import wavelink  # woo wavelink stuff
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials

from .errors import *
from .utils import *

# I originally had this in the music cog, but now that I put it in here it helps me keep my stuff more organized

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

    @property
    def tracks(self):
        return self._queue

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

    def remove(self, track_id):
        if not self._queue:
            raise QueueIsEmpty

        elif track_id > len(self._queue):
            raise TrackDoesNotExist

        self._queue.pop(int(track_id) - 1)


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
            if self.queue.length == 0:
                em = discord.Embed(
                    description=f"{SHARD} Playing [`{tracks[0].title}`]"
                                f"(https://www.youtube.com/watch?v={tracks[0].ytid})",
                    color=MAIN)
                em.set_image(url=tracks[0].thumb)
                await ctx.send(embed=em)
            else:
                em = discord.Embed(
                    description=f"{SHARD} Added [`{tracks[0].title}`](https://www.youtube.com/watch?v="
                                f"{tracks[0].ytid}) to the queue.",
                    color=MAIN)
                em.set_image(url=tracks[0].thumb)
                await ctx.send(embed=em)

            self.queue.add(tracks[0])

        else:
            if (track := await self.get_first_track(tracks)) is not None:
                if self.queue.length == 0:
                    em = discord.Embed(
                        description=f"{SHARD} Playing [`{tracks[0].title}`]"
                                    f"(https://www.youtube.com/watch?v={tracks[0].ytid})",
                        color=MAIN)
                    em.set_image(url=tracks[0].thumb)
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(
                        description=f"{SHARD} Added [`{tracks[0].title}`]"
                                    f"(https://www.youtube.com/watch?v={tracks[0].ytid}) to the queue.",
                        color=MAIN)
                    em.set_image(url=tracks[0].thumb)
                    await ctx.send(embed=em)

                self.queue.add(track)

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def get_first_track(self, tracks):
        if len(tracks):
            return tracks[0]
        else:
            return NoTracksFound

    async def search_tracks(self, ctx, tracks):
        embed = discord.Embed(
            title=f"Search for Music",
            description=(
                "\n".join(
                    f"[{t.title}](https://www.youtube.com/watch?v={t.ytid}) "
                    f"({t.length // 60000}:{str(t.length % 60).zfill(2)})"
                    for t in tracks[:15])
            ),
            colour=MAIN,
            timestamp=dt.utcnow()
        )
        embed.set_image(url=tracks[0].thumb)
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

    async def remove_track(self, track_id):
        # pointer to the Queue.remove function
        # why does this even exist lol
        self.queue.remove(track_id)


class SpotifyClient:
    def __init__(self, id, secret):
        self.credentials_manager = SpotifyClientCredentials(id, secret)
        self.sp = spotipy.Spotify(client_credentials_manager=self.credentials_manager)

    def get_track(self, url: str):
        track = self.sp.track(url)
        return track["name"] + track["artists"][0]["name"]
