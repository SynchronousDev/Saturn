import typing as t

from assets import *
from discord import Embed
from discord.ext import commands
import pytimeparse as pytp
from datetime import timedelta, datetime as dt
from copy import deepcopy

from discord.ext import menus, tasks
from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)


class Utility(commands.Cog):
    """
    The Utility cog. Includes useful things, like starboards and modmail.

    Not to be confused with the Miscellaneous cog.
    """
    def __init__(self, bot):
        self.bot = bot
        self.snipe_task = self.clear_snipe_cache.start()

    def cog_unload(self):
        self.snipe_task.cancel()

    @tasks.loop(seconds=10)
    async def clear_snipe_cache(self):
        current_time = dt.utcnow()
        snipes = deepcopy(self.bot.snipes)

        for key, value in snipes.items():
            clear_time = value['time'] + relativedelta(seconds=600)

            if current_time >= clear_time:
                self.bot.snipes.pop(value['_id'])

    @clear_snipe_cache.before_loop
    async def before_clear_snipe_cache(self):
        await self.bot.wait_until_ready()

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
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def user_info(self, ctx, member: t.Optional[t.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        embed = discord.Embed(colour=member.colour if isinstance(member, discord.Member) else MAIN,
                              timestamp=dt.utcnow())

        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(icon_url=member.avatar_url, name=member.name)

        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
        if isinstance(member, discord.Member):
            embed.add_field(name=f"Joined {ctx.guild}", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
            embed.add_field(
                name="Roles",
                value=str(" ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))),
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(
        name='roles',
        description='View your roles.'
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def view_roles(self, ctx, member: t.Optional[t.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        roles = " ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))
        print(roles)
        em = discord.Embed(
            description=str(roles if roles else f"{member.mention} has no roles!"),
            colour=member.colour,
            timestamp=dt.utcnow()
        )
        em.set_image(url=member.avatar_url)
        em.set_author(icon_url=member.avatar_url, name=member.name)
        await ctx.send(embed=em)

    @commands.command(
        name='avatar',
        aliases=['pfp', 'userpfp', 'av'],
        description="Shows a user's avatar")
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def get_avatar(self, ctx, member: t.Optional[discord.Member]):
        if member is None:
            member = ctx.author

        avatar = discord.Embed(
            color=member.color)
        avatar.set_image(url=member.avatar_url)
        await ctx.send(embed=avatar)

    @commands.command(
        name='snipe',
        aliases=['snp', 'snip'],
        description='Retrieve deleted messages.'
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def get_snipes(self, ctx, member: t.Optional[discord.Member]):
        em = discord.Embed(
            colour=MAIN,
        )
        em.description = f"Couldn't find any deleted messages " \
                         f"{f'from {member.mention}' if member else None}" \
                         f" in the last 10 minutes."

        if self.bot.snipes:
            for key, value in reversed(self.bot.snipes.items()):
                if member:
                    if value['guild'] == ctx.guild.id:
                        if value['author'] == member.id:
                            user = self.bot.get_user(value['author'])
                            em.set_author(name=user,
                                          icon_url=user.avatar_url)
                            em.description = value['content']
                            em.timestamp = value['time']

                else:
                    if value['guild'] == ctx.guild.id:
                        user = self.bot.get_user(value['author'])
                        em.set_author(name=user,
                                      icon_url=user.avatar_url)
                        em.description = value['content']
                        em.timestamp = value['time']
                        break

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Utility(bot))
