import typing as t
from assets import *
from discord.ext import commands
import discord

class Management(commands.Cog, name='Server Management'):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__) 

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
                    colour=GREEN)
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
                    colour=GREEN)
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
                    colour=GREEN)
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
                    colour=GREEN)
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
        await ctx.invoke(self.bot.get_command('help'), entity='create')

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
            colour=GREEN)
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
            colour=GREEN)
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
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='delete',
        aliases=['del'],
        description='The delete group of commands.',
        invoke_without_command=True)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def delete(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='delete')

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
            colour=GREEN)
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
            colour=GREEN)
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
            colour=GREEN)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Management(bot))