from discord import Embed
from assets import *
from discord.ext import commands
import traceback
import sys

log = logging.getLogger(__name__) 

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exc):
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(exc, commands.CommandNotFound):
            pass

        elif isinstance(exc, commands.MissingRequiredArgument):
            parameter = str(exc.param.name)

            em = Embed(
                description=f"{ERROR} Invalid argument `{parameter}` passed\n"
                            f"```{await error_arg_syntax(ctx.command, parameter)}```",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.CommandOnCooldown):
            em = Embed(
                description=f"{ERROR} Woah there, too fast! "
                            f"Please try again in `{(convert_time(round(exc.retry_after)))}`",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MemberNotFound):
            em = Embed(
                description=f"{ERROR} No such member was found.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, Blacklisted):
            em = Embed(
                description=f"{ERROR} You are blacklisted from the bot.",
                colour=RED)
            await ctx.author.send(embed=em)

        elif isinstance(exc, commands.RoleNotFound):
            em = Embed(
                description=f"{ERROR} No such role was found.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, discord.HTTPException):
            em = Embed(
                description=f"{ERROR} Whoops, looks like that didn't go as planned. Try again later?",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.BadUnionArgument):
            parameter = str(exc.param.name)

            em = Embed(
                description=f"{ERROR} Invalid argument `{parameter}` passed\n"
                            f"```{await error_arg_syntax(ctx.command, parameter)}```",
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
                description=f"{ERROR} You do not have  the proper permissions perform this action.\n"
                            f"```Missing {perms} permissions```",
                colour=RED)

            await ctx.send(embed=em)

        elif isinstance(exc, commands.BotMissingPermissions):
            perms = str(', '.join(exc.missing_perms)).title().replace('_', ' ')
            em = Embed(
                description=f"{ERROR} I do not have the proper permissions to perform this action.\n"
                            f"```Missing {perms} permissions```",
                colour=RED)

            await ctx.send(embed=em)

        elif isinstance(exc, commands.BadArgument):
            em = Embed(
                description=f"{ERROR} Invalid argument passed\n"
                            f"```{await syntax(ctx.command)}```",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.InvalidEndOfQuotedStringError):
            em = Embed(
                description=f"{ERROR} Invalid argument passed\n"
                            f"```{await syntax(ctx.command)}```",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.NotOwner):
            em = Embed(
                description=f"{ERROR} You are not a developer of this bot.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.CheckFailure):
            em = Embed(
                description=f"{ERROR} You do not have the proper permissions to perform this action.",
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
                            f"```{exc}```",
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
            log.warning("Something went wrong.")


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
