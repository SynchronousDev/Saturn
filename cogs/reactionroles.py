import typing as t
import discord
from discord.ext import commands
import emojis

from utils import *


class ReactionRolesNotSetup(commands.CommandError):
    """Reaction Roles are not set up for this guild."""
    pass


def is_setup():
    async def wrap_func(ctx):
        data = await ctx.bot.config.find_by_id(ctx.guild.id)
        if data is None:
            raise ReactionRolesNotSetup

        if data.get("message_id") is None:
            raise ReactionRolesNotSetup

        return True

    return commands.check(wrap_func)


class ReactionRoles(commands.Cog, name='Reaction Roles'):
    def __init__(self, bot):
        self.bot = bot

    async def get_current_reactions(self, guild_id):
        data = await self.bot.reaction_roles.get_all()
        data = filter(lambda r: r['guild_id'] == guild_id, data)
        data = map(lambda r: r["_id"], data)
        return list(data)

    async def rebuild_rr_embed(self, guild_id):
        data = await self.bot.config.find(guild_id)
        channel_id = data["channel_id"]
        message_id = data["message_id"]

        guild = await self.bot.get_guild(guild_id)
        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        em = discord.Embed(
            title=data["title"],
            colour=MAIN,
            timestamp=dt.utcnow())
        await message.clear_reactions()

        description = ""
        reaction_roles = await self.bot.reaction_roles.get_all()
        reaction_roles = list(filter(lambda r: r['guild_id'] == guild_id, reaction_roles))
        for reaction in reaction_roles:
            role = guild.get_role(reaction["role"])
            description += f"{item['_id']} - {role.mention}\n"
            await message.add_reaction(item['_id'])

        em.description = description
        await message.edit(embed=em)

    @commands.group(
        name='reactionroles',
        aliases=['rr'], descrption='The reaction roles group.',
        invoke_without_command=True)
    @commands.guild_only()
    async def rr_cmd(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity='reactionroles')

    @rr_cmd.command(
        name='channel',
        aliases=['chnnl', 'chnl', 'ch'],
        description='Sets the reaction role\'s channel.')
    async def rr_channel(self, ctx, channel: t.Optional[discord.TextChannel], *, title: t.Optional[str]):
        if not channel:
            em = discord.Embed(
                description=f"{ERROR} A channel was not provided, so I'm going to be "
                            f"using the current channel ({ctx.channel.mention})!",
                colour=RED)
            await ctx.send(embed=em)

        channel = channel or ctx.channel
        try:
            await channel.send("This is an automated message sent by me to set up reaction roles. "
                               "Do not worry, this will be deleted soon.",
                               delete_after=2)

        except discord.HTTPException:
            em = discord.Embed(
                description=f"{ERROR} Unable to send messages to {ctx.channel.mention}. "
                            f"Please update the permissions for that channel.",
                colour=RED)
            await ctx.send(embed=em)

        em = discord.Embed(
            title=title,
            colour=MAIN,
            timestamp=dt.now())

        description = ""
        reaction_roles = await self.bot.reaction_roles.get_all()
        reaction_roles = list(filter(lambda r: r['guild_id'] == ctx.guild.id, reaction_roles))

        for item in reaction_roles:
            role = ctx.guild.get_role(item["role"])
            description += f"{item['_id']} - {role.mention}"

        em.description = description

        msg = await channel.send(embed=em)

        for item in reaction_roles:
            await msg.add_reaction(item["_id"])

        await self.bot.config.upsert(
            {
                "_id": ctx.guild.id,
                "message_id": msg.id,
                "channel_id": msg.channel.id,
                "title": title,
                "is_enabled": True
            })

        em = discord.Embed(
            description=f"{CHECK} Reaction roles have been setup in {channel.mention}",
            colour=MAIN)
        await ctx.send(embed=em)

    @rr_cmd.command(
        name='toggle',
        aliases=['tg', 't'],
        description='Toggles reaction roles for the guild.')
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    @is_setup()
    async def rr_toggle(self, ctx):
        data = await self.bot.config.find(ctx.guild.id)
        data["is_enabled"] = not data["is_enabled"]
        await self.bot.config.upsert(data)

        mode = 'enabled' if data["is_enabled"] else 'disabled'
        em = discord.Embed(
            description=f"{CHECK} Reaction roles are now `{mode}`",
            colour=MAIN)
        await ctx.send(embed=em)

    @rr_cmd.command(
        name='add',
        description='Add a new reaction role.')
    @commands.guild_only()
    @is_setup()
    async def rr_add(self, ctx, emoji: str, *, role: discord.Role):
        reactions = await self.get_current_reactions(ctx.guild.id)
        if len(reactions) >= 20:
            em = discord.Embed(
                description=f"{ERROR} The number of reactions on that message is at the limit.",
                colour=RED)
            await ctx.send(embed=em)
            return

        if not isinstance(emoji, discord.Emoji):
            emoji = emojis.get(emoji)
            emoji = emoji.pop()

        elif isinstance(emoji, discord.Emoji):
            if not emoji.is_usable():
                em = discord.Embed(
                    description=f"{ERROR} Unable to use that emoji.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        emoji = str(emoji)
        await self.bot.reaction_roles.upsert(
            {
                "_id": emoji,
                "role": role.id,
                'guild_id': ctx.guild.id
            }
        )

        await self.rebuild_rr_embed(ctx.guild.id)
        em = discord.Embed(
            description=f"{CHECK} Added that emoji for {role.mention}",
            colour=MAIN)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(ReactionRoles(bot))
