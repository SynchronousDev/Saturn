from assets import *
from discord.ext import commands

class ReactionRoles(commands.Cog, name='Reaction Roles'):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
