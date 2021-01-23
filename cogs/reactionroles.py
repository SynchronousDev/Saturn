import typing as t
import discord
from discord.ext import commands
import emojis

from utils import *


class ReactionRoles(commands.Cog, name='Reaction Roles'):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
