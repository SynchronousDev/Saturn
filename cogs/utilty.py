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
        current_time = utc()
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
    async def user_info(self, ctx, member: typing.Optional[typing.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        embed = discord.Embed(colour=member.colour if isinstance(member, discord.Member) else MAIN,
                              timestamp=utc())

        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(icon_url=member.avatar_url, name=member.name)

        join_delta = (utc() - member.joined_at.replace(tzinfo=datetime.timezone.utc)).total_seconds()
        created_delta = (utc() - member.created_at.replace(
            tzinfo=datetime.timezone.utc)).total_seconds()

        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined Discord", value=general_convert_time(created_delta) + ' ago')
        if isinstance(member, discord.Member):
            roles = " ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))

            embed.add_field(name=f"Joined {ctx.guild}", value=general_convert_time(join_delta) + ' ago')
            if roles:
                embed.add_field(
                    name="Roles",
                    value=roles,

                )

        await ctx.send(embed=embed)

    # TODO: add reminder command yay
    # TODO: add source command (github repo and stuff)

    @commands.command(
        name='roles',
        description='View your roles.'
    )
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def view_roles(self, ctx, member: typing.Optional[typing.Union[discord.Member, discord.User]]):
        member = member or ctx.author

        roles = " ".join(reversed([f"<@&{r.id}>" for r in member.roles[1:]]))
        em = discord.Embed(
            description=str(roles if roles else f"{member.mention} has no roles!"),
            colour=member.colour,
            timestamp=utc()
        )
        em.set_image(url=member.avatar_url)
        em.set_author(icon_url=member.avatar_url, name=f"{member.name}'s roles")
        await ctx.send(embed=em)

    @commands.command(
        name='export',
        aliases=['channelcontents', 'export-contents', 'exportcontents', 'downloadchannelcontents', 'dcc'],
        description="Export a channel's content into a .txt file."
    )
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def export_channel_contents(self, ctx, channel: typing.Optional[discord.TextChannel],
                                      limit: typing.Optional[int] = 100):
        channel = channel or ctx.channel

        em = discord.Embed(
            description=f"{INFO} This might take a while, please wait...",
            colour=BLUE)
        msg = await ctx.send(embed=em)
        async with channel.typing():
            messages = await channel.history(limit=limit, oldest_first=True).flatten()
            with open(f'{self.bot.path}/assets/channel_exports/{channel.id}-export.txt', 'w', encoding='utf-8') as f:
                f.write(f"{len(messages)} messages exported from the #{channel} channel by {ctx.author}:\n\n")
                for message in messages:
                    content = message.clean_content
                    if not message.author.bot:
                        f.write(f"{message.author} {convert_to_timestamp(message.created_at)} EST"
                                f" (ID - {message.author.id})\n"
                                f"{content} (Message ID - {message.id})\n\n")
    
                    else:
                        f.write(f"{message.author} {convert_to_timestamp(message.created_at)} EST"
                                f" (ID - {message.author.id})\n"
                                f"{'Embed/file sent by a bot' if not content else content}\n\n")
    
            file = discord.File(f'{self.bot.path}/assets/channel_exports/{channel.id}-export.txt')

        await msg.delete()
        em = discord.Embed(
            title='Channel Export',
            description=f"Message contents of <#{channel.id}>\n"
                        f"Download the attached .txt file to view the contents.",
            colour=MAIN,
            timestamp=utc()
        )
        em.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/"
                             "thumbs/120/mozilla/36/memo_1f4dd.png")
        await ctx.send(embed=em)
        await asyncio.sleep(0.5)
        await ctx.send(file=file)

    @commands.command(
        name='avatar',
        aliases=['pfp', 'userpfp', 'av'],
        description="Shows a user's avatar")
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def get_avatar(self, ctx, member: typing.Optional[discord.Member]):
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
    async def get_snipes(self, ctx, member: typing.Optional[discord.Member],
                         channel: typing.Optional[discord.TextChannel]):
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
    async def get_editsnipes(self, ctx, member: typing.Optional[discord.Member],
                             channel: typing.Optional[discord.TextChannel]):
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