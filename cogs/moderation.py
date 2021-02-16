import typing as t
from copy import deepcopy
from dateutil.relativedelta import relativedelta

from discord.ext import menus
from discord.ext import tasks
from assets import *
import pytimeparse as pytp
import asyncio
from datetime import datetime as dt, timedelta


# noinspection PyTypeChecker
class GuildPunishmentsMenu(menus.ListPageSource):
    def __init__(self, ctx, data, bot):
        self.ctx = ctx
        self.bot = bot

        super().__init__(data, per_page=10)

    async def write_cases(self, menu, punishments):
        offset = (menu.current_page * self.per_page) + 1
        len_data = len(self.entries)

        em = discord.Embed(
            title=f'{self.ctx.guild}\'s Moderation Cases',
            colour=MAIN,
            timestamp=dt.utcnow())
        em.set_thumbnail(url=self.ctx.guild.icon_url)

        if not punishments:
            em.description = 'This guild has a clean record! Amazing!'

        else:
            em.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page - 1):,} "
                               f"of {len_data:,} punishments")

            for case in punishments:
                case_id = case['case_id']
                action = case['action']
                user = self.bot.get_user(case['member']) or (await self.bot.fetch_user(case['member']))
                reason = case['reason']
                em.add_field(
                    name=f'{case_id}.  {action} on {user}',
                    value=reason + ' - ' + '<@!{}>'.format(case['moderator']), inline=False)

        return em

    async def format_page(self, menu, entries):
        return await self.write_cases(menu, entries)


# noinspection PyTypeChecker
class PunishmentsMenu(menus.ListPageSource):
    def __init__(self, ctx, data, bot, member):
        self.ctx = ctx
        self.bot = bot
        self.member = member

        super().__init__(data, per_page=10)

    async def write_cases(self, menu, punishments):
        offset = (menu.current_page * self.per_page) + 1
        len_data = len(self.entries)

        em = discord.Embed(
            title='Moderation Cases',
            colour=MAIN,
            timestamp=dt.utcnow())

        if not punishments:
            em.description = f'{self.member.mention} has a clean record!'

        else:
            em.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page - 1):,} "
                               f"of {len_data:,} punishments")

            for case in punishments:
                case_id = case['case_id']
                action = case['action']
                reason = case['reason']
                em.set_thumbnail(url=self.member.avatar_url)
                em.add_field(
                    name=f'Case no. {case_id} - {action}',
                    value=reason + ' - ' + '<@!{}>'.format(case['moderator']), inline=False)

        return em

    async def format_page(self, menu, entries):
        return await self.write_cases(menu, entries)


class Mod(commands.Cog, name='Moderation'):
    """
    The moderation cog. Includes all commands related to moderation.

    This includes commands related to kicking, banning, muting, fetching punishments, etc...
    """
    def __init__(self, bot):
        self.bot = bot
        self.mute_task = self.check_mutes.start()
        self.ban_task = self.check_bans.start()
        self.mod_task = self.update_modlogs.start()

    def cog_unload(self):
        self.mute_task.cancel()
        self.mod_task.cancel()

    @tasks.loop(minutes=1)
    async def update_modlogs(self):
        for guild in self.bot.guilds:
            await update_log_caseids(self.bot, guild)

    @tasks.loop(seconds=1)
    async def check_mutes(self):
        current_time = dt.utcnow()
        mutes = deepcopy(self.bot.muted_users)

        for key, value in mutes.items():
            if value['mute_duration'] is None:
                continue

            unmute_time = value['muted_at'] + relativedelta(seconds=value['mute_duration'])

            guild = self.bot.get_guild(value['guild_id'])

            member = guild.get_member(value['_id'])

            data = await self.bot.config.find_one({"_id": guild.id})
            mute_role = guild.get_role(data['mute_role_id'])

            if current_time >= unmute_time:
                if not member:
                    continue

                try:
                    await self.bot.mutes.delete_one({"_id": member.id})

                except commands.MemberNotFound:
                    pass

                if mute_role in member.roles:
                    await member.remove_roles(mute_role, reason='Mute time expired', atomic=True)

                try:
                    self.bot.muted_users.pop(member.id)

                except KeyError:
                    pass

            else:
                if member in guild.members:
                    if mute_role not in member.roles:
                        await member.add_roles(mute_role, reason='Role Persists')

    @tasks.loop(seconds=1)
    async def check_bans(self):
        current_time = dt.utcnow()
        bans = deepcopy(self.bot.banned_users)

        for key, value in bans.items():
            if value['ban_duration'] is None:
                continue

            unban_time = value['banned_at'] + relativedelta(seconds=value['ban_duration'])

            guild = self.bot.get_guild(value['guild_id'])
            member = self.bot.get_user(value['_id']) or await self.bot.fetch_user(value['_id'])

            data = await self.bot.config.find_one({"_id": guild.id})

            if current_time >= unban_time:
                try:
                    await self.bot.bans.delete_one({"_id": member.id})
                    await guild.unban(user=member, reason="Ban time expired")

                except commands.MemberNotFound:
                    pass

                try:
                    self.bot.banned_users.pop(member.id)

                except KeyError:
                    pass

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.bot.wait_until_ready()

    @check_bans.before_loop
    async def before_check_bans(self):
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
        punishments = await get_member_modlogs(self.bot, member, ctx.guild)
        menu = menus.MenuPages(source=PunishmentsMenu(ctx, punishments, self.bot, member), delete_message_after=True)

        await menu.start(ctx)

    @commands.command(
        name='guildcases',
        aliases=['guildpunishments', 'gpunishments', 'gcases'],
        description='View the moderation cases of your guild.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def check_guild_punishments(self, ctx):
        punishments = await get_guild_modlogs(self.bot, ctx.guild)
        menu = menus.MenuPages(source=GuildPunishmentsMenu(ctx, punishments, self.bot), delete_message_after=True)

        await menu.start(ctx)

    @commands.command(
        name='deletecase',
        aliases=['deletepunishment', 'delcase', 'delpun'],
        description='Delete a moderation case by ID.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def delete_punishment(self, ctx, case_id: int):
        logs = await get_guild_modlogs(self.bot, ctx.guild)

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
        logs = await get_guild_modlogs(self.bot, ctx.guild)

        for i, log in enumerate(logs, start=1):
            if i == case_id:
                em = discord.Embed(
                    colour=MAIN,
                    timestamp=log['time']
                )
                moderator = self.bot.get_user(log["moderator"])
                member = self.bot.get_user(log["member"])
                em.set_thumbnail(url=member.avatar_url)
                em.set_author(icon_url=moderator.avatar_url, name=f'Case no. {log["case_id"]} - {log["action"]}')
                em.add_field(name='Member', value=member.mention)
                em.add_field(name='Actioned By', value=moderator.mention)
                em.add_field(name='Reason', value=log['reason'])
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
        active = {}
        bans = deepcopy(self.bot.banned_users)
        mutes = deepcopy(self.bot.muted_users)

        em = discord.Embed(
            title='Active Moderation Cases',
            colour=MAIN,
            timestamp=dt.utcnow()
        )

        if not bans and not mutes:
            em.description = "There are currently no active moderation cases in this guild! Hooray!"

        else:
            for key, value in bans.items():
                try:
                    text = f"Duration - `{convert_time(value['ban_duration'])}`\n"
                    text += f"End time - " \
                            f"`{str(value['banned_at'] + relativedelta(seconds=value['ban_duration']))[:-7]} UTC`"
                    em.add_field(name=self.bot.get_user(value['_id']), value=text)

                except KeyError:
                    em.add_field(name=self.bot.get_user(value['_id']), value="Indefinite ban")
                    raise

            for key, value in mutes.items():
                try:
                    text = f"Duration - `{convert_time(value['mute_duration'])}`\n"
                    text += f"End time - " \
                            f"`{str(value['muted_at'] + relativedelta(seconds=value['mute_duration']))[:-7]} UTC`"
                    em.add_field(name=self.bot.get_user(value['_id']), value=text)

                except KeyError:
                    em.add_field(name=self.bot.get_user(value['_id']), value="Indefinite mute")

        await ctx.send(embed=em)

    @commands.command(
        name='kick',
        aliases=['k'],
        description='Kicks members from the server. 3 second cooldown, must have Kick Users permission.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if member is not ctx.guild.owner:
                    em = discord.Embed(
                        description=f"{CHECK} Kicked {member.mention} for `{reason}`",
                        timestamp=dt.utcnow(),
                        colour=GREEN)
                    em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                    await ctx.send(embed=em)
                    await send_punishment(self.bot, member, ctx.guild, 'kick', ctx.author, reason)
                    await member.kick(reason=reason)
                else:
                    raise RoleNotHighEnough

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

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
            if ctx.guild.me.top_role > member.top_role:
                if ctx.author.top_role > member.top_role:
                    if member is not ctx.guild.owner:
                        em = discord.Embed(
                            description=f"{CHECK} Banned {member.mention} for `{reason}`",
                            timestamp=dt.utcnow(),
                            colour=GREEN)
                        await ctx.send(embed=em)
                        em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                        await send_punishment(self.bot, member, ctx.guild, 'ban', ctx.author, reason)
                        await member.ban(reason=reason, delete_message_days=delete_days)
                    else:
                        raise RoleNotHighEnough

                else:
                    raise RoleNotHighEnough

            else:
                raise BotRoleNotHighEnough

        elif isinstance(member, discord.User):
            em = discord.Embed(
                description=f"{CHECK} Banned {member.mention} for `{reason}`",
                timestamp=dt.utcnow(),
                colour=GREEN)
            await ctx.send(embed=em)
            await ctx.guild.ban(member, reason=reason, delete_message_days=delete_days)

    @commands.command(
        name='softban',
        aliases=['sban', 'sb', 'softb'],
        description='Softbans a member, essentially kicking them and deleting all of their messages.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def softban_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if member is not ctx.guild.owner:
                    em = discord.Embed(
                        description=f"{CHECK} Softbanned {member.mention} for `{reason}`",
                        timestamp=dt.utcnow(),
                        colour=GREEN)
                    await ctx.send(embed=em)
                    em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                    await send_punishment(self.bot, member, ctx.guild, 'softban', ctx.author, reason)
                    await member.ban(reason=reason, delete_message_days=7)
                    await asyncio.sleep(0.5)
                    await member.unban(reason='Softban actioned by {0} (ID {1})'.format(ctx.author, ctx.author.id))

                else:
                    raise RoleNotHighEnough

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

    @commands.command(
        name='tempban',
        aliases=['tb', 'tempb', 'tban'],
        description='Tempoarily bans a member, with customizability for duration.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def tempban_cmd(self, ctx, member: t.Union[discord.Member, discord.User], *args):
        time = pytp.parse(args[0]) or None
        if not time:
            reason = ' '.join(args)

        else:
            reason = ' '.join(args[1:])
            if not reason:
                reason = 'no reason provided'

        if isinstance(member, discord.Member):
            if ctx.guild.me.top_role > member.top_role:
                if ctx.author.top_role > member.top_role:
                    if member is not ctx.guild.owner:
                        try:
                            if self.bot.banned_users[member.id]:
                                em = discord.Embed(
                                    description=f"{ERROR} {member.mention} is already banned! "
                                                f"Talk about adding insult to injury.",
                                    colour=RED)
                                return await ctx.send(embed=em)

                        except KeyError:
                            pass

                        schema = {
                            '_id': member.id,
                            'banned_at': dt.utcnow(),
                            'ban_duration': time or None,
                            'banned_by': ctx.author.id,
                            'guild_id': ctx.guild.id
                        }

                        await self.bot.bans.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
                        self.bot.banned_users[member.id] = schema
                        await send_punishment(self.bot, member, ctx.guild, 'temporary ban',
                                              ctx.author, reason, convert_time(time))
                        await member.ban(reason=reason)
                        em = discord.Embed(
                            description=f"{CHECK} Tempbanned {member.mention} lasting `{str(convert_time(time))}`"
                                        f", for `{reason}`", timestamp=dt.utcnow(),
                            colour=GREEN)
                        em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                        await ctx.send(embed=em)

                    else:
                        raise RoleNotHighEnough

                else:
                    raise RoleNotHighEnough

            else:
                raise BotRoleNotHighEnough

        elif isinstance(member, discord.User):
            try:
                if self.bot.bans[member.id]:
                    em = discord.Embed(
                        description=f"{ERROR} {member.mention} is already banned! "
                                    f"Talk about adding insult to injury.",
                        colour=RED)
                    return await ctx.send(embed=em)

            except KeyError:
                pass

            schema = {
                '_id': member.id,
                'banned_at': dt.utcnow(),
                'ban_duration': time or None,
                'banned_by': ctx.author.id,
                'guild_id': ctx.guild.id
            }

            await self.bot.bans.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
            self.bot.banned_users[member.id] = schema
            await member.ban(reason=reason)
            em = discord.Embed(
                description=f"{CHECK} Tempbanned {member.mention} lasting `{str(convert_time(time))}`"
                            f", for `{reason}`", timestamp=dt.utcnow(),
                colour=GREEN)
            em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
            await ctx.send(embed=em)

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
        if isinstance(member, discord.User):
            try:
                await ctx.guild.unban(member, reason=reason)

            except Exception:
                raise commands.MemberNotFound(member)

        elif isinstance(member, int):
            user = await self.bot.fetch_user(member)
            if not user:
                raise commands.MemberNotFound(member)

            try:
                await ctx.guild.unban(user, reason=reason)

            except Exception:
                raise commands.MemberNotFound(member)

        user = self.bot.get_user(member) or member

        await create_log(self.bot, user, ctx.guild, 'unban', ctx.author, reason)

        try:
            self.bot.banned_users.pop(user.id)

        except KeyError:
            pass

        em = discord.Embed(
            description=f"{CHECK} Unbanned {member.mention} for `{reason}`",
            timestamp=dt.utcnow(),
            colour=GREEN)
        em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
        await ctx.send(embed=em)

    @commands.command(
        name='warn',
        aliases=['w', 'wrn'],
        description='Warns members in the server. 3 second cooldown, must have Manage Messages permission.')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Warned {member.mention} for `{reason}`",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                await ctx.send(embed=em)
                try:
                    await send_punishment(self.bot, member, ctx.guild, 'warn', ctx.author, reason)

                except discord.Forbidden:
                    pass

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

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
        time = pytp.parse(args[0]) or None
        if not time:
            reason = ' '.join(args)

        else:
            reason = ' '.join(args[1:])
            if not reason:
                reason = 'no reason provided'

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role_id'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{SHARD} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=MAIN)
                msg = await ctx.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except KeyError:
            em = discord.Embed(
                description=f"{SHARD} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=MAIN)
            msg = await ctx.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if member is not ctx.guild.owner:
                    try:
                        if self.bot.muted_users[member.id]:
                            em = discord.Embed(
                                description=f"{ERROR} {member.mention} is already muted! "
                                            f"Talk about adding insult to injury.",
                                colour=RED)
                            return await ctx.send(embed=em)

                    except KeyError:
                        pass

                    schema = {
                        '_id': member.id,
                        'muted_at': dt.utcnow(),
                        'mute_duration': time or None,
                        'muted_by': ctx.author.id,
                        'guild_id': ctx.guild.id
                    }

                    await self.bot.mutes.update_one({"_id": member.id}, {'$set': schema}, upsert=True)
                    self.bot.muted_users[member.id] = schema
                    em = discord.Embed(
                        description=f"{CHECK} Muted {member.mention} lasting `{str(convert_time(time))}`"
                                    f", for `{reason}`", timestamp=dt.utcnow(),
                        colour=GREEN)
                    em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                    await ctx.send(embed=em)
                    await member.add_roles(
                        mute_role, reason=f'Muted by {ctx.author} lasting `{str(convert_time(time))}`'
                                          f', for {reason}.', atomic=True)

                    try:
                        await send_punishment(
                            self.bot, member, ctx.guild, 'mute', ctx.author, reason, convert_time(time))

                    except discord.Forbidden:
                        pass

                else:
                    raise RoleNotHighEnough

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

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
            mute_role = ctx.guild.get_role(data['mute_role_id'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{SHARD} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=MAIN)
                msg = await ctx.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except KeyError:
            em = discord.Embed(
                description=f"{SHARD} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=MAIN)
            msg = await ctx.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if self.bot.muted_users[member.id]:
                    em = discord.Embed(
                        description=f"{CHECK} Unmuted {member.mention} for `{reason}`",
                        timestamp=dt.utcnow(),
                        colour=GREEN)
                    em.set_footer(text=f"Case no. {await get_last_caseid(self.bot, ctx.guild)}")
                    await ctx.send(embed=em)

                    try:
                        await self.bot.mutes.delete_one({"_id": member.id})

                    except commands.MemberNotFound:
                        pass

                    try:
                        self.bot.muted_users.pop(member.id)

                    except KeyError:
                        pass

                    await member.remove_roles(mute_role, reason=reason)

                    try:
                        await send_punishment(self.bot, member, ctx.guild, 'unmute', ctx.author, reason)

                    except discord.Forbidden:
                        pass

                else:
                    em = discord.Embed(
                        description=f"{ERROR} {member.mention} is not muted.",
                        colour=RED)
                    return await ctx.send(embed=em)

            else:
                raise RoleNotHighEnough

        else:
            raise BotRoleNotHighEnough

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

        await channel.edit(slowmode_delay=time, reason='Slowmode delay edited by {ctx.author} via slowmode command')
        em = discord.Embed(
            description=f"{CHECK} Slowmode delay for {channel.mention} was set to `{str(convert_time(time))}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='purge',
        aliases=['p', 'prg', 'prune'])
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_cmd(self, ctx, limit: int, members: commands.Greedy[discord.User]):
        if 0 < limit < 1001:
            await ctx.message.delete()
            deleted = await ctx.channel.purge(
                limit=limit,
                after=dt.utcnow() - timedelta(days=14),
                check=lambda m: m.author in members or not len(members))

            if not len(deleted):
                em = discord.Embed(
                    description=f"{ERROR} Could not find any messages to delete.\n"
                                f"```Messages older than 2 weeks cannot be deleted```",
                    color=RED)
                return await ctx.send(embed=em)

            em = discord.Embed(
                description=f"{CHECK} Deleted {len(deleted, )} messages in {ctx.channel.mention}",
                color=GREEN)
            await ctx.send(embed=em, delete_after=2)

        else:
            em = discord.Embed(
                description=f"{ERROR} The limit provided is not within acceptable boundaries.\n"
                            f"```Limit must be in between 1 and 1000 messages```",
                color=RED)
            await ctx.send(embed=em)

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

        await member.move_to(channel=None, reason=reason)

        em = discord.Embed(
            description=f"{CHECK} Kicked {member.mention} from `{vc}`",
            color=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Mod(bot))
