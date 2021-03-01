from discord import Embed
from assets import *
from discord.ext import commands, tasks
import traceback
import sys
import random
import DiscordUtils
from glob import glob

log = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_messages = [
            "Too fast!",
            "Woah, too quick there!",
            "Slow down!",
            "This command's on cooldown!",
            "Why do I hear boss music?",
            "Take a chill pill!"
        ]
        self.tracker = DiscordUtils.InviteTracker(self.bot)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.tracker.cache_invites()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.tracker.update_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.tracker.update_guild_cache(guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.tracker.remove_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.tracker.remove_guild_cache(guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content == f"<@!{self.bot.user.id}>":
            em = discord.Embed(
                description=f":bell: The prefix for `{message.guild}` is currently "
                            f"set to `{await retrieve_prefix(self.bot, message)}`",
                color=GOLD)
            await message.channel.send(embed=em)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            inviter = await self.tracker.fetch_inviter(member)
            guild = member.guild
            try:
                if self.bot.muted_users[member.id]:
                    data = await self.bot.config.find_one({"_id": guild.id})
                    mute_role = guild.get_role(data['mute_role_id'])
                    if mute_role:
                        await member.add_roles(mute_role, reason='Role Persists', atomic=True)

            except KeyError:
                pass

            data = await self.bot.config.find_one({"_id": guild.id})
            member_logs = None
            try:
                member_logs = member.guild.get_channel(data['member_logs'])

            except TypeError:
                return

            except KeyError:
                return

            if not member_logs:
                return

            em = discord.Embed(
                title='Member Joined',
                description=f"{member.mention} `({member})`",
                colour=GREEN,
                timestamp=dt.utcnow()
            )
            em.set_thumbnail(url=member.avatar_url)
            em.set_footer(text=f"Member no. {len(guild.members)} | Invited by {inviter}")
            await member_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            data = await self.bot.config.find_one({"_id": member.guild.id})
            member_logs = None
            try:
                member_logs = member.guild.get_channel(data['member_logs'])

            except TypeError:
                return

            except KeyError:
                return

            if not member_logs:
                return

            em = discord.Embed(
                title='Member Left',
                description=f"{member.mention} `({member})`",
                colour=RED,
                timestamp=dt.utcnow()
            )
            em.set_thumbnail(url=member.avatar_url)
            em.set_footer(text=f"Only {len(member.guild.members)} members left in {member.guild}")
            await member_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        Fires when a message is deleted
        """
        self.bot.snipes[message.id] = {
            "_id": message.id,
            "author": message.author.id,
            "content": message.content,
            "guild": message.guild.id,
            "time": dt.utcnow()
        }
        if not message.author.bot:
            data = await self.bot.config.find_one({"_id": message.guild.id})
            try:
                message_logs = message.guild.get_channel(data['message_logs'])

            except KeyError:
                return

            em = discord.Embed(
                title='Message Deleted',
                colour=RED,
                timestamp=dt.utcnow()
            )
            em.set_thumbnail(url=message.author.avatar_url)
            em.add_field(name="Author", value=message.author.mention)
            em.add_field(name="Channel", value=f"{message.channel.mention} `(#{message.channel})`")
            em.add_field(name="Content", value=f"{message.content}", inline=False)
            em.set_footer(text=f"Message ID - {message.id}")
            await message_logs.send(embed=em)  # send the embed

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.author.bot:
            """
            Fires when a message is edited
            """
            data = await self.bot.config.find_one({"_id": after.guild.id})
            try:
                message_logs = after.guild.get_channel(data['message_logs'])

            except KeyError:
                return

            em = discord.Embed(
                title='Message Edited',
                description=f"[Jump!](https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id})",
                colour=GOLD,
                timestamp=dt.utcnow()
            )
            em.set_thumbnail(url=after.author.avatar_url)
            em.add_field(name="Author", value=after.author.mention)
            em.add_field(name="Channel", value=f"{after.channel.mention} `(#{after.channel})`")
            em.add_field(name="Before", value=f"{before.content}", inline=False)
            em.add_field(name="After", value=f"{after.content}", inline=False)
            em.set_footer(text=f"Message ID - {after.id}")  # footer because why not
            await message_logs.send(embed=em)  # send the embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "⭐":
            message = await (self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).
                             fetch_message(payload.message_id))

            data = await self.bot.config.find_one({"_id": message.guild.id})
            _starboard = await self.bot.starboard.find_one({"_id": message.id})
            if not _starboard:
                stars, msg_id = 0, None

            else:
                try:
                    stars, msg_id = _starboard['stars'], _starboard['star_id']

                except KeyError:
                    stars, msg_id = 0, None

            try:
                starboard = message.guild.get_channel(data['starboard'])

            except KeyError:
                return

            em = discord.Embed(
                colour=GOLD,
                description=f"{message.content}",
                timestamp=dt.utcnow()
            )
            em.add_field(name='Original Message', value=f"[Jump!](https://discord.com/channels/"
                                                        f"{payload.guild_id}/{payload.channel_id}/{message.id})")

            if len(message.attachments):
                attachment = message.attachments[0]

                em.add_field(name='Attachments', value=f"[{attachment.filename}]({attachment.url})", inline=False)
                em.set_image(url=attachment.url)

            em.set_author(icon_url=message.author.avatar_url, name=message.author)
            em.set_footer(text=f'Message ID - {message.id}')

            if not stars:
                msg = await starboard.send(
                    content=f"**{stars + 1}** ✨ - **{message.channel.mention}**", embed=em)
                schema = {
                    '_id': message.id,
                    'stars': stars + 1,
                    'star_id': msg.id
                }
                await self.bot.starboard.insert_one(schema)

            else:
                msg = await (self.bot.get_guild(message.guild.id).get_channel(starboard.id).
                             fetch_message(msg_id))
                await msg.edit(
                    content=f"**{stars + 1}** ✨ - **{message.channel.mention}**", embed=em)
                await self.bot.starboard.update_one(
                    {'_id': message.id}, {'$set': {'stars': stars + 1, 'star_id': msg.id}})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.emoji.name == "⭐":
            message = await (self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).
                             fetch_message(payload.message_id))
            data = await self.bot.config.find_one({"_id": message.guild.id})
            _starboard = await self.bot.starboard.find_one({"_id": message.id})
            if not _starboard:  # check if there are stars on that message
                return

            else:
                try:
                    stars, msg_id = _starboard['stars'], _starboard['star_id']

                except KeyError:
                    return  # only if the the stars or star_id param doesn't exist

            try:
                starboard = message.guild.get_channel(data['starboard'])

            except KeyError:
                return

            em = discord.Embed(
                colour=GOLD,
                description=f"{message.content}",
                timestamp=dt.utcnow()
            )
            em.add_field(name='Original Message', value=f"[Jump!](https://discord.com/channels/"
                                                        f"{payload.guild_id}/{payload.channel_id}/{message.id})")

            if len(message.attachments):
                attachment = message.attachments[0]

                em.add_field(name='Attachments', value=f"[{attachment.filename}]({attachment.url})", inline=False)
                em.set_image(url=attachment.url)

            em.set_author(icon_url=message.author.avatar_url, name=message.author)
            em.set_footer(text=f'Message ID - {message.id}')

            msg = await (self.bot.get_guild(message.guild.id).get_channel(starboard.id).
                         fetch_message(msg_id))
            if stars - 1 < 1:
                await msg.delete()
                await self.bot.starboard.delete_one({'_id': message.id})

            else:
                await msg.edit(
                        content=f"**{stars - 1}** ✨ - **{message.channel.mention}**", embed=em)
                await self.bot.starboard.update_one(
                    {'_id': message.id}, {'$set': {'stars': stars - 1, 'star_id': msg.id}}, upsert=True)

def setup(bot):
    bot.add_cog(Events(bot))  # add this stupid cog i'm tired
