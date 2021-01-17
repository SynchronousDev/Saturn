import asyncio
from datetime import datetime as dt
import typing as t

import discord
from discord.ext import commands
from utils import *


class Mod(commands.Cog, name='Moderation'):
    def __init__(self, bot):
        self.bot = bot 

    # some of this code is snipped from the original Selenium, but this is a rewritten version

    @commands.command(
        name='kick',
        aliases=['k'],
        description='Kicks members from the server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Kicked {member.mention} for **{reason}**.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                await send_punishment(member, ctx.guild, 'kick', ctx.author, reason)
                await member.kick(reason=reason)

            else:
                em = discord.Embed(
                    description=f"{ERROR} You are not high enough in the role"
                                f" hierarchy to perform this action.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        else:
            em = discord.Embed(
                description=f"{ERROR} I am not high enough in the member"
                            f" hierarchy to perform this action.",
                colour=RED)
            await ctx.send(embed=em)
            return

    @commands.command(
        name='ban',
        aliases=['b'],
        description='Bans members from the server.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: discord.Member, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Banned {member.mention} for **{reason}**.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                await send_punishment(member, ctx.guild, 'ban', ctx.author, reason)
                await member.ban(reason=reason)
            else:
                em = discord.Embed(
                    description=f"{ERROR} You are not high enough in the role"
                                f" hierarchy to perform this action.",
                    colour=RED)
                await ctx.send(embed=em)

                return

        else:
            em = discord.Embed(
                description=f"{ERROR} I am not high enough in the member"
                            f" hierarchy to perform this action.",
                colour=RED)
            await ctx.send(embed=em)
            return

    @commands.command(
        name='warn',
        aliases=['w', 'wrn'],
        description='Warns members in the server.')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str]="no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Warned {member.mention} for **{reason}**.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                try:
                    await send_punishment(member, ctx.guild, 'warn', ctx.author, reason)

                except discord.Forbidden:
                    pass

            else:
                em = discord.Embed(
                    description=f"{ERROR} You are not high enough in the role"
                                f" hierarchy to perform this action.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        else:
            em = discord.Embed(
                description=f"{ERROR} I am not high enough in the member"
                            f" hierarchy to perform this action.",
                colour=RED)
            await ctx.send(embed=em)
            return

def setup(bot):
    bot.add_cog(Mod(bot))