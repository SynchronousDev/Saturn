from datetime import datetime as dt
from datetime import timedelta
import typing as t 

import discord
from utils import *
from discord import Embed
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='ping',
        description='Used to check if the bot is alive')
    async def ping(self, ctx):
        em = Embed(
            colour=MAIN)
        em.set_author(icon_url=self.bot.user.avatar_url,
                      name=f"Pong! {self.bot.latency * 1000:.2f}ms")
        await ctx.send(embed=em)

    @commands.command(
        name='purge',
        aliases=['p', 'prg', 'prune'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    async def purge_cmd(self, ctx, limit: int, members: commands.Greedy[discord.Member]):
        def check(m):
            return not len(members) or m.author in members

        if 0 < limit < 1001:
            await ctx.message.delete()
            deleted = await ctx.channel.purge(
                limit=limit,
                after=dt.utcnow() - timedelta(days=14),
                check=check)

            em = Embed(
                description=f"{CHECK} Deleted {len(deleted,)} messages in {ctx.channel.mention}",
                color=MAIN)
            await ctx.send(embed=em, delete_after=2)

        else:
            em = Embed(
                description=f"{ERROR} The limit provided is not within acceptable bounds.\n"
                            f"```Limit must be in between 1 and 1000 messages```",
                color=RED)
            await ctx.send(embed=em)

    @commands.command(name="userinfo",
                      aliases=["memberinfo", "ui", "mi"],
                      description='Information about a user')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def user_info(self, ctx, member: t.Optional[discord.Member]):
        member = member or ctx.author

        embed = discord.Embed(colour=member.colour,
                              timestamp=dt.utcnow())

        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(icon_url=member.avatar_url, name=member.name)

        fields = [("ID", member.id, False),
                  ("Joined Discord", member.created_at.strftime("%d/%m/%Y"), False),
                  ("Joined {}".format(ctx.guild),
                   member.joined_at.strftime("%d/%m/%Y"), False),
                  ("Top Role", member.top_role.mention, False)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)

    @commands.command(
        name='avatar',
        aliases=['pfp', 'userpfp', 'av'],
        description="Shows a user's avatar")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def avatar(self, ctx, member: t.Optional[discord.Member]):
        if member is None:
            member = ctx.author

        avatar = discord.Embed(
            color=member.color)
        avatar.set_image(url=member.avatar_url)
        await ctx.send(embed=avatar)

    @commands.group(
        name='create',
        aliases=['make', 'new'],
        description='The delete group of commands.',
        invoke_without_command=True)    
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def create(self, ctx):
        em = discord.Embed(
            description=f"{ERROR} Please specify an action to perform.",
            colour=RED)
        await ctx.send(embed=em)

    @create.command(
        name='category',
        aliases=['cgry', 'ctgry'],
        description='Creates a category.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def create_category(self, ctx, *, name):
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)}
        category = await ctx.guild.create_category(name=name, overwrites=overwrites)
        em = discord.Embed(
            description=f"{CHECK} Created category `{category.name}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @create.command(
        name='channel',
        aliases=['chnl'],
        description='Creates a channel.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def create_channel(self, ctx, *, name):
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)}
        channel = await ctx.guild.create_text_channel(name=name, overwrites=overwrites)
        em = discord.Embed(
            description=f"{CHECK} Created channel {channel.mention}",
            colour=MAIN)
        await ctx.send(embed=em)

    @commands.group(
        name='delete',
        aliases=['del', 'remove'],
        description='The delete group of commands.',
        invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def delete(self, ctx):
        em = discord.Embed(
            description=f"{ERROR} Please specify an action to perform.",
            colour=RED)
        await ctx.send(embed=em)

    @delete.command(
        name='category',
        aliases=['cgry'],
        description='Deletes a category.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def del_category(self, ctx, category: discord.CategoryChannel, *, reason=None):
        await category.delete(reason=reason)
        em = discord.Embed(
            description=f"{CHECK} Deleted category `{category.name}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @delete.command(
        name='channel',
        aliases=['chnl'],
        description='Deletes a channel.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def del_channel(self, ctx, channel: discord.TextChannel=None, *, reason=None):
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        em = discord.Embed(
            description=f"{CHECK} Deleted channel `{channel.name}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @commands.command(
        name='lock',
        aliases=['lck', 'lk'],
        description='Locks a channel. Essentially mutes the channel and no one can talk in it.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lock_cmd(self, ctx, channel: discord.TextChannel=None):
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            await channel.edit(overwrites=overwrites)
            em = discord.Embed(
                description=f"{LOCK} {channel.mention} is now locked.",
                colour=RED)
            await ctx.send(embed=em)

        elif channel.overwrites[ctx.guild.default_role].send_messages == True or channel.overwrites[ctx.guild.default_role].send_messages == None:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            em = discord.Embed(
                description=f"{LOCK} {channel.mention} is now locked.",
                colour=RED)
            await ctx.send(embed=em)

        else:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            em = discord.Embed(
                description=f"{UNLOCK} {channel.mention} is now unlocked.",
                colour=MAIN)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Utility(bot))