from discord import Embed
from assets import *
from discord.ext import commands
import traceback
import sys
import random

log = logging.getLogger(__name__) 

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_messages = [
            "Too fast!",
            "Woah, too quick there!",
            "Slow down!",
            "This command's on cooldown!",
            "Do me a favour and slow down a little, you're overheating the systems.",
            "Congrats, you earned yourself an extra millisecond of cooldown.",
            "Take a chill pill!"
        ]

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(exc, commands.CommandNotFound):
            em = Embed(
                description=f"{ERROR} Command `{ctx.invoked_with}` does not exist.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MissingRequiredArgument):
            parameter = str(exc.param.name)

            em = Embed(
                description=f"{ERROR} Invalid argument `{parameter}` passed\n"
                            f"{await syntax(ctx.command)}",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.CommandOnCooldown):
            em = Embed(
                description=f"{ERROR} {random.choice(self.cooldown_messages)} "
                            f"Please try again in `{(convert_time(round(exc.retry_after)))}`",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MemberNotFound):
            em = Embed(
                description=f"{ERROR} No such member was found.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.RoleNotFound):
            em = Embed(
                description=f"{ERROR} No such role was found.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.BadUnionArgument):
            parameter = str(exc.param.name)

            em = Embed(
                description=f"{ERROR} Invalid argument `{parameter}` passed\n"
                            f"{await syntax(ctx.command)}",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.ChannelNotFound):
            em = Embed(
                description=f"{ERROR} No such channel was found.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MissingPermissions):
            perms = str(', '.join(exc.missing_perms)).title().replace('_', ' ')
            em = Embed(
                description=f"{ERROR} You do not have the required permissions perform this action.\n"
                            f"```Missing {perms} permissions```",
                colour=RED)

            await ctx.send(embed=em)

        elif isinstance(exc, commands.BotMissingPermissions):
            perms = str(', '.join(exc.missing_perms)).title().replace('_', ' ')
            em = Embed(
                description=f"{ERROR} I do not have permission to perform this action.\n"
                            f"```Missing {perms} permissions```",
                colour=RED)

            await ctx.send(embed=em)

        elif isinstance(exc, commands.BadArgument):
            em = Embed(
                description=f"{ERROR} Invalid argument passed\n"
                            f"{await syntax(ctx.command)}",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.InvalidEndOfQuotedStringError):
            em = Embed(
                description=f"{ERROR} Invalid argument passed\n"
                            f"{await syntax(ctx.command)}",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.NotOwner):
            em = Embed(
                description=f"{ERROR} You are not a developer of this bot.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.CheckFailure):
            em = Embed(
                description=f"{ERROR} You do not have the permissions to perform this action.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.DisabledCommand):
            em = Embed(
                description=f"{ERROR} This command is currently disabled.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.TooManyArguments):
            em = Embed(
                description=f"{ERROR} Too many arguments were passed.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, Blacklisted):
            em = discord.Embed(
                    description=f"{ERROR} You are blacklisted.",
                    colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, NoMoreTracks):
            em = discord.Embed(
                description=f"{ERROR} There are no more tracks in the queue.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, NoPreviousTracks):
            em = discord.Embed(
                description=f"{ERROR} There are no previous tracks in the queue.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, InvalidRepeatMode):
            em = discord.Embed(
                description=f"{ERROR} Invalid repeat mode specified.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, PlayerIsAlreadyPaused):
            em = discord.Embed(
                description=f"{ERROR} Player is already paused.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, PlayerIsAlreadyResumed):
            em = discord.Embed(
                description=f"{ERROR} Player is already playing.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, PlayerIsAlreadyStopped):
            em = discord.Embed(
                description=f"{ERROR} Player is already stopped.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, QueueIsEmpty):
            em = discord.Embed(
                description=f"{ERROR} The queue is empty.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, NoTracksFound):
            em = discord.Embed(
                description=f"{ERROR} No tracks were found.",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, AlreadyConnectedToChannel):
            em = discord.Embed(
                    description=f"{ERROR} Already connected to a channel.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, NotConnectedToChannel):
            em = discord.Embed(
                    description=f"{ERROR} You are not in a voice channel.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, BotNotConnectedToChannel):
            em = discord.Embed(
                    description=f"{ERROR} I am not connected to a voice channel.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, TrackDoesNotExist):
            em = discord.Embed(
                    description=f"{ERROR} Track does not exist.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, RoleNotHighEnough):
            em = discord.Embed(
                    description=f"{ERROR} You are not high enough in the role hierarchy to perform this action.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, BotRoleNotHighEnough):
            em = discord.Embed(
                    description=f"{ERROR} I am not high enough in the role hierarchy to perform this action.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, InvalidLimit):
            em = discord.Embed(
                description=f"{ERROR} The limit provided is not within acceptable boundaries.\n"
                            f"```Limit must be in between 1 and 1000 messages```",
                color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, IsAdministrator):
            em = discord.Embed(
                    description=f"{ERROR} This member has the `administrator` permission.",
                    color=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.NoPrivateMessage):
            em = discord.Embed(
                    description=f"{ERROR} This command cannot be used in private messages.",
                    color=RED)
            await ctx.send(embed=em)

        elif hasattr(exc, "original"):
            em = discord.Embed(
                description=f"{ERROR} Something went wrong. Whoops!"
                            f"```py{exc}```",
                color=RED)
            await ctx.send(embed=em)
            raise exc.original

        else:
            em = discord.Embed(
                description=f"{ERROR} Something went wrong. Whoops!"
                            f"```{exc}```",
                color=RED)
            await ctx.send(embed=em)
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
