import discord
from discord.ext import commands
import youtube_dl as ydl
import typing as t

from assets import *

log = logging.getLogger(__name__)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='join',
        aliases=['j', 'connect', 'conn'],
        description='Make the bot join your voice channel.',
    )
    async def join_channel(self, ctx):
        channel = await self._connect(ctx)
        em = discord.Embed(
            description=f"{CHECK} Connected to `{channel}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='leave',
        aliases=['disconnect', 'dconn'],
        description='Make the bot leave your voice channel.'
    )
    async def leave_channel(self, ctx):
        await self._disconnect(ctx)
        em = discord.Embed(
            description=f"{CHECK} Disconnected.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='play',
        aliases=['pl'],
        description='Play some music in your channel.'
    )
    async def play_music(self, ctx, url: t.Optional[str]):
        await self._connect(ctx)
        if not url:
            await self._resume(ctx)
            em = discord.Embed(
                description=f"{CHECK} Resumed.",
                colour=GREEN)
            return await ctx.send(embed=em)

        track = await self._play(ctx, url)

        _name = track.rstrip(".mp3")[:-12]
        em = discord.Embed(
            description=f"{SATURN} Now playing `{_name}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='pause',
        aliases=['ps'],
        description='Pause the currently playing music.'
    )
    async def pause_music(self, ctx):
        await self._pause(ctx)
        em = discord.Embed(
            description=f"{CHECK} Paused.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='stop',
        description='Stop the currently playing music.'
    )
    async def stop_playing(self, ctx):
        await self._stop(ctx)
        em = discord.Embed(
            description=f"{CHECK} Stopped.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='resume',
        aliases=['unpause'],
        description='Resume the currently playing music.'
    )
    async def resume_playing(self, ctx):
        await self._resume(ctx)
        em = discord.Embed(
            description=f"{CHECK} Resumed.",
            colour=GREEN)
        await ctx.send(embed=em)

    async def _pause(self, ctx):
        """
        Pause the player.
        """
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.pause()
            log.debug(msg='Paused')

        elif not voice:
            raise BotNotConnectedToChannel

        elif not ctx.author.voice:
            raise NotConnectedToChannel

        elif voice.is_paused():
            raise PlayerIsAlreadyPaused

    async def _resume(self, ctx):
        """
        Resume the player.
        """
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and not voice.is_playing():
            voice.resume()
            log.debug(msg='Resumed music')

        elif not voice:
            raise BotNotConnectedToChannel

        elif not ctx.author.voice:
            raise NotConnectedToChannel

        elif voice.is_playing():
            raise PlayerIsAlreadyResumed

    async def _stop(self, ctx):
        """
        Stop the player.
        For pausing, use the pause command.
        """
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            voice.stop()
            log.debug(msg='Stopped playing music')

        elif not voice:
            raise BotNotConnectedToChannel

        elif not ctx.author.voice:
            raise NotConnectedToChannel

        elif not voice.is_playing():
            raise PlayerIsAlreadyStopped

    async def _play(self, ctx, url):
        """
        Play music.
        """
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        _track = os.path.isfile('song.mp3')
        try:
            if _track:
                os.remove('song.mp3')
                log.info("Removed old song.mp3 file")

        except PermissionError:
            log.info("Attempted to remove old song.mp3 file, but song is currently being played.")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        with ydl.YoutubeDL(ydl_opts) as _ydl:
            _ydl.download([url])

        name = None
        for file in os.listdir('./'):
            if file.endswith('.mp3'):
                name = file
                log.info("Renamed old song file to song.mp3")
                os.rename(file, "song.mp3")

        voice.play(discord.FFmpegPCMAudio("song.mp3"))
        return name

    async def _connect(self, ctx):
        """
        Connect the bot to a voice channel.
        This is a method, for actually connecting the bot to a voice channel run the `connect` command.
        """
        if not ctx.author.voice:
            raise NotConnectedToChannel

        channel = ctx.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)

        else:
            voice = await channel.connect()

        return channel

    async def _disconnect(self, ctx):
        """
        Disconnect the bot from the voice channel. This is for general use, not as a developer command.
        """
        if not ctx.author.voice:
            raise NotConnectedToChannel

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()
            log.info(msg="Successfully disconnected from channel [{}]".format(channel.mention))
        else:
            raise BotNotConnectedToChannel


def setup(bot):
    bot.add_cog(Music(bot))
