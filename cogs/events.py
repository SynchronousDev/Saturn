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
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.CommandNotFound):
            em = Embed(
                description=f"{ERROR} Command `{ctx.invoked_with}` does not exist.",
                colour=RED)
            await ctx.send(embed=em)

        elif isinstance(exc, commands.MissingRequiredArgument):
            try:
                invalid_param, param_type = str(exc.param).split(':')
            except ValueError:
                invalid_param = str(exc.param)
                param_type = None
            em = Embed(
                description=f"{ERROR} Invalid argument `{invalid_param}` passed\n"
                            f"{await syntax(ctx.command, ctx)}",
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

        elif isinstance(exc, commands.MissingPermissions):
            perms = str(', '.join(exc.missing_perms)).title().replace('_', ' ')
            em = Embed(
                description=f"{ERROR} You do not have the required permissions to perform this action.\n"
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