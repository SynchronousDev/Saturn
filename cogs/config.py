import typing

from assets import *

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Config(commands.Cog):
    """
    The Configuration module. All commands that can help you set up or customize the bot are included here.

    This includes changing the prefix, setting moderator and muting roles, logging, and others.
    """

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.command != self.bot.get_command('prefixes'):
            if not ctx.guild:
                return False

            return ctx.author.guild_permissions.manage_guild

        else:
            if not ctx.invoked_subcommand:
                return True

            else:
                if not ctx.guild:
                    return False

                return ctx.author.guild_permissions.manage_guild

    @commands.group(
        name="prefixes",
        aliases=["pres", 'showprefixes'],
        description="Show the prefixes that the bot will respond to.",
        invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx):
        em = SaturnEmbed(
            title='Prefixes for {}'.format(ctx.guild),
            description=(
                '\n'.join('**{} - ** {}'.format(i, prefix)
                          for i, prefix in enumerate(
                    (await retrieve_prefix(self.bot, ctx)).split('|'), start=1))
            ),
            colour=MAIN,
            timestamp=utc()
        )
        em.set_footer(text='You can always invoke commands by mentioning me.')
        await ctx.send(embed=em)

    @prefix.command(
        name='addprefix',
        aliases=['addpre', 'add', 'append'],
        description='Add a prefix that the bot responds to.'
    )
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def _add_prefix(self, ctx, prefix):
        await ctx.invoke(self.bot.get_command('addprefix'), prefix=prefix)

    @prefix.command(
        name='removeprefix',
        aliases=['delprefix', 'delpre', 'removepre', 'remove'],
        description='Remove a prefix that the bot responds to.'
    )
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def _remove_prefix(self, ctx, prefix):
        await ctx.invoke(self.bot.get_command('removeprefix'), prefix=prefix)

    @commands.command(
        name='addprefix',
        aliases=['addpre'],
        description='Add a prefix that the bot responds to.'
    )
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def add_prefix(self, ctx, prefix):
        if prefix != "--":
            prefix = prefix.replace("--", " ")

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if prefix in flatten(data['prefix']):
                em = SaturnEmbed(
                    description=f"{ERROR} `{prefix}` is already a registered prefix.",
                    colour=RED)
                return await ctx.send(embed=em)

        except TypeError:
            pass

        if not data or not data['prefix']:
            prefixes = prefix

        else:
            prefixes = (data['prefix'], prefix)
            prefixes = flatten(prefixes)

        if len(prefixes) > 10:
            em = SaturnEmbed(
                description=f"{ERROR} Your guild does not have any prefixes!",
                colour=RED)
            return await ctx.send(embed=em)

        await self.bot.config.update_one({"_id": ctx.guild.id}, {'$set': {"prefix": prefixes}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} `{prefix}` has been added as a prefix.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='removeprefix',
        aliases=['delprefix', 'delpre', 'removepre'],
        description='Remove a prefix that the bot responds to.'
    )
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def remove_prefix(self, ctx, prefix):
        if prefix != "--":
            prefix = prefix.replace("--", " ")

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data or len(data['prefix']) < 1:
                em = SaturnEmbed(
                    description=f"{ERROR} Your guild does not have any prefixes!",
                    colour=RED)
                return await ctx.send(embed=em)

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{ERROR} Your guild does not have any prefixes!",
                colour=RED)
            return await ctx.send(embed=em)

        prefixes = data["prefix"]

        if isinstance(prefixes, str):
            pass
        else:
            try:
                prefixes.remove(prefix)

            except ValueError:
                em = SaturnEmbed(
                    description=f"{ERROR} `{prefix}` is not registered as a prefix.",
                    colour=RED)
                return await ctx.send(embed=em)

        await self.bot.config.update_one({"_id": ctx.guild.id}, {'$set': {"prefix": prefixes}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} `{prefix}` has been removed as a prefix.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='moderatorrole',
        aliases=['modrole', 'modr', 'mdr'],
        description='The command to change the settings for the moderator role. '
                    'This role will be able to access most moderation commands,'
                    'but individual commands can always be disabled later.',
        invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='modrole')

    @mod_role.command(
        name='set',
        aliases=['assign'],
        description='Sets the moderator role for your guild. This role will be able to access most moderation commands,'
                    'but individual commands can always be disabled later.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def set_moderator_role(self, ctx, role: discord.Role):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"mod_role": role.id}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} The moderator role has been assigned to {role.mention}",
            colour=GREEN)
        await ctx.send(embed=em)

    @mod_role.command(
        name='delete',
        aliases=['del', 'd'],
        description='Deletes the moderator role.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role_del(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['mod_role'])
            if not mod_role:
                em = SaturnEmbed(
                    description=f"{ERROR} The moderator role does not exist! "
                                f"Run `modrole set <role>` or `modrole create`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{ERROR} The moderator role does not exist! "
                            f"Run `modrole set <role>` or `modrole create`",
                colour=RED)
            await ctx.send(embed=em)
            return

        mod_role = ctx.guild.get_role(data['mod_role'])

        try:
            await mod_role.delete(reason=f'Moderator role deleted by {ctx.author.name} (ID {ctx.author.id})')

        except discord.Forbidden:
            em = SaturnEmbed(
                description=f"{ERROR} Sorry, I couldn't execute that action.\n"
                            f"```Moderator role is above my role```",
                colour=RED)
            await ctx.send(embed=em)
            return

        except discord.HTTPException:
            em = SaturnEmbed(
                description=f"{ERROR} Whoops! Something went wrong while executing that action.",
                colour=RED)
            await ctx.send(embed=em)
            return

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$unset': {"mod_role": None}})

        em = SaturnEmbed(
            description=f"{CHECK} The moderator role has been deleted.",
            colour=GREEN)
        await ctx.send(embed=em)

    @mod_role.command(
        name='create',
        aliases=['make', 'new'],
        description='Creates the moderator role.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role_create(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['mod_role'])
            if mod_role:
                em = SaturnEmbed(
                    description=f"{ERROR} The moderator role already exists"
                                f"Run `modrole set <role>` or `modrole delete`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except (TypeError, KeyError):
            pass

        perms = discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            manage_emojis=True,
            change_nickname=True,
            mute_members=True,
            deafen_members=True,
            move_members=True
        )
        mod_role = await ctx.guild.create_role(
            name='Moderator', permissions=perms, reason='Could not find a muted role')

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"mod_role": mod_role.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The moderator role was created.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='muterole',
        aliases=['mr'],
        description='The command to change the settings for the '
                    'muted role that the bot assigns to members upon a mute.',
        invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='muterole')

    @mute_role.command(
        name='set',
        aliases=['assign'],
        description='Sets the mute role to a role.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_set(self, ctx, role: discord.Role):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"mute_role": role.id}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} The mute role has been assigned to {role.mention}",
            colour=GREEN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='delete',
        aliases=['del', 'd'],
        description='Deletes the mute role.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_del(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role'])
            if not mute_role:
                em = SaturnEmbed(
                    description=f"{ERROR} The mute role does not exist! Run `muterole set <role>` or `muterole create`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{ERROR} The mute role does not exist! Run `muterole set <role>` or `muterole create`",
                colour=RED)
            await ctx.send(embed=em)
            return

        mute_role = ctx.guild.get_role(data['mute_role'])

        try:
            await mute_role.delete(reason=f'Mute role deleted by {ctx.author.name} (ID {ctx.author.id})')

        except discord.Forbidden:
            em = SaturnEmbed(
                description=f"{ERROR} Sorry, I couldn't execute that action.\n"
                            f"```Muted role is above my role```",
                colour=RED)
            await ctx.send(embed=em)
            return

        except discord.HTTPException:
            em = SaturnEmbed(
                description=f"{ERROR} Whoops! Something went wrong while executing that action.",
                colour=RED)
            await ctx.send(embed=em)
            return

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$unset': {"mute_role": None}})

        em = SaturnEmbed(
            description=f"{CHECK} The mute role has been deleted.",
            colour=GREEN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='create',
        aliases=['make', 'new'],
        description='Creates the mute role.')
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_create(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['mute_role'])
            if mod_role:
                em = SaturnEmbed(
                    description=f"{ERROR} The mute role already exists! Run `muterole set <role>` or `muterole delete`",
                    colour=RED)
                return await ctx.send(embed=em)

        except (TypeError, KeyError):
            pass

        perms = discord.Permissions(
            send_messages=False, read_messages=True)
        mute_role = await ctx.guild.create_role(name='Muted', colour=RED, permissions=perms,
                                                reason='Could not find a muted role')

        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(mute_role, read_messages=True, send_messages=False)

            except discord.Forbidden:
                continue

            except discord.HTTPException:
                continue

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"mute_role": mute_role.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The mute role was created.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='messagelogs',
        aliases=['msglogs'],
        description='The command to change the settings for the message log channel.',
    )
    async def message_logs(self, ctx, channel: discord.TextChannel):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"message_logs": channel.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The `message logs` channel was set to {channel.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='modlogs',
        aliases=['moderationlogs'],
        description='The command to change the settings for the moderation log channel.',
    )
    async def mod_logs(self, ctx, channel: discord.TextChannel):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"mod_logs": channel.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The `moderation logs` channel was set to {channel.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='memberlogs',
        aliases=['userlogs', 'memberlog', 'userlog'],
        description='The command to change the settings for the member log channel.',
        invoke_without_command=True
    )
    async def member_logs(self, ctx, channel: discord.TextChannel):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"member_logs": channel.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The `member logs` channel was set to {channel.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

    @member_logs.command(
        name='level',
        aliases=['levels', 'log', 'changelevel', 'setlevel'],
        description='Change the default levels of what member actions to log.'
    )
    async def change_log_level(self, ctx, level: typing.Optional[str]):
        if not level:
            # TODO: add option to customizably enable and disable logging features
            em = SaturnEmbed(
                description=f"""
                Each level has all the logging of the levels below it.
                
                `LOW - member join and leaves`
                `MEDIUM - role changes`
                `HIGH - nickname changes`
                `OFF - turn member logging off`
                """,
                colour=BLUE)
            em.set_author(name="Member Log Levels",
                          icon_url=INFO_URL)
            return await ctx.send(embed=em)

        if level.lower() not in ('low', 'medium', 'high', 'off'):
            em = SaturnEmbed(
                description=f"{ERROR} Invalid level given."
                            f"```Choose between LOW, MEDIUM, HIGH and OFF```",
                colour=RED
            )
            await ctx.send(embed=em)

        else:
            await self.bot.config.update_one(
                {"_id": ctx.guild.id}, {'$set': {"member_log_level": level.upper()}}, upsert=True)
            em = SaturnEmbed(
                description=f"{CHECK} The `member logs` level was set to `{level.upper()}`",
                colour=GREEN)
            await ctx.send(embed=em)

    @member_logs.command(
        name='current',
        aliases=['show'],
        description="Show the current member log level."
    )
    async def show_member_log_level(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            member_log_level = data['member_log_level']

        except (TypeError, KeyError): member_log_level = "HIGH"

        em = SaturnEmbed(
            description=f"{INFO} The member logs level is currently set to `{member_log_level.upper()}`\n"
                        f"```Set the member log level via the memberlogs level command```",
            colour=BLUE)
        await ctx.send(embed=em)

    @commands.command(
        name='automod',
        aliases=['auto-moderation', 'amod', 'automoderation'],
        description='The command to change the settings for the automod log channel.',
    )
    async def auto_mod_logs(self, ctx, channel: discord.TextChannel):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"automod_logs": channel.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The `automod logs` channel was set to {channel.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='starboard',
        aliases=['star', 'sboard'],
        description='The command to change the settings for the starboard.',
        invoke_without_command=True
    )
    async def star_board(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='starboard')

    @star_board.command(
        name='set',
        aliases=['assign'],
        description='Set the starboard channel to a channel.'
    )
    async def set_starboard(self, ctx, channel: discord.TextChannel):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"starboard": channel.id}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} The `starboard` channel was set to {channel.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

    @star_board.command(
        name='stars',
        aliases=['count', 'star'],
        description='Set the required number of stars needed to get a message to the starboard.'
    )
    async def set_starboard_stars(self, ctx, stars: int):
        if stars < 2:
            em = SaturnEmbed(
                description=f"{ERROR} Minimum number of stars cannot be less than 2.",
                colour=RED)
            return await ctx.send(embed=em)

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"count": stars}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} Messages now require `{stars}` stars to get on the starboard.",
            colour=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Config(bot))