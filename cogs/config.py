import asyncio
import json
import os
import typing as t
from datetime import datetime as dt

import discord
from discord.ext import commands
from utils import *


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @commands.command(
        name="prefix",
        aliases=["changeprefix", "setprefix", 'pre'],
        description="Change your guild's prefix.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx, *, prefix="sl!"):
        await self.bot.config.upsert({"_id": ctx.guild.id, "prefix": prefix})
        em = discord.Embed(
                description=f"{CHECK} Prefix has been set to `{prefix}`",
                colour=GREEN,
                timestamp=dt.now())
        await ctx.send(embed=em)


    @commands.command(
        name='deleteprefix',
        aliases=['dp', 'delpre'],
        description="Delete your guild's prefix.")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def deleteprefix(self, ctx):
        await self.bot.config.unset({"_id": ctx.guild.id, "prefix": 1})
        em = discord.Embed(
                description=f"{CHECK} Prefix has been reset to the default `sl!`",
                colour=GREEN,
                timestamp=dt.now())
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Config(bot))
