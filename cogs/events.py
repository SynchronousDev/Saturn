import asyncio
import os
import typing as t
from datetime import datetime as dt

from discord import Embed
import discord
from discord.ext import commands
from utils import *


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        if isinstance(exc, commands.CommandNotFound):
            em = Embed(
                description=f"{ERROR} Command `{ctx.invoked_with}` does not exist.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MissingRequiredArgument):
            invalid_param = str(exc.param)
            em = Embed(
                description=f"{ERROR} Invalid argument `{invalid_param}` passed\n"
                            f"{await syntax(ctx.command, ctx, self.bot)}",
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

        elif isinstance(exc, commands.NotOwner):
            em = Embed(
                description=f"{ERROR} You are not a developer of this bot.",
                colour=RED)

            await ctx.send(embed=em)

        else:
            em = discord.Embed(
                description=f"{ERROR} Whoops! Something went wrong. We'll look into it.",
                color=RED)
            await ctx.send(embed=em)
            raise exc


def setup(bot):
    bot.add_cog(Events(bot))
