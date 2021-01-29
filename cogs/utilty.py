import typing as t

from assets import *
from discord import Embed
from discord.ext import commands
import pytimeparse as pytp


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
                description=f"{CHECK} Deleted {len(deleted, )} messages in {ctx.channel.mention}",
                color=GREEN)
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
        name='lock',
        aliases=['lck', 'lk'],
        description='Locks a channel. Essentially mutes the channel and no one can talk in it. '
                    'Run the command again to unlock the channel.')
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

        elif channel.overwrites[ctx.guild.default_role].send_messages or channel.overwrites[
             ctx.guild.default_role].send_messages is None:
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
                colour=GREEN)
            await ctx.send(embed=em)

    @commands.command(
        name='slowmode',
        aliases=['slm', 'sl'],
        description='Changes the slowmode delay on a given channel. '
                    'Must be equal or less than 6 hours. Requires Manage Channels permission.')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def slowmode_cmd(self, ctx, channel: t.Optional[discord.TextChannel], time: pytp.parse):
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
            colour=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Utility(bot))
