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
        latency = float(f"{self.bot.latency * 1000:.2f}")
        if latency < 60:
            strength = STRONG_SIGNAL

        elif latency < 101:
            strength = MEDIUM_SIGNAL

        else:
            strength = WEAK_SIGNAL

        em = Embed(
            description=f"{strength} Pong! `{latency}ms`",
            colour=MAIN)
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

    @commands.command(
        name='addrole',
        aliases=['addr', 'ar', 'arole'],
        description="Adds a role to you or a specified member.")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def add_roles(self, ctx, role: discord.Role, member: t.Optional[discord.Member], reason: t.Optional[str]='no reason provided'):
        member = member or ctx.author

        if ctx.guild.me.top_role > member.top_role and (member != ctx.author) and (role.position < ctx.guild.me.top_role.position):
            if ctx.author.top_role > member.top_role and member != ctx.author:
                await member.add_roles(role, reason=reason, atomic=True)
                em = discord.Embed(
                    description=f"{CHECK} Added {role.mention} to {member.mention}",
                    colour=MAIN)
                await ctx.send(embed=em)

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
        name='massaddrole',
        aliases=['maddr', 'mar', 'marole'],
        description="Adds a role to you or a specified member.")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mass_add_roles(self, ctx, role: discord.Role, has_role: discord.Role, reason: t.Optional[str]='no reason provided'):
        em = discord.Embed(
            description=f"{LOADING} This might take a while, please wait...",
            colour=MAIN)
        msg = await ctx.send(embed=em)
        added_roles = []
        for member in ctx.guild.members:
            if has_role in member.roles:
                await member.add_roles(role, reason=reason, atomic=True)
                added_roles.append(member)

            else:
                continue 

        else:
            await msg.delete()
            em = discord.Embed(
                    description=f"{CHECK} Added {role.mention} to `{len(added_roles)}` members.",
                    colour=MAIN)
            await ctx.send(embed=em)

    @commands.command(
        name='massremoverole',
        aliases=['mrmvr', 'mremover', 'mrrole'],
        description="Removes a role from you or a specified member.")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mass_remove_roles(self, ctx, role: discord.Role, has_role: discord.Role, reason: t.Optional[str]='no reason provided'):
        em = discord.Embed(
            description=f"{LOADING} This might take a while, please wait...",
            colour=MAIN)
        msg = await ctx.send(embed=em)
        removed_roles = []
        for member in ctx.guild.members:
            if has_role in member.roles:
                await member.remove_roles(role, reason=reason, atomic=True)
                removed_roles.append(member)

            else:
                continue 

        else:
            await msg.delete()
            em = discord.Embed(
                    description=f"{CHECK} Removed {role.mention} from `{len(removed_roles)}` members.",
                    colour=MAIN)
            await ctx.send(embed=em)


    @commands.command(
        name='removerole',
        aliases=['rmvr', 'remover', 'rrole'],
        description="Removes a role from you or a specified member.")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def remove_roles(self, ctx, role: discord.Role, member: t.Optional[discord.Member], reason: t.Optional[str]='no reason provided'):
        member = member or ctx.author

        if ctx.guild.me.top_role > member.top_role and (member != ctx.author) and (role.position < ctx.guild.me.top_role.position):
            if ctx.author.top_role > member.top_role and member != ctx.author:
                await member.remove_roles(role, reason=reason, atomic=True)
                em = discord.Embed(
                    description=f"{CHECK} Added {role.mention} to {member.mention}",
                    colour=MAIN)
                await ctx.send(embed=em)

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

    @create.command(
        name='role',
        aliases=['r', 'rle', 'ro'],
        description='Creates a role. Colour is applied via a Hex Code (#FF000)')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def create_role(self, ctx, name, colour: t.Optional[commands.ColourConverter], *, reason: t.Optional[str]='no reason provided'):
        new_role = await ctx.guild.create_role(name=name, colour=colour if colour else discord.Color.default(), reason=reason)
        em = discord.Embed(
            description=f"{CHECK} Created role {new_role.mention}",
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
    async def del_channel(self, ctx, channel: t.Optional[discord.TextChannel], *, reason=None):
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        em = discord.Embed(
            description=f"{CHECK} Deleted channel `{channel.name}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @delete.command(
        name='role',
        aliases=['r', 'rle', 'ro'],
        description='Deletes a role.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def del_channel(self, ctx, role: t.Optional[discord.Role], *, reason=None):
        await role.delete(reason=reason)
        em = discord.Embed(
            description=f"{CHECK} Deleted role `{role.name}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @commands.command(
        name='lock',
        aliases=['lck', 'lk'],
        description='Locks a channel. Essentially mutes the channel and no one can talk in it. Run the command again to unlock the channel.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lock_cmd(self, ctx, channel: t.Optional[discord.TextChannel]):
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

    @commands.command(
        name='slowmode',
        aliases=['slm', 'sl'],
        description='Changes the slowmode delay on a given channel. Must be equal or less than 6 hours. Requires Manage Channels permission.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def slowmode_cmd(self, ctx, channel: t.Optional[discord.TextChannel], time: TimeConverter):
        channel = channel or ctx.channel
        if time > 21600 or time < 1:
            em = discord.Embed(
                description=f"{ERROR} Slowmode time should be equal or less than 6 hours.",
                colour=RED)
            await ctx.send(embed=em)
            return 

        await channel.edit(slowmode_delay=time, reason='Slowmode delay edited by {ctx.author} via slowmode command')
        em = discord.Embed(
                description=f":clock1: Slowmode delay for {channel.mention} was set to {str(convert_time(time))}",
                colour=MAIN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Utility(bot))