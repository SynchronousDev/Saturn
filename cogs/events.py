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


def setup(bot):
    bot.add_cog(Events(bot))
