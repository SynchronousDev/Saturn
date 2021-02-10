from assets.utils import *

log = logging.getLogger(__name__) 

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @commands.command(
        name="prefix",
        aliases=["changeprefix", "setprefix", 'pre'],
        description="Change your guild's prefix.")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx, *, prefix="sl!"):
        await self.bot.config.update_one({"_id": ctx.guild.id}, {'$set': {"prefix": prefix}}, upsert=True)
        em = discord.Embed(
                description=f"{CHECK} Prefix has been set to `{prefix}`",
                colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='deleteprefix',
        aliases=['dp', 'delpre'],
        description="Delete your guild's prefix.")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def deleteprefix(self, ctx):
        await self.bot.config.update_one({"_id": ctx.guild.id}, {"$unset": {"prefix": 1}})
        em = discord.Embed(
                description=f"{CHECK} Prefix has been reset to the default `sl!`",
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
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='modrole')

    @mod_role.command(
        name='set',
        aliases=['assign'],
        description='Sets the moderator role for your guild. This role will be able to access most moderation commands,'
                    'but individual commands can always be disabled later.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def set_moderator_role(self, ctx, role: discord.Role):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"moderator_role_id": role.id}}, upsert=True)
        em = discord.Embed(
            description=f"{CHECK} The moderator role has been assigned to {role.mention}",
            colour=GREEN)
        await ctx.send(embed=em)

    @mod_role.command(
        name='delete',
        aliases=['del', 'd'],
        description='Deletes the moderator role.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role_del(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['moderator_role_id'])
            if not mod_role:
                em = discord.Embed(
                    description=f"{ERROR} The moderator role does not exist! "
                                f"Run `modrole set <role>` or `modrole create`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except KeyError:
            em = discord.Embed(
                description=f"{ERROR} The moderator role does not exist! "
                            f"Run `modrole set <role>` or `modrole create`",
                colour=RED)
            await ctx.send(embed=em)
            return

        mod_role = ctx.guild.get_role(data['moderator_role_id'])

        try:
            await mod_role.delete(reason=f'Moderator role deleted by {ctx.author.name} (ID {ctx.author.id})')

        except discord.Forbidden:
            em = discord.Embed(
                description=f"{ERROR} Sorry, I couldn't execute that action.\n"
                            f"```Moderator role is above my role```",
                colour=RED)
            await ctx.send(embed=em)
            return

        except discord.HTTPException:
            em = discord.Embed(
                description=f"{ERROR} Whoops! Something went wrong while executing that action.",
                colour=RED)
            await ctx.send(embed=em)
            return

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$unset': {"moderator_role_id": None}})

        em = discord.Embed(
            description=f"{CHECK} The moderator role has been deleted.",
            colour=GREEN)
        await ctx.send(embed=em)

    @mod_role.command(
        name='create',
        aliases=['make', 'new'],
        description='Creates the moderator role.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mod_role_create(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['moderator_role_id'])
            if mod_role:
                em = discord.Embed(
                    description=f"{ERROR} The moderator role already exists"
                                f"Run `modrole set <role>` or `modrole delete`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except KeyError:
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
        mod_role = await ctx.guild.create_role(name='Moderator', permissions=perms,
                                    reason='Could not find a muted role')

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"moderator_role_id": mod_role.id}}, upsert=True)

        em = discord.Embed(
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
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='muterole')

    @mute_role.command(
        name='set',
        aliases=['assign'],
        description='Sets the mute role to a role.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_set(self, ctx, role: discord.Role):
        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$set': {"mute_role_id": role.id}}, upsert=True)
        em = discord.Embed(
            description=f"{CHECK} The mute role has been assigned to {role.mention}",
            colour=GREEN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='delete',
        aliases=['del', 'd'],
        description='Deletes the mute role.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_del(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mute_role = ctx.guild.get_role(data['mute_role_id'])
            if not mute_role:
                em = discord.Embed(
                    description=f"{ERROR} The mute role does not exist! Run `muterole set <role>` or `muterole create`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except KeyError:
            em = discord.Embed(
                description=f"{ERROR} The mute role does not exist! Run `muterole set <role>` or `muterole create`",
                colour=RED)
            await ctx.send(embed=em)
            return

        mute_role = ctx.guild.get_role(data['mute_role_id'])

        try:
            await mute_role.delete(reason=f'Mute role deleted by {ctx.author.name} (ID {ctx.author.id})')

        except discord.Forbidden:
            em = discord.Embed(
                description=f"{ERROR} Sorry, I couldn't execute that action.\n"
                            f"```Muted role is above my role```",
                colour=RED)
            await ctx.send(embed=em)
            return

        except discord.HTTPException:
            em = discord.Embed(
                description=f"{ERROR} Whoops! Something went wrong while executing that action.",
                colour=RED)
            await ctx.send(embed=em)
            return

        await self.bot.config.update_one(
            {"_id": ctx.guild.id}, {'$unset': {"mute_role_id": None}})

        em = discord.Embed(
                description=f"{CHECK} The mute role has been deleted.",
                colour=GREEN)
        await ctx.send(embed=em)

    @mute_role.command(
        name='create',
        aliases=['make', 'new'],
        description='Creates the mute role.')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def mute_role_create(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            mod_role = ctx.guild.get_role(data['mute_role_id'])
            if mod_role:
                em = discord.Embed(
                    description=f"{ERROR} The mute role already exists! Run `muterole set <role>` or `muterole delete`",
                    colour=RED)
                await ctx.send(embed=em)
                return

        except KeyError:
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

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"mute_role_id": mute_role.id}}, upsert=True)

        em = discord.Embed(
                description=f"{CHECK} The mute role was created.",
                colour=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Config(bot))
