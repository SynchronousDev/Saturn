import DiscordUtils
from better_profanity import profanity

from assets import *

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
            try:
                em = discord.Embed(
                    description=f":bell: The prefix(es) for `{message.guild}` is currently "
                                f"set to `{await retrieve_prefix(self.bot, message)}`",
                    color=GOLD)
                await message.channel.send(embed=em)

            except TypeError:
                em = discord.Embed(
                    description=f":bell: Your guild does not have any set prefixes!",
                    color=GOLD)
                await message.channel.send(embed=em)

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

        except KeyError:
            pass

        if not member.bot:
            inviter = await self.tracker.fetch_inviter(member)  # get the inviter of the member
            guild = member.guild
            data = await self.bot.config.find_one({"_id": guild.id})
            try:
                member_logs = member.guild.get_channel(data['member_logs'])

            except TypeError or KeyError: return
            if not member_logs: return

            em = discord.Embed(
                title='Member Joined',
                description=f"{member.mention} `({member})`",
                colour=GREEN,
                timestamp=dt.utcnow()
            )
            em.set_thumbnail(url=member.avatar_url)
            em.add_field(name='Account Created At', value=str(member.created_at)[:-16])
            em.set_footer(text=f"Member no. {len(guild.members)} | Invited by {inviter}")
            await member_logs.send(embed=em)  # send the member embed thing

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        Fires when a member leaves the server
        """
        if not member.bot:
            data = await self.bot.config.find_one({"_id": member.guild.id})
            try:
                member_logs = member.guild.get_channel(data['member_logs'])

            except TypeError or KeyError: return
            if not member_logs: return

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
        if not message.author.bot:
            profanity.load_censor_words()
            if profanity.contains_profanity(message.content): return
            schema = {
                "_id": message.id,
                "channel": message.channel.id,
                "author": message.author.id,
                "content": message.content,
                "guild": message.guild.id,
                "time": dt.utcnow()
            }
            self.bot.snipes[message.id] = schema

            data = await self.bot.config.find_one({"_id": message.guild.id})
            try:
                message_logs = message.guild.get_channel(data['message_logs'])

            except KeyError or TypeError:
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
        """
        Fires when a message is edited
        """

        if not after.author.bot:
            profanity.load_censor_words()
            if profanity.contains_profanity(after.content):
                await after.delete()
                return await after.channel.send("That word is not allowed in **{}**".format(after.guild))

            schema = {
                "_id": after.id,
                "channel": after.channel.id,
                "author": after.author.id,
                "before": before.content,
                "after": after.content,
                "guild": after.guild.id,
                "time": dt.utcnow()
            }
            self.bot.edit_snipes[after.id] = schema

            data = await self.bot.config.find_one({"_id": after.guild.id})
            try:
                message_logs = after.guild.get_channel(data['message_logs'])

            except KeyError or TypeError:
                return

            em = discord.Embed(
                title='Message Edited',
                description=f"[Jump!]({after.jump_url})",
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
        if payload.emoji.name == "⭐":  # check if the emoji is a star for the starboard stuff
            message = await (self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).
                             fetch_message(payload.message_id))

            data = await self.bot.config.find_one({"_id": message.guild.id})
            try:
                if not data['starboard']:
                    return

            except KeyError or TypeError:
                return

            count = data['count'] or 3

            _starboard = await self.bot.starboard.find_one({"_id": message.id})
            stars = 0
            msg_id = None
            if not _starboard:
                schema = {
                    '_id': message.id,
                    'stars': 0,
                }
                await self.bot.starboard.insert_one(schema)

            try:
                stars = _starboard['stars']
                msg_id = _starboard['star_id']

            except KeyError:
                msg_id = None

            except TypeError:
                stars = 0

            starboard = message.guild.get_channel(data['starboard'])
            if not starboard:
                return

            em = starboard_embed(message, payload)
            schema = {
                '_id': message.id,
                'stars': stars + 1,
            }
            await self.bot.starboard.update_one(
                {"_id": message.id}, {'$set': schema}, upsert=True)

            if stars + 1 >= count:
                if msg_id:
                    msg = await (self.bot.get_guild(message.guild.id).get_channel(starboard.id).
                                 fetch_message(msg_id))
                    await msg.edit(
                        content=f"**{stars + 1}** ✨ - **{message.channel.mention}**", embed=em)

                else:
                    msg = await starboard.send(
                        content=f"**{stars + 1}** ✨ - **{message.channel.mention}**", embed=em)
                    await self.bot.starboard.update_one(
                        {"_id": message.id}, {'$set': {"star_id": msg.id}}, upsert=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.emoji.name == "⭐":
            message = await (self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).
                             fetch_message(payload.message_id))
            data = await self.bot.config.find_one({"_id": message.guild.id})
            try:
                if not data['starboard']:
                    return

            except KeyError or TypeError:
                return

            _starboard = await self.bot.starboard.find_one({"_id": message.id})
            count = data['count'] or 3
            try:
                stars = _starboard['stars']

            except KeyError or TypeError:
                return

            try:
                msg_id = _starboard['star_id']
            except KeyError:
                msg_id = None

            if not _starboard:  # check if there are stars on that message
                return

            starboard = message.guild.get_channel(data['starboard'])
            if not starboard:
                return

            em = starboard_embed(message, payload)

            await self.bot.starboard.update_one(
                {'_id': message.id}, {'$set': {'stars': stars - 1}}, upsert=True)

            if msg_id and (stars - 1) < count:
                msg = await (self.bot.get_guild(message.guild.id).get_channel(starboard.id).
                             fetch_message(msg_id))
                await self.bot.starboard.update_one(
                    {'_id': message.id}, {
                        '$set': {
                            'stars': stars - 1, 'star_id': None
                        }
                    }, upsert=True)
                return await msg.delete()

            if stars < 1:
                return await self.bot.starboard.delete_one({'_id': message.id})

            else:
                if msg_id:
                    msg = await (self.bot.get_guild(message.guild.id).get_channel(starboard.id).
                                 fetch_message(msg_id))
                    await msg.edit(
                        content=f"**{stars - 1}** ✨ - **{message.channel.mention}**", embed=em)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        data = await self.bot.config.find_one({"_id": after.guild.id})
        try:
            if not data['mute_role']: return
        except TypeError or KeyError: return

        mute_role = after.guild.get_role(data['mute_role'])

        if (mute_role in before.roles) and (mute_role not in after.roles):
            try:
                await self.bot.mutes.delete_one({"_id": after.id})
                self.bot.muted_users.pop(after.id)

            except commands.MemberNotFound or KeyError:
                pass


def setup(bot):
    bot.add_cog(Events(bot))  # add this stupid cog i'm tired
