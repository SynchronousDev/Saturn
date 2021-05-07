import os
import re
from copy import deepcopy
from glob import glob
from discord.ext.commands.errors import MemberNotFound

import pytimeparse as pytp
from dateutil.relativedelta import relativedelta
from discord.ext import tasks

from assets import *


# noinspection PyUnusedLocal, SpellCheckingInspection
async def purge_msgs(bot, ctx, limit, check):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(
        limit=limit,
        after=datetime.datetime.utcnow() - datetime.timedelta(weeks=2),
        check=check)

    if not len(deleted):
        em = SaturnEmbed(
            description=f"{ERROR} Could not find any messages to delete.\n"
                        f"```Messages older than 2 weeks cannot be deleted```",
            color=RED)
        return await ctx.send(embed=em)

    deleted = list(reversed(deleted))

    em = SaturnEmbed(
        description=f"{CHECK} Deleted {len(deleted)} messages in {ctx.channel.mention}",
        color=GREEN)
    await ctx.send(embed=em, delete_after=2)
    data = await bot.config.find_one({"_id": ctx.guild.id})
    try:
        mod_logs = ctx.guild.get_channel(data['mod_logs'])
        if not mod_logs:
            return

    except (TypeError, KeyError):
        return

    try:
        await create_purge_file(bot, ctx, deleted)

    except FileNotFoundError:
        await asyncio.sleep(0.5)
        await create_purge_file(bot, ctx, deleted)

    file = discord.File(f'{bot.path}/assets/purge_txts/purge-{deleted[0].id}.txt')

    em = SaturnEmbed(
        title='Messages Purged',
        description=f'Deleted {len(deleted)} messages in {ctx.channel.mention}\n'
                    f'Command invoked by {ctx.author.mention}',
        colour=discord.Colour.orange(),
        timestamp=utc()
    )
    em.set_thumbnail(url=NOTE)
    em.set_footer(text="Download the attached .txt file to view the contents.")
    await mod_logs.send(embed=em)
    await asyncio.sleep(0.5)
    await mod_logs.send(file=file)


async def create_purge_file(bot, ctx, deleted):
    try:
        await _create_pfile(bot, ctx, deleted)

    except FileNotFoundError:
        os.mkdir(f"{bot.path}/assets/purge_txts")
        await _create_pfile(bot, ctx, deleted)

async def _create_pfile(bot, ctx, deleted):
    with open(f'{bot.path}/assets/purge_txts/purge-{deleted[0].id}.txt', 'w+', encoding='utf-8') as f:
        f.write(f"{len(deleted)} messages deleted in the #{ctx.channel} channel by {ctx.author}:\n\n")
        for message in deleted:
            content = message.clean_content
            if not message.author.bot:
                f.write(f"{message.author} {convert_to_timestamp(message.created_at)} EST"
                        f" (ID - {message.author.id})\n"
                        f"{content} (Message ID - {message.id})\n\n")

            else:
                f.write(f"{message.author} {convert_to_timestamp(message.created_at)} EST"
                        f" (ID - {message.author.id})\n"
                        f"{'Embed/file sent by a bot' if not content else content}\n\n")


# noinspection PyBroadException,SpellCheckingInspection
async def create_log(bot, member: discord.Member, guild, action, moderator, reason, duration=None):
    """
    Send details about a punishment and log it in the mod logs channel.
    """
    colours = {
        "kick": {"colour": discord.Colour.orange(), "emote": NO_ENTRY},
        "ban": {"colour": discord.Colour.red(), "emote": NO_ENTRY},
        "mute": {"colour": discord.Colour.orange(), "emote": MUTE},
        "unmute": {"colour": discord.Colour.green(), "emote": UNMUTE},
        "warn": {"colour": discord.Colour.gold(), "emote": WARN},
        "unban": {"colour": discord.Colour.gold(), "emote": UNBAN},
        "softban": {"colour": discord.Colour.red(), "emote": NO_ENTRY},
        "tempban": {"colour": discord.Colour.red(), "emote": NO_ENTRY}
    }
    colour = GOLD
    emote = None
    for key, value in colours.items():
        if str(key) == str(action.lower()):
            colour, emote = value["colour"], value["emote"]

    try:
        em = SaturnEmbed(
            colour=colour,
            timestamp=utc()
        )
        em.set_thumbnail(url=emote)
        desc = f"**Guild** - {guild}\n" \
               f"**Moderator** - {moderator.mention}\n" \
               f"**Action** - {action.title()}\n" \
               f"**Reason** - {reason}\n"
        if duration:
            desc += f"**Duration** - {duration}\n"

        em.description = desc

        # noinspection PyTypeChecker
        await member.send(embed=em)

    except discord.HTTPException:
        pass

    # send it to the log channel because why not lol
    data, mod_logs = await bot.config.find_one({"_id": guild.id}), None
    try:
        mod_logs = guild.get_channel(data['mod_logs'])

    except (TypeError, KeyError):
        pass

    action_ = action
    if action.find("ban") != -1:
        action_ += "ned"

    elif action in ("mute", "unmute"):
        action_ += "d"

    else:
        action_ += "ed"

    em = SaturnEmbed(
        title=f'Member {action_.title()}',
        colour=colour,
        timestamp=utc()
    )
    em.set_thumbnail(url=emote)
    em.set_author(icon_url=member.avatar_url, name=member.name)
    em.set_footer(text='Case no. {}'.format(await get_last_case_id(bot, guild)))
    em.add_field(name='Member', value=member.mention)
    em.add_field(name='Moderator', value=moderator.mention)
    if duration:
        em.add_field(name='Duration', value=duration)

    if reason:
        em.add_field(name='Reason', value=reason)

    try:
        await mod_logs.send(embed=em)

    except AttributeError:
        pass

    except discord.HTTPException:
        pass

    _action = action + ((' for ' + duration) if duration else '')
    # get the action + duration for formatting purposes
    await _create_log(bot, member, guild, _action, moderator, reason)  # create the log


async def get_member_mod_logs(bot, member, guild) -> list:
    """
    Fetch mod logs for a specific guild
    Will only fetch the first 10000 punishments, because ya know, operation times suck
    """
    logs = []
    cursor = bot.mod.find({"member": member.id, "guild_id": guild.id})
    for document in await cursor.to_list(length=10000):
        logs.append(document)

    return logs


async def get_guild_mod_logs(bot, guild) -> list:
    """
    Fetch mod logs for a specific guild
    """
    logs = []
    cursor = bot.mod.find({"guild_id": guild.id})
    for document in await cursor.to_list(length=10000):
        logs.append(document)

    return logs


# noinspection SpellCheckingInspection
async def get_last_case_id(bot, guild) -> int:
    """
    Return the case_id of the current case
    """
    logs = await get_guild_mod_logs(bot, guild)
    await update_log_caseids(bot, guild)

    if not logs:
        return 1

    else:
        try:
            return int(logs[-1]["case_id"]) + 1

        except (TypeError, KeyError):
            return 1


async def _create_log(bot, member: discord.Member, guild, action, moderator, reason) -> None:
    """
    Create a new log object in the database
    """
    case_id = await get_last_case_id(bot, guild)

    schema = {
        "guild_id": guild.id,
        "case_id": case_id,
        "member": member.id,
        "action": action,
        "moderator": moderator.id,
        "reason": reason,
        "time": utc()
    }
    await bot.mod.insert_one(schema)


# noinspection PyUnusedLocal
async def update_log(bot, case_id, guild, action, reason) -> None:
    """
    Update a mod log
    Used to update reasons for punishments
    """
    logs = await get_guild_mod_logs(bot, guild)

    schema = {
        "action": action,
        "reason": reason
    }
    await bot.mod.update_one({"guild_id": guild.id, "case_id": case_id}, {"$set": schema}, upsert=True)


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


async def update_log_caseids(bot, guild) -> None:
    """
    Update the case_ids for the logs. Run when a case is deleted and you need to update the case_ids for the logs.
    """
    logs = await get_guild_mod_logs(bot, guild)

    for i, _log in enumerate(logs, start=1):
        if i != _log['case_id']:
            await bot.mod.update_one(
                {"guild_id": guild.id, "case_id": _log['case_id']}, {"$set": {"case_id": i}}, upsert=True)


async def delete_log(bot, id, guild) -> None:
    """
    Delete a moderation log.
    """
    await bot.mod.delete_one({"guild_id": guild.id, "case_id": id})
    await update_log_caseids(bot, guild)


async def kick_members(bot, ctx, member, reason):
    """
    Kick members
    """
    await create_log(bot, member, ctx.guild, 'kick', ctx.author if ctx.author != member else ctx.guild.me, reason)
    await member.kick(reason=f"{ctx.author if ctx.author != member else ctx.guild.me} - " + reason)


# noinspection PyShadowingNames
async def ban_members(bot, ctx, member, reason, time=None, delete_days=None, _type='ban'):
    """
    Ban members
    """
    if time:
        schema = {
            '_id': member.id,
            'at': utc(),
            'duration': time or None,
            'moderator': ctx.author.id,
            'guild_id': ctx.guild.id,
            'type': 'ban'
        }
        await bot.bans.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
        bot.banned_users[member.id] = schema

    await ctx.guild.ban(member, reason=f"{ctx.author if ctx.author != member else ctx.guild.me} - "
                                       + reason, delete_message_days=delete_days)
    await create_log(bot, member, ctx.guild, _type, ctx.author if ctx.author != member else ctx.guild.me, reason)

    if _type == 'softban':
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

    except (TypeError, KeyError):
        pass

    await create_log(bot, member, ctx.guild, "unban", ctx.author if ctx.author != member else ctx.guild.me, reason)


# noinspection PyShadowingNames
async def mute_members(bot, ctx, member: discord.Member, reason, mute_role, time=None):
    """
    Mute members
    """
    schema = {
        '_id': member.id,
        'at': utc(),
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

    except (commands.MemberNotFound, KeyError):
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


# noinspection SpellCheckingInspection,PyShadowingNames
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

    def cog_check(self, ctx):
        if ctx.guild:
            return True

        return False

    @tasks.loop(minutes=1)
    async def update_modlogs(self):
        for guild in self.bot.guilds:
            await update_log_caseids(self.bot, guild)

    @tasks.loop(seconds=30)
    async def purge_files(self):
        for file in glob(self.bot.path + '/assets/purge_txts/*.txt'):
            os.unlink(file)

    @tasks.loop(seconds=1)
    async def check_mods(self):
        current_time = utc()
        mutes = deepcopy(self.bot.muted_users)
        bans = deepcopy(self.bot.banned_users)

        # mutes stuff
        for key, value in mutes.items():
            guild = self.bot.get_guild(value['guild_id'])

            member = guild.get_member(value['_id']) or await self.bot.fetch_user(value['_id'])

            data = await self.bot.config.find_one({"_id": guild.id})
            mute_role = guild.get_role(data['mute_role'])

            try:
                join_delta = utc() - member.joined_at. \
                    replace(tzinfo=datetime.timezone.utc)

            except AttributeError:
                continue

            if mute_role not in member.roles and join_delta > datetime.timedelta(seconds=3):
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except (commands.MemberNotFound, KeyError):
                    pass

                continue

            if value['duration'] is None:
                continue

            unmute_time = value['at'] + relativedelta(seconds=value['duration'])

            if current_time >= unmute_time.replace(tzinfo=datetime.timezone.utc):
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except (commands.MemberNotFound, KeyError):
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

                            except (commands.MemberNotFound, KeyError):
                                pass

                    except (TypeError, KeyError):
                        pass

        for key, value in bans.items():
            if value['duration'] is None:
                continue

            unban_time = value['at'] + relativedelta(seconds=value['duration'])

            guild = self.bot.get_guild(value['guild_id'])
            member = self.bot.get_user(value['_id']) or await self.bot.fetch_user(value['_id'])

            if current_time >= unban_time.replace(tzinfo=datetime.timezone.utc):
                try:
                    await self.bot.bans.delete_one({"_id": member.id})
                    self.bot.banned_users.pop(member.id)
                    await guild.unban(user=member, reason="Ban time expired")

                except (discord.NotFound, commands.MemberNotFound, KeyError):
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

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # check for mute stuff
        data = await self.bot.config.find_one({"_id": after.guild.id})
        try:
            if not data['mute_role']: return
        except (TypeError, KeyError):
            return

        mute_role = after.guild.get_role(data['mute_role'])

        if (mute_role in before.roles) and (mute_role not in after.roles):
            try:
                await self.bot.mutes.delete_one({"_id": after.id})
                self.bot.muted_users.pop(after.id)

            except (commands.MemberNotFound, KeyError):
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Fires when a member joins the server
        """
        try:
            if self.bot.muted_users[member.id]:
                data = await self.bot.config.find_one({"_id": member.guild.id})
                mute_role = member.guild.get_role(data['mute_role'])
                if mute_role:
                    await member.add_roles(mute_role, reason='Role Persists', atomic=True)
                    # check if the member left the server while they were muted
                    # anti-mute bypass yes

        except (TypeError, KeyError):
            pass

    @commands.command(
        name='cases',
        aliases=['punishments'],
        description='View the moderation cases of a member.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def check_punishments(self, ctx, member: typing.Optional[typing.Union[discord.Member, discord.User]]):
        member = member or ctx.author
        logs = await get_member_mod_logs(self.bot, member, ctx.guild)
        entries = []
        for entry in logs:
            time = entry["time"]
            desc = f"""
            **Case ID** - {entry['case_id']}
            **Moderator** - <@!{entry['moderator']}>
            **Action** - {entry['action']}
            **Reason** - {entry['reason']}
            **Time** - {convert_to_timestamp(time)}
            """
            entries.append(desc)

        if not entries:
            entries = [f"There are no punishments for {member.mention}! Hooray!"]

        pager = Paginator(
            title=f'Punishments for **{member.name}**',
            colour=member.colour if isinstance(member, discord.Member) else MAIN,
            entries=entries,
            thumbnail=member.avatar_url,
            length=1
        )
        await pager.start(ctx)

    @commands.command(
        name='guildcases',
        aliases=['guildpunishments', 'gpunishments', 'gcases'],
        description='View the moderation cases of your guild.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def check_guild_punishments(self, ctx):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)
        entries = []
        for entry in logs:
            action = entry["action"]
            if action.find("mute") != -1 and action != "unmute":
                _action = action.split(' ')
                _duration = ' '.join(_action[2:])
                desc = f"""
                **Case ID** - {entry['case_id']}
                **Member** - <@!{entry['member']}>            
                **Moderator** - <@!{entry['moderator']}>
                **Action** - {_action[0]}
                **Duration** - {_duration}
                **Reason** - {entry['reason']}
                **Time** - {convert_to_timestamp(_time=entry['time'])}
                """

            else:
                desc = f"""
                **Case ID** - {entry['case_id']}
                **Member** - <@!{entry['member']}>            
                **Moderator** - <@!{entry['moderator']}>
                **Action** - {entry['action']}
                **Reason** - {entry['reason']}
                **Time** - {convert_to_timestamp(_time=entry['time'])}
                """
            entries.append(desc)

        if not entries:
            entries = ["There are no punishments in this guild! Hooray!"]

        pager = Paginator(
            title=f'Punishments in **{ctx.guild}**',
            colour=MAIN,
            entries=entries,
            thumbnail=ctx.guild.icon_url,
            length=1
        )
        await pager.start(ctx)

    @commands.command(
        name='deletecase',
        aliases=['deletepunishment', 'delcase', 'delpun'],
        description='Delete a moderation case by ID.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    async def delete_punishment(self, ctx, case_id: int):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)

        if len(logs) >= case_id:
            if case_id > 0:
                conf = await ConfirmationMenu(f'delete case `{case_id}`').prompt(ctx)
                if conf:
                    await delete_log(self.bot, case_id, ctx.guild)
                    em = SaturnEmbed(
                        description=f"{CHECK} Deleted punishment number `{case_id}`",
                        colour=GREEN)
                    await ctx.send(embed=em)

            else:
                em = SaturnEmbed(
                    description=f"{ERROR} Cases can't go into the negatives! It's just common sense.",
                    colour=RED)
                await ctx.send(embed=em)

        else:
            em = SaturnEmbed(
                description=f"{ERROR} An invalid case ID was given."
                            f"```Please pick from {len(logs)} cases```",
                colour=RED)
            await ctx.send(embed=em)

    @commands.command(
        name='viewcase',
        aliases=['viewpunishment', 'vcase', 'case'],
        description='Delete a moderation case by ID.'
    )
    @commands.cooldown(1, 1, commands.BucketType.member)
    async def view_case(self, ctx, case_id: int):
        logs = await get_guild_mod_logs(self.bot, ctx.guild)

        for i, entry in enumerate(logs, start=1):
            if i == case_id:
                action = entry["action"]
                if action.find("mute") != -1 and action != "unmute":
                    _action = action.split(' ')
                    _duration = ' '.join(_action[2:])
                    desc = f"""
                    **Case ID** - {entry['case_id']}
                    **Member** - <@!{entry['member']}>            
                    **Moderator** - <@!{entry['moderator']}>
                    **Action** - {_action[0]}
                    **Duration** - {_duration}
                    **Reason** - {entry['reason']}
                    """

                else:
                    desc = f"""
                    **Member** - <@!{entry['member']}>            
                    **Moderator** - <@!{entry['moderator']}>
                    **Action** - {entry['action']}
                    **Reason** - {entry['reason']}
                    """

                em = SaturnEmbed(
                    colour=MAIN,
                    description=desc,
                    timestamp=entry['time']
                )
                moderator = ctx.guild.get_member(entry["moderator"]) or await self.bot.fetch_user(entry["moderator"])
                member = ctx.guild.get_member(entry["member"]) or await self.bot.fetch_user(entry["member"])
                em.set_thumbnail(url=member.avatar_url)
                em.set_author(icon_url=moderator.avatar_url, name=moderator)
                em.set_footer(text=f"Case #{entry['case_id']}")
                return await ctx.send(embed=em)

        else:
            em = SaturnEmbed(
                description=f"{ERROR} An invalid case ID was given."
                            f"```Please pick from {len(logs)} cases```",
                colour=RED)
            await ctx.send(embed=em)

    @commands.command(
        name='moderations',
        aliases=['amods', 'activemods', 'activemoderations'],
        description='See the currently active moderation cases.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def view_active_moderations(self, ctx):
        bans, mutes = deepcopy(self.bot.banned_users), deepcopy(self.bot.muted_users)
        cases = bans | mutes
        _entries, entries = [], []
        for key, value in cases.items():
            _entries.append({key: value})

        for entry in _entries:
            for key, value in entry.items():
                duration = value['duration']
                if duration:
                    ends_at = (value['at'] + datetime.timedelta(seconds=duration)) \
                        .replace(tzinfo=datetime.timezone.utc)
                    delta = (ends_at - utc()).total_seconds()

                else:
                    delta = 'never'

                desc = f"""
                **Member** - <@!{value['_id']}>            
                **Moderator** - <@!{value['moderator']}>
                **Action** - {value['type']}
                **Duration** - {general_convert_time(duration) if duration else 'indefinite'}
                **Ends at** - {general_convert_time(delta) if delta != 'never' else delta}
                **Time** - {convert_to_timestamp(value['at'])}
                """
                entries.append(desc)

        if not entries:
            entries = ["There are no active punishments in this guild! Hooray!"]

        pager = Paginator(
            title=f'Active Punishments in **{ctx.guild}**',
            colour=MAIN,
            entries=entries,
            thumbnail=ctx.guild.icon_url,
            length=1
        )
        await pager.start(ctx)

    @commands.command(
        name='kick',
        aliases=['k'],
        description='Kicks members from the server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await kick_members(self.bot, ctx, member, reason)
            em = SaturnEmbed(
                description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                            f"{member.mention} has been kicked.",
                colour=GREEN)
            await ctx.send(embed=em)

    @commands.command(
        name='ban',
        aliases=['b'],
        description='Bans members from the server, with customizability on how many days of their messages '
                    'should be deleted.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: typing.Union[discord.Member, discord.User],
                      delete_days: typing.Optional[int], *, reason: typing.Optional[str] = "no reason provided"):
        delete_days = int(delete_days) if delete_days else 7
        if delete_days > 7:
            em = SaturnEmbed(
                description=f"{ERROR} The `days_delete` parameter has to be either equal or less than 7.",
                colour=RED)
            return await ctx.send(embed=em)

        if isinstance(member, discord.Member):
            if not await mod_check(ctx, member): return

        await ban_members(self.bot, ctx, member, reason, delete_days=delete_days)
        em = SaturnEmbed(
            description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                        f"{member.mention} has been banned.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='softban',
        aliases=['sban', 'sb', 'softb'],
        description='Softbans a member, essentially kicking them and deleting all of their messages.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def softban_cmd(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await ban_members(self.bot, ctx, member, reason, delete_days=7, _type='softban')
            em = SaturnEmbed(
                description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                            f"{member.mention} has been softbanned.",
                colour=GREEN)
            await ctx.send(embed=em)

    @commands.command(
        name='tempban',
        aliases=['tb', 'tempb', 'tban'],
        description='Tempoarily bans a member, with customizability for duration.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def tempban_cmd(self, ctx, member: typing.Union[discord.User, discord.Member], *time_and_reason):
        try:
            time = pytp.parse(time_and_reason[0]) or None

        except IndexError:
            time = None

        if not time:
            reason = ' '.join(time_and_reason)
        else:
            reason = ' '.join(time_and_reason[1:])
        if not reason: reason = 'no reason provided'

        if isinstance(member, discord.Member):
            if await mod_check(ctx, member):
                pass

        try:
            if self.bot.banned_users[member.id]:
                em = SaturnEmbed(
                    description=f"{ERROR} {member.mention} is already banned! "
                                f"Talk about adding insult to injury.",
                    colour=RED)
                return await ctx.send(embed=em)

        except (TypeError, KeyError):
            pass

        await ban_members(self.bot, ctx, member, reason, time, delete_days=7, _type='tempban')
        em = SaturnEmbed(
            description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                        f"{member.mention} has been banned for `{convert_time(time)}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='massban',
        aliases=['mb', 'massb', 'mban'],
        description="Ban up to five members with a single command."
    )
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def mass_ban(self, ctx, members: commands.Greedy[discord.Member],
                       *, reason: typing.Optional[str] = "no reason provided"):
        if not members or len(members) > 5:
            em = SaturnEmbed(
                description=f"{ERROR} Invalid members specified."
                            f"```Limit must be between 1 and 5 members```",
                colour=RED)
            return await ctx.send(embed=em)

        else:
            banned, failed = [], []
            for member in members:
                try:
                    await ctx.guild.ban(member, reason=reason, delete_message_days=7)
                    await create_log(
                        self.bot, member, ctx.guild, 'massban', ctx.author, reason)
                    banned.append(member)

                except TypeError:
                    failed.append(member)

        if not len(failed) and not len(banned):
            em = SaturnEmbed(
                description=f"{ERROR} Invalid members specified."
                            f"```No members were given```",
                colour=RED)
            return await ctx.send(embed=em)

        if not len(failed):
            last_case = await get_last_case_id(self.bot, ctx.guild) - 1
            em = SaturnEmbed(
                description=(f"{CHECK} `Case #{last_case - len(members)} to #{last_case}`"
                             if len(members) > 1 else f"{CHECK} `Case #{last_case}`"),
                colour=GREEN)

        else:
            em = SaturnEmbed(
                description=f"{ERROR} `Could not ban all members.`",
                colour=RED)

        if len(banned) > 0:
            em.add_field(name='Successful Bans', value="\n".join(reversed([f"<@1{m.id}>" for m in banned])))

        if len(failed) > 0:
            em.add_field(name='Failed Bans', value="\n".join(reversed([f"<@!{m.id}>" for m in failed])))

        await ctx.send(embed=em)

    @commands.command(
        name='unban',
        aliases=['ub', 'unb'],
        description='Unbans members from a server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def unban_cmd(self, ctx, member: typing.Union[discord.User, int],
                        *, reason: typing.Optional[str] = 'no reason provided'):
        await unban_members(self.bot, ctx, member, reason)
        em = SaturnEmbed(
            description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                        f"{member.mention} has been unbanned.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='warn',
        aliases=['w', 'wrn'],
        description='Warns members in the server.')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = "no reason provided"):
        if await mod_check(ctx, member):
            await warn_members(self.bot, ctx, member, reason)
            em = SaturnEmbed(
                description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                            f"{member.mention} has been warned.",
                colour=GREEN)
            await ctx.send(embed=em)

    @commands.command(
        name='mute',
        aliases=['m', 'silence'],
        description='Mutes users in the server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, manage_roles=True)
    async def mute_cmd(self, ctx, member: discord.Member, *time_and_reason):
        try:
            time = pytp.parse(time_and_reason[0]) or None

        except IndexError:
            time = None

        if not time:
            reason = ' '.join(time_and_reason)
        else:
            reason = ' '.join(time_and_reason[1:])
        if not reason: reason = 'no reason provided'

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role'])
            if not mute_role:
                em = SaturnEmbed(
                    description=f"{WARNING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=GOLD)
                msg = await ctx.channel.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{WARNING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=GOLD)
            msg = await ctx.channel.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if await mod_check(ctx, member):
            if not member.guild_permissions.administrator:
                try:
                    if mute_role in member.roles:
                        em = SaturnEmbed(
                            description=f"{ERROR} {member.mention} is already muted! "
                                        f"Talk about adding insult to injury.",
                            colour=RED)
                        return await ctx.send(embed=em)

                except (TypeError, KeyError):
                    pass

                await mute_members(self.bot, ctx, member, reason, mute_role, time)
                em = SaturnEmbed(
                    description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                                f"{member.mention} has been muted"
                                f"{f' for `{convert_time(time)}`' if convert_time(time) != 'indefinitely' else '.'}",
                    colour=GREEN)
                await ctx.send(embed=em)

            else:
                em = SaturnEmbed(
                    description=f"{ERROR} {member.mention} has the `Administrator` permission.",
                    color=RED)
                await ctx.send(embed=em)

    @commands.command(
        name='unmute',
        aliases=['um', 'umt', 'unm'],
        description='Unmutes members in the server.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True, manage_messages=True)
    async def unmute_cmd(self, ctx, member: discord.Member,
                         *, reason: typing.Optional[str] = 'no reason provided'):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role'])
            if not mute_role:
                em = SaturnEmbed(
                    description=f"{ERROR} This guild does not have a mute role set up.",
                    colour=RED)
                return await ctx.send(embed=em)

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{ERROR} This guild does not have a mute role set up.",
                colour=RED)
            return await ctx.send(embed=em)

        if await mod_check(ctx, member):
            if mute_role in member.roles:
                await unmute_members(self.bot, ctx, member, reason, mute_role)
                em = SaturnEmbed(
                    description=f"{CHECK} `Case #{await get_last_case_id(self.bot, ctx.guild) - 1}` "
                                f"{member.mention} has been unmuted.",
                    colour=GREEN)
                await ctx.send(embed=em)

            else:
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})
                    self.bot.muted_users.pop(member.id)

                except (commands.MemberNotFound, KeyError):
                    pass

                em = SaturnEmbed(
                    description=f"{ERROR} {member.mention} is not muted.",
                    colour=RED)
                return await ctx.send(embed=em)

    @commands.command(
        name='lock',
        aliases=['lck', 'lk', 'lockdown'],
        description='Locks a channel. Essentially mutes the channel and no one can talk in it. '
                    'Run the command again to unlock the channel.')
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lock_cmd(self, ctx, channel: typing.Optional[discord.TextChannel]):
        channel = channel or ctx.channel

        if ctx.guild.default_role not in channel.overwrites:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)
            }
            await channel.edit(overwrites=overwrites)
            em = SaturnEmbed(
                description=f"{LOCK} {channel.mention} is now locked.",
                colour=RED)
            await ctx.send(embed=em)

        elif (channel.overwrites[ctx.guild.default_role].send_messages
              or channel.overwrites[ctx.guild.default_role].send_messages is None):
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            em = SaturnEmbed(
                description=f"{LOCK} {channel.mention} is now locked.",
                colour=RED)
            await ctx.send(embed=em)

        else:
            overwrites = channel.overwrites[ctx.guild.default_role]
            overwrites.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
            em = SaturnEmbed(
                description=f"{UNLOCK} {channel.mention} is now unlocked.",
                colour=GREEN)
            await ctx.send(embed=em)

    @commands.command(
        name='slowmode',
        aliases=['slm', 'sl'],
        description='Changes the slowmode delay on a given channel. '
                    'Must be equal or less than 6 hours.')
    @commands.has_guild_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def slowmode_cmd(self, ctx, time: typing.Union[int, pytp.parse],
                           channel: typing.Optional[discord.TextChannel]):
        channel = channel or ctx.channel
        if not time and time != 0:
            em = SaturnEmbed(
                description=f"{ERROR} Please provide a valid time.",
                colour=RED)
            return await ctx.send(embed=em)

        if time > 21600 or time < 0:
            em = SaturnEmbed(
                description=f"{ERROR} Slowmode time should be equal or less than 6 hours.",
                colour=RED)
            return await ctx.send(embed=em)

        await channel.edit(slowmode_delay=time,
                           reason=f"{ctx.author}" + 'Slowmode delay edited by {ctx.author} via slowmode command')
        em = SaturnEmbed(
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
    async def purge_match(self, ctx, limit: typing.Optional[int], *, match: str):
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
    async def purge_humans(self, ctx, limit: typing.Optional[int]):
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
    async def purge_bots(self, ctx, limit: typing.Optional[int]):
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
    async def purge_no_match(self, ctx, limit: typing.Optional[int], *, match: str):
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
    async def purge_starts_with(self, ctx, limit: typing.Optional[int], *, match: str):
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
    async def purge_ends_with(self, ctx, limit: typing.Optional[int], *, match: str):
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
    async def purge_links(self, ctx, limit: typing.Optional[int]):
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
    async def purge_invites(self, ctx, limit: typing.Optional[int]):
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
    async def purge_mentions(self, ctx, limit: typing.Optional[int]):
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
    async def voice_kick(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = 'no reason provided'):
        try:
            vc = member.voice.channel

        except AttributeError:
            em = SaturnEmbed(
                description=f"{ERROR} {member.mention} is not in a voice channel.",
                color=RED)
            return await ctx.send(embed=em)

        await member.move_to(channel=None, reason=f"{ctx.author} - " + reason)

        em = SaturnEmbed(
            description=f"{CHECK} Kicked {member.mention} from `{vc}`",
            color=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Mod(bot))
