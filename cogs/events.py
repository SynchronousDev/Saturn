from discord import Embed
from assets import *
from discord.ext import commands
import traceback
import sys

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__) 

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        try:
            if self.bot.muted_users[member.id]:
                data = await self.bot.config.find_by_id(guild.id)
                mute_role = guild.get_role(data['mute_role_id'])
                if mute_role:
                    await member.add_roles(mute_role, reason='Attempted mute bypass', atomic=True)

        except KeyError:
            pass

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
            invalid_param = str(exc.param)
            try:
                parameter, param_type = invalid_param.split(':')

            except ValueError:
                parameter = invalid_param

            em = Embed(
                description=f"{ERROR} Invalid argument `{parameter}` passed\n"
                            f"{await syntax(ctx.command)}",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.CommandOnCooldown):
            em = Embed(
                description=f"{ERROR} This command is on cooldown. "
                            f"Please try again in {(convert_time(round(exc.retry_after)))}",
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
            invalid_param = str(exc.param)
            try:
                parameter, param_type = invalid_param.split(':')

            except ValueError:
                parameter = invalid_param

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
                description=f"{ERROR} You do not have the required permissions to perform this action.\n"
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

        elif isinstance(exc, commands.NotOwner):
            em = Embed(
                description=f"{ERROR} You are not a developer of this bot.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.DisabledCommand):
            em = Embed(
                description=f"{ERROR} This command is currently disabled.",
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

        elif isinstance(exc, NoVoiceChannel):
            em = discord.Embed(
                    description=f"{ERROR} You are not in a voice channel.",
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

        elif hasattr(exc, "original"):
            raise exc.original

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
            


def setup(bot):
    bot.add_cog(Events(bot))
