import os
import typing as t
from copy import deepcopy
from datetime import timedelta
from glob import glob

import pytimeparse as pytp
from dateutil.relativedelta import relativedelta
from discord.ext import tasks

from assets import *

import re


# noinspection PyUnusedLocal, SpellCheckingInspection
async def purge_msgs(bot, ctx, limit, check):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(
        limit=limit,
        after=dt.utcnow() - timedelta(weeks=2),
        check=check)

    if not len(deleted):
        em = discord.Embed(
            description=f"{ERROR} Could not find any messages to delete.\n"
                        f"```Messages older than 2 weeks cannot be deleted```",
            color=RED)
        return await ctx.send(embed=em)

    deleted = list(reversed(deleted))

    em = discord.Embed(
        description=f"{CHECK} Deleted {len(deleted)} messages in {ctx.channel.mention}",
        color=GREEN)
    await ctx.send(embed=em, delete_after=2)
    data = await bot.config.find_one({"_id": ctx.guild.id})
    try:
        mod_logs = ctx.guild.get_channel(data['mod_logs'])
        if not mod_logs:
            return

    except KeyError or TypeError:
        return

    try:
        await create_purge_file(bot, ctx, deleted)

    except FileNotFoundError:
        await asyncio.sleep(0.5)
        await create_purge_file(bot, ctx, deleted)

    try:
        file = discord.File(f'{bot.path}/assets/purge-txts/purge-{deleted[0].id}.txt')

    except FileNotFoundError:
        await create_purge_file(bot, ctx, deleted)
        file = discord.File(f'{bot.path}/assets/purge-txts/purge-{deleted[0].id}.txt')

    em = discord.Embed(
        title='Messages Purged',
        description=f'Deleted {len(deleted)} messages in {ctx.channel.mention}\n'
                    f'Command invoked by {ctx.author.mention}',
        colour=discord.Colour.orange(),
        timestamp=dt.utcnow()
    )
    em.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/"
                         "thumbs/120/mozilla/36/memo_1f4dd.png")
    em.set_footer(text="Download the .txt file below to view deleted messages")
    await mod_logs.send(embed=em)
    await asyncio.sleep(0.5)
    await mod_logs.send(file=file)


async def create_purge_file(bot, ctx, deleted):
    with open(f'{bot.path}/assets/purge-txts/purge-{deleted[0].id}.txt', 'w+', encoding='utf-8') as f:
        f.write(f"{len(deleted)} messages deleted in the #{ctx.channel} channel by {ctx.author}:\n\n")
        for message in deleted:
            content = message.clean_content
            if not message.author.bot:
                f.write(f"{message.author} at {str(message.created_at)[:-7]} UTC"
                        f" (ID - {message.author.id})\n"
                        f"{content} (Message ID - {message.id})\n\n")

            else:
                f.write(f"{u'{}'.format(str(message.author))} at {str(message.created_at)[:-7]} UTC"
                        f" (ID - {message.author.id})\n"
                        f"{'Embed/file sent by a bot' if not content else content}\n\n")


async def create_mute_role(bot, ctx):
    """Create the mute role for a guild"""
    perms = discord.Permissions(
        send_messages=False, read_messages=True)
    mute_role = await ctx.guild.create_role(
        name='Muted', permissions=perms,
        reason='Could not find a muted role in the process of muting or unmuting.')

    await bot.config.update_one({"_id": ctx.guild.id},
                                {'$set': {"mute_role": mute_role.id}}, upsert=True)

    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(mute_role, read_messages=True, send_messages=False)

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

    return mute_role

async def kick_members(bot, ctx, member, reason):
    """
    Kick members
    """
    await create_log(bot, member, ctx.guild, 'kick', ctx.author if ctx.author != member else ctx.guild.me, reason)
    await member.kick(reason=f"{ctx.author if ctx.author != member else ctx.guild.me} - " + reason)

async def ban_members(bot, ctx, member, reason, time=None, delete_days=None, _type='ban'):
    """
    Ban members
    """
    if time:
        schema = {
            '_id': member.id,
            'at': dt.utcnow(),
            'duration': time or None,
            'moderator': ctx.author.id,
            'guild_id': ctx.guild.id,
            'type': 'ban'
        }
        await bot.bans.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
        bot.banned_users[member.id] = schema

    await create_log(bot, member, ctx.guild, _type, ctx.author if ctx.author != member else ctx.guild.me, reason)
    await ctx.guild.ban(member, reason=f"{ctx.author if ctx.author != member else ctx.guild.me} - "
                                       + reason, delete_message_days=delete_days)
    if _type == 'softban':
        await asyncio.sleep(0.5)
        await ctx.guild.unban(member, reason=f"{ctx.author} - softban")

async def unban_members(bot, ctx, member, reason):
    """
    Unban members
    """
    if isinstance(member, discord.User):
        try:
            await ctx.guild.unban(member, reason=f"{ctx.author} - " + reason)

        except Exception:
            raise commands.MemberNotFound(member)

    elif isinstance(member, int):
        user = await bot.fetch_user(member)
        if not user:
            raise commands.MemberNotFound(member)

        try:
            await ctx.guild.unban(user, reason=f"{ctx.author if ctx.author != member else ctx.guild.me} - " + reason)

        except Exception:
            raise commands.MemberNotFound(member)

    user = bot.get_user(member) or member

    try:
        bot.banned_users.pop(user.id)

    except KeyError:
        pass

    await create_log(bot, member, ctx.guild, "unban", ctx.author if ctx.author != member else ctx.guild.me, reason)


async def mute_members(bot, ctx, member: discord.Member, reason, mute_role, time=None):
    """
    Mute members
    """
    schema = {
        '_id': member.id,
        'at': dt.utcnow(),
        'duration': time or None,
        'moderator': ctx.author.id,
        'guild_id': ctx.guild.id,
        'type': 'mute'
    }

    await member.add_roles(mute_role,
                           reason=f"{ctx.author if ctx.author != member else 'automod'} - "
                                  + f'Mute lasting {convert_time(time)}, for {reason}.')

    await bot.mutes.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
    bot.muted_users[member.id] = schema
    await create_log(
        bot, member, ctx.guild, 'mute', ctx.author if
        ctx.author != member else ctx.guild.me, reason, convert_time(time))


async def unmute_members(bot, ctx, member: discord.Member, reason, mute_role):
    """
    Unmute members
    """
    try:
        await bot.mutes.delete_one({"_id": member.id})
        bot.muted_users.pop(member.id)

    except commands.MemberNotFound or KeyError:
        pass

    await member.remove_roles(mute_role,
                              reason=f"{ctx.author if ctx.author != member else 'automod'} - {reason}")
    try:
        await create_log(bot, member, ctx.guild, 'unmute', ctx.author, reason)

    except discord.Forbidden:
        pass

async def warn_members(bot, ctx, member, reason):
    """
    Warn members
    """
    try:
        await create_log(bot, member, ctx.guild, 'warn', ctx.author if ctx.author != member else 'automod', reason)

    except discord.Forbidden:
        pass

# kinda useful for the moderation stuff
# I have another check in the mute command but whatever lol
async def mod_check(ctx, member):
    if ctx.author is ctx.guild.owner:
        return True

    else:
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if member is not ctx.guild.owner:
                    return True

                else:
                    raise RoleNotHighEnough

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

# noinspection SpellCheckingInspection
class Mod(commands.Cog, name='Moderation'):
    """
    The Moderation module. Includes all commands related to moderation.

    This includes commands related to kicking, banning, muting, fetching punishments, etc...
    """

    def __init__(self, bot):
        self.bot = bot
        self.purge_task = self.purge_files.start()
        self.mod_task = self.update_modlogs.start()
        self.check_mods = self.check_mods.start()

    def cog_unload(self):
        self.mod_task.cancel()
        self.purge_task.cancel()

    @tasks.loop(minutes=1)
    async def update_modlogs(self):
        for guild in self.bot.guilds:
            await update_log_caseids(self.bot, guild)

    @tasks.loop(seconds=30)
    async def purge_files(self):
        for file in glob(self.bot.path + '/purge_txts/*.txt'):
            os.unlink(file)

    @tasks.loop(seconds=1)
    async def check_mods(self):
        current_time = dt.utcnow()
        mutes = deepcopy(self.bot.muted_users)
        bans = deepcopy(self.bot.banned_users)

        # mutes stuff
        for key, value in mutes.items():
            guild = self.bot.get_guild(value['guild_id'])

            member = guild.get_member(value['_id']) or await self.bot.fetch_user(value['_id'])

            data = await self.bot.config.find_one({"_id": guild.id})
            mute_role = guild.get_role(data['mute_role'])

            try:
                join_delta = dt.utcnow() - member.joined_at

            except AttributeError:
                continue

            if mute_role not in member.roles and join_delta > timedelta(seconds=3):
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except commands.MemberNotFound or KeyError:
                    pass

                continue

            if value['duration'] is None:
                continue

            unmute_time = value['at'] + relativedelta(seconds=value['duration'])

            if current_time >= unmute_time:
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except commands.MemberNotFound or KeyError:
                    pass
                
                if isinstance(member, discord.Member):
                    if mute_role in member.roles:
                        await member.remove_roles(mute_role, reason='Mute time expired')

            else:
                if member in guild.members:
                    try:
                        if self.bot.muted_users[member.id] and (mute_role not in member.roles):
                            await member.remove_roles(mute_role, reason='Mute time expired', atomic=True)

                            try:
                                await self.bot.mutes.delete_one({"_id": member.id})
                                self.bot.muted_users.pop(member.id)

                            except commands.MemberNotFound or KeyError:
                                pass

                    except KeyError:
                        pass

        for key, value in bans.items():
            if value['duration'] is None:
                continue

            unban_time = value['at'] + relativedelta(seconds=value['duration'])

            guild = self.bot.get_guild(value['guild_id'])
            member = self.bot.get_user(value['_id']) or await self.bot.fetch_user(value['_id'])

            if current_time >= unban_time:
                try:
                    await self.bot.bans.delete_one({"_id": member.id})
                    self.bot.banned_users.pop(member.id)
                    await guild.unban(user=member, reason="Ban time expired")

                except discord.NotFound or commands.MemberNotFound or KeyError:
                    pass

    @check_mods.before_loop
    async def before_check_mods(self):
        await self.bot.wait_until_ready()

    @purge_files.before_loop
    async def before_purge_files(self):
        await self.bot.wait_until_ready()

    @update_modlogs.before_loop
    async def before_update_modlogs(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name='cases',
        aliases=['punishments'],
        description='View the moderation cases of a member.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def check_punishments(self, ctx, member: t.Optional[discord.User]):
        member = member or ctx.author
        await get_member_mod_logs(self.bot, member, ctx.guild)
        await ctx.send("TBD...")

    @commands.command(
        name='guildcases',
        aliases=['guildpunishments', 'gpunishments', 'gcases'],
        description='View the moderation cases of your guild.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def check_guild_punishments(self, ctx):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)
        print(logs)

    @commands.command(
        name='deletecase',
        aliases=['deletepunishment', 'delcase', 'delpun'],
        description='Delete a moderation case by ID.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def delete_punishment(self, ctx, case_id: int):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)

        if len(logs) > case_id:
            if case_id > 0:
                await delete_log(self.bot, case_id, ctx.guild)

            else:
                em = discord.Embed(
                    description=f"{ERROR} Cases can't go into the negatives! It's just common sense.",
                    colour=RED)
                await ctx.send(embed=em)

        else:
            em = discord.Embed(
                description=f"{ERROR} An invalid case ID was given."
                            f"```Please pick from {len(logs)} cases```",
                colour=RED)
            await ctx.send(embed=em)

    @commands.command(
        name='viewcase',
        aliases=['viewpunishment', 'vcase', 'case'],
        description='Delete a moderation case by ID.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def view_case(self, ctx, case_id: int):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)

        for i, _log in enumerate(logs, start=1):
            if i == case_id:
                em = discord.Embed(
                    colour=MAIN,
                    timestamp=_log['time']
                )
                moderator = self.bot.get_user(_log["moderator"])
                member = self.bot.get_user(_log["member"])
                em.set_thumbnail(url=member.avatar_url)
                em.set_author(icon_url=moderator.avatar_url, name=f'Case #{_log["case_id"]} - {_log["action"]}')
                em.add_field(name='Member', value=member.mention)
                em.add_field(name='Actioned By', value=moderator.mention)
                em.add_field(name='Reason', value=_log['reason'])
                em.set_footer(text="Actioned at")
                return await ctx.send(embed=em)

        else:
            em = discord.Embed(
                description=f"{ERROR} An invalid case ID was given."
                            f"```Please pick from {len(logs)} cases```",
                colour=RED)
            await ctx.send(embed=em)

    @commands.command(
        name='moderations',
        aliases=['mods', 'activemods', 'activemoderations'],
        description='See the currently active moderation cases. These include timed mutes and bans.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def view_moderations(self, ctx):
        bans, mutes = deepcopy(self.bot.banned_users), deepcopy(self.bot.muted_users)
        cases = bans | mutes
        active = []
        for key, value in cases.items():
            active.append({key: value})

        await ctx.send("TBD...")

    @commands.command(
        name='kick',
        aliases=['k'],
        description='Kicks members from the server. 3 second cooldown, must have Kick Users permission.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await kick_members(self.bot, ctx, member, reason)
            em = discord.Embed(
                description=f"{CHECK} Kicked {member.mention} for `{reason}`",
                timestamp=dt.utcnow(),
                colour=GREEN)
            em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
            await ctx.send(embed=em)

    @commands.command(
        name='ban',
        aliases=['b'],
        description='Bans members from the server, with customizability on how many days of their messages '
                    'should be deleted. 3 second cooldown, must have Ban Members permission.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: t.Union[discord.Member, discord.User],
                      delete_days: t.Optional[int], *, reason: t.Optional[str] = "no reason provided"):
        delete_days = int(delete_days) if delete_days else 7
        if delete_days > 7:
            em = discord.Embed(
                description=f"{ERROR} The `days_delete` parameter has to be either equal or less than 7.",
                colour=RED)
            return await ctx.send(embed=em)

        if isinstance(member, discord.Member):
            if await mod_check(ctx, member): pass

        await ban_members(self.bot, ctx, member, reason, delete_days=delete_days)
        em = discord.Embed(
            description=f"{CHECK} Banned {member.mention} for `{reason}`",
            timestamp=dt.utcnow(),
            colour=GREEN)
        em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
        await ctx.send(embed=em)

    @commands.command(
        name='softban',
        aliases=['sban', 'sb', 'softb'],
        description='Softbans a member, essentially kicking them and deleting all of their messages.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def softban_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await ban_members(self.bot, ctx, member, reason, delete_days=7, _type='softban')
            em = discord.Embed(
                description=f"{CHECK} Softbanned {member.mention} for `{reason}`",
                timestamp=dt.utcnow(),
                colour=GREEN)
            em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
            await ctx.send(embed=em)

    @commands.command(
        name='tempban',
        aliases=['tb', 'tempb', 'tban'],
        description='Tempoarily bans a member, with customizability for duration.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def tempban_cmd(self, ctx, member: t.Union[discord.User, discord.Member], *args):
        try:
            time = pytp.parse(args[0]) or None

        except IndexError:
            time = None

        if not time: reason = ' '.join(args)
        else: reason = ' '.join(args[1:])
        if not reason: reason = 'no reason provided'

        if isinstance(member, discord.Member):
            if await mod_check(ctx, member):
                pass

        try:
            if self.bot.banned_users[member.id]:
                em = discord.Embed(
                    description=f"{ERROR} {member.mention} is already banned! "
                                f"Talk about adding insult to injury.",
                    colour=RED)
                return await ctx.send(embed=em)

        except KeyError:
            pass

        await ban_members(self.bot, ctx, member, reason, time, delete_days=7, _type='tempban')
        em = discord.Embed(
            description=f"{CHECK} Tempbanned {member.mention} lasting `{convert_time(time)}`"
                        f", for `{reason}`", timestamp=dt.utcnow(),
            colour=GREEN)
        em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
        await ctx.send(embed=em)

    # TODO: update paginator for moderation things

    @commands.command(
        name='unban',
        aliases=['ub', 'unb'],
        description='Unbans members from a server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def unban_cmd(self, ctx, member: t.Union[discord.User, int],
                        *, reason: t.Optional[str] = 'no reason provided'):
        await unban_members(self.bot, ctx, member, reason)
        em = discord.Embed(
            description=f"{CHECK} Unbanned {member.mention} for `{reason}`",
            timestamp=dt.utcnow(),
            colour=GREEN)
        em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
        await ctx.send(embed=em)

    @commands.command(
        name='warn',
        aliases=['w', 'wrn'],
        description='Warns members in the server. 3 second cooldown, must have Manage Messages permission.')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await warn_members(self.bot, ctx, member, reason)
            em = discord.Embed(
                description=f"{CHECK} Warned {member.mention} for `{reason}`",
                timestamp=dt.utcnow(),
                colour=GREEN)
            em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
            await ctx.send(embed=em)

    @commands.command(
        name='mute',
        aliases=['m', 'silence'],
        description='Mutes users in the server. '
                    '3 second cooldown, must have Manage Messages permission. Cannot be bypassed.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, manage_roles=True)
    async def mute_cmd(self, ctx, member: discord.Member, *args):
        try:
            time = pytp.parse(args[0]) or None

        except IndexError:
            time = None

        if not time: reason = ' '.join(args)
        else: reason = ' '.join(args[1:])
        if not reason: reason = 'no reason provided'

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{WARNING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=GOLD)
                msg = await ctx.channel.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except KeyError:
            em = discord.Embed(
                description=f"{WARNING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=GOLD)
            msg = await ctx.channel.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if await mod_check(ctx, member):
            if not member.guild_permissions.administrator:
                try:
                    if mute_role in member.roles:
                        em = discord.Embed(
                            description=f"{ERROR} {member.mention} is already muted! "
                                        f"Talk about adding insult to injury.",
                            colour=RED)
                        return await ctx.send(embed=em)

                except KeyError:
                    pass

                await mute_members(self.bot, ctx, member, reason, mute_role, time)
                em = discord.Embed(
                    description=f"{CHECK} Muted {member.mention} lasting `{convert_time(time)}`"
                                f", for `{reason}`", timestamp=dt.utcnow(),
                    colour=GREEN)
                em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
                await ctx.send(embed=em)

            else:
                em = discord.Embed(
                    description=f"{ERROR} {member.mention} has the `Administrator` permission.",
                    color=RED)
                await ctx.send(embed=em)

    @commands.command(
        name='unmute',
        aliases=['um', 'umt', 'unm'],
        description='Unmutes members in the server. 3 second cooldown, must have Manage Messages permission.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True, manage_messages=True)
    async def unmute_cmd(self, ctx, member: discord.Member,
                         *, reason: t.Optional[str] = 'no reason provided'):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{ERROR} This guild does not have a mute role set up.",
                    colour=RED)
                return await ctx.send(embed=em)

        except KeyError:
            em = discord.Embed(
                description=f"{ERROR} This guild does not have a mute role set up.",
                colour=RED)
            return await ctx.send(embed=em)

        if await mod_check(ctx, member):
            if mute_role in member.roles:
                await unmute_members(self.bot, ctx, member, reason, mute_role)
                em = discord.Embed(
                    description=f"{CHECK} Unmuted {member.mention} for `{reason}`", timestamp=dt.utcnow(),
                    colour=GREEN)
                em.set_footer(text=f"Case #{await get_last_case_id(self.bot, ctx.guild) - 1}")
                await ctx.send(embed=em)

            else:
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except commands.MemberNotFound or KeyError:
                    pass

                em = discord.Embed(
                    description=f"{ERROR} {member.mention} is not muted.",
                    colour=RED)
                return await ctx.send(embed=em)

    @commands.command(
        name='lock',
        aliases=['lck', 'lk', 'lockdown'],
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

        elif (channel.overwrites[ctx.guild.default_role].send_messages
              or channel.overwrites[ctx.guild.default_role].send_messages is None):
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
    async def slowmode_cmd(self, ctx, time: t.Union[int, pytp.parse], channel: t.Optional[discord.TextChannel]):
        channel = channel or ctx.channel
        if not time and time != 0:
            em = discord.Embed(
                description=f"{ERROR} Please provide a valid time.",
                colour=RED)
            return await ctx.send(embed=em)

        if time > 21600 or time < 0:
            em = discord.Embed(
                description=f"{ERROR} Slowmode time should be equal or less than 6 hours.",
                colour=RED)
            return await ctx.send(embed=em)

        await channel.edit(slowmode_delay=time,
                           reason=f"{ctx.author}" + 'Slowmode delay edited by {ctx.author} via slowmode command')
        em = discord.Embed(
            description=f"{CHECK} Slowmode delay for {channel.mention} was set to `{convert_time(time)}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='purge',
        aliases=['p', 'prg', 'prune'],
        description='Purge messages in a channel. Limit must be equal or less than 1000.',
        invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_cmd(self, ctx, limit: int, members: commands.Greedy[discord.User]):
        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: m.author in members or not len(members))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='match',
        aliases=['message', 'contain', 'has'],
        description='Purge all messages that match a certain string or sentence.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_match(self, ctx, limit: t.Optional[int], *, match: str):
        def check(m):
            return (str(match.lower())) in str(m.content).lower()

        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: check(m))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='bots',
        aliases=['apps', 'bot'],
        description='Purge messages from bots, ignoring messages sent by members.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_humans(self, ctx, limit: t.Optional[int]):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: m.author.bot)

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='members',
        aliases=['member', 'users', 'user', 'humans'],
        description='Purge messages from bots, ignoring messages sent by bots.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_bots(self, ctx, limit: t.Optional[int]):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: not m.author.bot)

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='nomatch',
        aliases=['matchnot', 'not', 'nocontain'],
        description='Purge messages that do not contain a certain word or sentence.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_no_match(self, ctx, limit: t.Optional[int], *, match: str):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: str(m.content).lower().find(str(match.lower())) == -1)

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='starts',
        aliases=['startswith', 'start', 'sw'],
        description='Purge messages that start with a certain word or sentence.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_starts_with(self, ctx, limit: t.Optional[int], *, match: str):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: str(m.content).lower().startswith(str(match.lower())))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='ends',
        aliases=['endswith', 'end', 'ew'],
        description='Purge messages that end with a certain word or sentence.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_ends_with(self, ctx, limit: t.Optional[int], *, match: str):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: str(m.content).lower().endswith(str(match.lower())))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='links',
        aliases=['url', 'urls', 'link'],
        description='Purge messages containing links.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_links(self, ctx, limit: t.Optional[int]):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: re.search(URL_REGEX, str(m.content).lower()))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='invites',
        aliases=['invs', 'ads', 'invite'],
        description='Purge messages containing discord guild invites.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_invites(self, ctx, limit: t.Optional[int]):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: re.search(INVITE_URL_REGEX, str(m.content).lower()))

        else:
            raise InvalidLimit

    @purge_cmd.command(
        name='mentions',
        aliases=['pings', 'mention', 'ping'],
        description='Purge messages containing mentions.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_mentions(self, ctx, limit: t.Optional[int]):
        limit = limit or 100

        if 0 < limit < 1001:
            await purge_msgs(self.bot, ctx, limit, lambda m: len(m.mentions))

        else:
            raise InvalidLimit

    @commands.command(
        name='voicekick',
        aliases=['vck', 'vk', 'vkick'],
        description='Kick a user from a voice channel. Only works if they are connected.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(move_members=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.guild_only()
    async def voice_kick(self, ctx, member: discord.Member, *, reason: t.Optional[str] = 'no reason provided'):
        try:
            vc = member.voice.channel

        except AttributeError:
            em = discord.Embed(
                description=f"{ERROR} {member.mention} is not in a voice channel.",
                color=RED)
            return await ctx.send(embed=em)

        await member.move_to(channel=None, reason=f"{ctx.author} - " + reason)

        em = discord.Embed(
            description=f"{CHECK} Kicked {member.mention} from `{vc}`",
            color=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Mod(bot))
