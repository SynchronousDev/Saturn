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
                colour=MAIN)
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
                colour=MAIN)
        await ctx.send(embed=em)

    @commands.group(
        name='muterole',
        aliases=['mr'],
        description='The command to change the settings for the '
                    'muted role that the bot assigns to members upon a mute.',
        invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='muterole')

    @mute_role.command(
        name='set',
        aliases=['assign'],
        description='Sets the mute role to a role.')
    async def mute_role_set(self, ctx, role: discord.Role):
        await self.bot.config.upsert({"_id": ctx.guild.id, "mute_role_id": role.id})
        em = discord.Embed(
            description=f"{CHECK} The mute role has been assigned to {role.mention}",
            colour=MAIN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='delete',
        aliases=['del', 'd'],
        description='Deletes the mute role.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_del(self, ctx):
        data = await self.bot.config.find_by_id(ctx.guild.id)
        mute_role = ctx.guild.get_role(data['mute_role_id'])
        if not mute_role:
            em = discord.Embed(
                description=f"{ERROR} The mute role does not exist! Run `muterole <role>` or `muterole create`",
                colour=RED)
            await ctx.send(embed=em)
            return

        try:
            await mute_role.delete(reason=f'Mute role deleted by {ctx.author.name} (ID {ctx.author.id})')

        except discord.Forbidden:
            em = discord.Embed(
                description=f"{ERROR} Sorry, I couldn't execute that action.\n"
                            f"```Missing permissions```",
                colour=RED)
            await ctx.send(embed=em)
            return

        except discord.HTTPException:
            em = discord.Embed(
                description=f"{ERROR} Whoops! Something went wrong while executing that action.",
                colour=RED)
            await ctx.send(embed=em)
            return

        em = discord.Embed(
                description=f"{CHECK} The mute role has been deleted.",
                colour=MAIN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='create',
        aliases=['make', 'new'],
        description='Creates the mute role.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_create(self, ctx):
        data = await self.bot.config.find_by_id(ctx.guild.id)
        mute_role = ctx.guild.get_role(data['mute_role_id'])
        if not mute_role:
            em = discord.Embed(
                description=f"{ERROR} The mute role already exists! Run `muterole <role>` or `muterole delete`",
                colour=RED)
            await ctx.send(embed=em)
            return

        perms = discord.Permissions(
                send_messages=False, read_messages=True)
        mute_role = await ctx.guild.create_role(name='Muted', colour=RED, permissions=perms, reason='Could not find a muted role')

        await self.bot.config.upsert({"_id": ctx.guild.id, "mute_role_id": mute_role.id})

        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(mute_role, read_messages=True, send_messages=False)

            except discord.Forbidden:
                continue

            except discord.HTTPException:
                continue

        em = discord.Embed(
                description=f"{CHECK} The mute role was created.",
                colour=MAIN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Config(bot))
