from copy import deepcopy
from time import time

from dateutil.relativedelta import relativedelta
from discord.ext import tasks

from assets import *

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Utility(commands.Cog):
    """
    The Utility module. Includes useful things, like starboards and modmail.

    Not to be confused with the Fun module.
    """

    def __init__(self, bot):
        self.bot = bot
        self.snipe_task = self.clear_snipe_cache.start()

    def cog_unload(self):
        self.snipe_task.cancel()

    @tasks.loop(seconds=10)
    async def clear_snipe_cache(self):
        current_time = datetime.datetime.now(datetime.timezone.utc)
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
            colour = GREEN

        elif latency < 101:
            colour = GOLD

        else:
            colour = RED

        start = time()
        msg = await ctx.send("Pinging...")
        end = time()
        em = discord.Embed(
            description=f"Pong!\n**Bot -** `{latency}ms`\n"
                        f"**API -** `{(end - start) * 1000:,.2f}ms`\n",
            colour=colour)
        await msg.edit(content=None, embed=em)

    # noinspection SpellCheckingInspection
    @commands.command(
        name="version",
        aliases=['vers'])
    async def _vers(self, ctx):
        await ctx.reply(f"{self.bot.__name__} is currently running on version **{self.bot.__version__}**")

    @commands.command(
        name="membercount",
        aliases=['members', 'numberofmembers'])
    async def member_count(self, ctx):
        bots = len([m for m in ctx.guild.members if m.bot])
        users = len(ctx.guild.members) - bots
        await ctx.reply(f"**{ctx.guild}** has **{bots + users}** members. (**{bots}** bots and **{users}** users)")

    @commands.command(name="userinfo",
                      aliases=["memberinfo", "ui", "mi"],
                      description='Information about a user')
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def user_info(self, ctx, member: t.Optional[t.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        embed = discord.Embed(colour=member.colour if isinstance(member, discord.Member) else MAIN,
                              timestamp=datetime.datetime.now(datetime.timezone.utc))

        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(icon_url=member.avatar_url, name=member.name)

        join_delta = (datetime.datetime.now(datetime.timezone.utc) - member.joined_at.replace(tzinfo=datetime.timezone.utc)).total_seconds()
        created_delta = (datetime.datetime.now(datetime.timezone.utc) - member.created_at.replace(
            tzinfo=datetime.timezone.utc)).total_seconds()

        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined Discord", value=general_convert_time(created_delta) + ' ago', inline=False)
        if isinstance(member, discord.Member):
            roles = " ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))

            embed.add_field(name=f"Joined {ctx.guild}", value=general_convert_time(join_delta) + ' ago', inline=False)
            if roles:
                embed.add_field(
                    name="Roles",
                    value=roles,
                    inline=False
                )

        await ctx.send(embed=embed)

    # TODO: add command to export channel contents as a file

    @commands.command(
        name='roles',
        description='View your roles.'
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def view_roles(self, ctx, member: t.Optional[t.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        roles = " ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))
        em = discord.Embed(
            description=str(roles if roles else f"{member.mention} has no roles!"),
            colour=member.colour,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        em.set_image(url=member.avatar_url)
        em.set_author(icon_url=member.avatar_url, name=f"{member.name}'s roles")
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
    async def get_snipes(self, ctx, member: t.Optional[discord.Member], channel: t.Optional[discord.TextChannel]):
        em = discord.Embed(
            colour=BLUE,
        )
        em.description = f"{INFO} Couldn't find any deleted messages " \
                         f"{f'from {member.mention}' if member else ''}" \
                         f" in the last 10 minutes."

        if self.bot.snipes:
            for key, value in reversed(self.bot.snipes.items()):
                if value['guild'] == ctx.guild.id:
                    if channel:
                        if value['channel'] == channel.id:
                            pass

                        else:
                            continue

                    if member:
                        if value['author'] == member.id:
                            pass

                        else:
                            continue

                    user = self.bot.get_user(value['author'])
                    em.set_author(name=user,
                                  icon_url=user.avatar_url)
                    em.description = value['content']
                    em.timestamp = value['time']
                    em.colour = ctx.author.colour
                    break

        await ctx.send(embed=em)

    @commands.command(
        name='editsnipe',
        aliases=['esnp', 'esnip'],
        description='Retrieve edited messages.'
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def get_editsnipes(self, ctx, member: t.Optional[discord.Member], channel: t.Optional[discord.TextChannel]):
        em = discord.Embed(
            colour=BLUE,
        )
        em.description = f"{INFO} Couldn't find any edited messages " \
                         f"{f'from {member.mention}' if member else ''}" \
                         f" in the last 10 minutes."

        if self.bot.edit_snipes:
            for key, value in reversed(self.bot.edit_snipes.items()):
                if value['guild'] == ctx.guild.id:
                    if channel:
                        if value['channel'] == channel.id:
                            pass

                        else:
                            continue
                        
                    if member:
                        if value['author'] == member.id:
                            pass

                        else:
                            continue

                    user = self.bot.get_user(value['author'])
                    em.set_author(name=user,
                                  icon_url=user.avatar_url)
                    em.description = f"**Before** - {value['before']}\n" \
                                     f"**After** - {value['after']}"
                    em.timestamp = value['time']
                    em.colour = ctx.author.colour
                    break

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Utility(bot))
