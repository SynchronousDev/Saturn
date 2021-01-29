import typing as t
from copy import deepcopy
from dateutil.relativedelta import relativedelta

from discord.ext import tasks
from assets import *
import pytimeparse as pytp


class Mod(commands.Cog, name='Moderation'):
    def __init__(self, bot):
        self.bot = bot
        self.mute_task = self.check_mutes.start()

    def cog_unload(self):
        self.mute_task.cancel()

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
                try:
                    await self.bot.mutes.delete_one({"_id": member.id})

                except discord.MemberNotFound:
                    pass

                if mute_role in member.roles:
                    await member.remove_roles(mute_role, reason='Mute time expired', atomic=True)

                else:
                    pass

                try:
                    self.bot.muted_users.pop(member.id)

                except KeyError:
                    pass

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.bot.wait_until_ready()

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
                em = discord.Embed(
                    description=f"{CHECK} Kicked {member.mention} for `{reason}`.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                await send_punishment(member, ctx.guild, 'kick', ctx.author, reason)
                await member.kick(reason=reason)

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
        name='ban',
        aliases=['b'],
        description='Bans members from the server. 5 second cooldown, must have Ban Members permission.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Banned {member.mention} for `{reason}`.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                await send_punishment(member, ctx.guild, 'ban', ctx.author, reason)
                await member.ban(reason=reason)
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
        name='warn',
        aliases=['w', 'wrn'],
        description='Warns members in the server. 5 second cooldown, must have Manage Messages permission.')
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason provided"):
        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                em = discord.Embed(
                    description=f"{CHECK} Warned {member.mention} for `{reason}`.",
                    timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                try:
                    await send_punishment(member, ctx.guild, 'warn', ctx.author, reason)

                except discord.Forbidden:
                    pass

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
        name='mute',
        aliases=['m', 'silence'],
        description='Mutes users in the server. '
                    '3 second cooldown, must have Manage Messages permission. Cannot be bypassed.')
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    async def mute_cmd(self, ctx, member: discord.Member, *args):
        time = pytp.parse(args[0]) or None
        if not time:
            reason = ' '.join(args)

        else:
            reason = ' '.join(args[1:])
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role_id'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{LOADING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=MAIN)
                msg = await ctx.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except KeyError:
            em = discord.Embed(
                description=f"{LOADING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=MAIN)
            msg = await ctx.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                try:
                    if self.bot.muted_users[member.id]:
                        em = discord.Embed(
                            description=f"{ERROR} {member.mention} is already muted! "
                                        f"Talk about adding insult to injury.",
                            colour=RED)
                        await ctx.send(embed=em)
                        return

                except KeyError:
                    pass

                data = {
                    '_id': member.id,
                    'muted_at': dt.utcnow(),
                    'mute_duration': time or None,
                    'muted_by': ctx.author.id,
                    'guild_id': ctx.guild.id
                }
                await self.bot.mutes.update_one({"_id": member.id}, {'$set': data}, upsert=True)
                self.bot.muted_users[member.id] = data
                em = discord.Embed(
                    description=f"{CHECK} Muted {member.mention} lasting {str(convert_time(time))}"
                                f", for `{reason}`.", timestamp=dt.utcnow(),
                    colour=GREEN)
                await ctx.send(embed=em)
                await member.add_roles(mute_role, reason=f'Muted by {ctx.author} lasting {str(convert_time(time))}'
                                                         f', for {reason}.', atomic=True)

                try:
                    await send_punishment(member, ctx.guild, 'mute', ctx.author, reason, convert_time(time))

                except discord.Forbidden:
                    pass

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
        name='unmute',
        aliases=['um', 'umt', 'unm'],
        description='Unmutes members in the server. 3 second cooldown, must have Manage Messages permission.')
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    async def unmute_cmd(self, ctx, member: discord.Member,
                         *, reason: t.Optional[str] = 'no reason provided'):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role_id'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{LOADING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                    colour=MAIN)
                msg = await ctx.send(embed=em)

                mute_role = await create_mute_role(self.bot, ctx)

                await msg.delete()

        except KeyError:
            em = discord.Embed(
                description=f"{LOADING} Couldn't find a mute role to assign to {member.mention}, making one now...",
                colour=MAIN)
            msg = await ctx.send(embed=em)

            mute_role = await create_mute_role(self.bot, ctx)

            await msg.delete()

        if ctx.guild.me.top_role > member.top_role:
            if ctx.author.top_role > member.top_role:
                if mute_role in member.roles:
                    em = discord.Embed(
                        description=f"{CHECK} Unmuted {member.mention} for `{reason}`.",
                        timestamp=dt.utcnow(),
                        colour=GREEN)
                    await ctx.send(embed=em)

                    try:
                        await self.bot.mutes.delete_one({"_id": member.id})

                    except discord.MemberNotFound:
                        pass

                    try:
                        self.bot.muted_users.pop(member.id)

                    except KeyError:
                        pass

                    await member.remove_roles(mute_role, reason=reason)

                    try:
                        await send_punishment(member, ctx.guild, 'unmute', ctx.author, reason)

                    except discord.Forbidden:
                        pass

                else:
                    em = discord.Embed(
                        description=f"{ERROR} {member.mention} is not muted.",
                        colour=RED)
                    await ctx.send(embed=em)
                    return

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


def setup(bot):
    bot.add_cog(Mod(bot))
