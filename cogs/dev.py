import asyncio
import json
import os
import typing as t
from datetime import datetime as dt

import discord
from discord.ext import commands
from utils import *


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @commands.command(
        name='blacklist',
        aliases=['bl'],
        description='A developer command. Blacklists a user from using the bot.')
    @commands.is_owner()
    async def blacklist_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str]='no reason provided'):
        await self.bot.blacklists.upsert({"_id": member.id, "reason": reason})

        em = discord.Embed(
                description=f"{CHECK} Blacklisted {member.mention} for **{reason}**.",
                colour=GREEN,
                timestamp=dt.now())
        await ctx.send(embed=em)


    @commands.command(
        name='unblacklist',
        aliases=['ubl'],
        description='A developer command. Unblacklists a user from using the bot.')
    @commands.is_owner()
    async def unblacklist_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str]='no reason provided'):
        try:
            await self.bot.blacklists.delete_by_id(member.id)

        except commands.MemberNotFound:
            em = discord.Embed(
                description=f"{ERROR} {member.mention} is not blacklisted from this bot.",
                colour=RED)
            await ctx.send(embed=em)

        em = discord.Embed(
                description=f"{CHECK} Unblacklisted {member.mention} for **{reason}**.",
                colour=GREEN,
                timestamp=dt.now())
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Dev(bot))
