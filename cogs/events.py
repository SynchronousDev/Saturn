from discord import Embed
from assets import *
from discord.ext import commands
import traceback
import sys
import random

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
        # member logs: 812881787112914954
        # message logs 812881774073479178
        # mod logs: 812881839902949478

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
        member_logs = guild.get_channel(data['member_logs'])

        em = discord.Embed(
            title='Member Joined',
            description=f"{member.mention} `({member})`",
            colour=GREEN,
            timestamp=dt.utcnow()
        )
        em.set_thumbnail(url=member.avatar_url)
        em.set_footer(text=f"Member no. {len(guild.members)} | ID - {member.id}")
        await member_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        pass

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
            message_logs = message.guild.get_channel(data['message_logs'])
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
            try:
                await message_logs.send(embed=em)  # send the embed

            except Exception as e:
                pass

            # I had some issues with how on_message_delete and on_mesage_edit are triggered
            # cough cough discord
            # needed to check if the message was sent by a bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.author.bot:
            """
            Fires when a message is edited
            """
            data = await self.bot.config.find_one({"_id": after.guild.id})
            message_logs = after.guild.get_channel(data['message_logs'])
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
            try:
                await message_logs.send(embed=em)  # send the embed

            except Exception as e:
                pass

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        data = await self.bot.config.find_one({"_id": member.guild.id})
        member_logs = member.guild.get_channel(data['member_logs'])

        em = discord.Embed(
            title='Member Left',
            description=f"{member.mention} `({member})`",
            colour=RED,
            timestamp=dt.utcnow()
        )
        em.set_thumbnail(url=member.avatar_url)
        em.set_footer(text=f"ID - {member.id}")
        await member_logs.send(embed=em)


def setup(bot):
    bot.add_cog(Events(bot))  # add this stupid cog i'm tired
