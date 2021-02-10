import typing as t

from assets import *
from discord import Embed
from discord.ext import commands
import pytimeparse as pytp
from datetime import timedelta

from discord.ext import menus

log = logging.getLogger(__name__)


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
            colour = GREEN

        elif latency < 101:
            strength = MEDIUM_SIGNAL
            colour = GOLD

        else:
            strength = WEAK_SIGNAL
            colour = RED

        em = Embed(
            description=f"{strength} Pong! `{latency}ms`",
            colour=colour)
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


def setup(bot):
    bot.add_cog(Utility(bot))
