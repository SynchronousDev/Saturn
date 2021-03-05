from assets import *
from discord.ext import commands
from better_profanity import profanity
import re

log = logging.getLogger(__name__)


class AutoMod(commands.Cog, name='Auto Moderation'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        profanity.load_censor_words()
        msg = message.content.lower()

        # anti profanity
        if (
            profanity.contains_profanity(msg) or  # message just has plain profanity
            profanity.contains_profanity(msg.replace(' ', '')) or  # message has spaces and remove the spaces
            profanity.contains_profanity(re.sub(r'[^\w\s]', '', msg)) or  # message has punctuation, remove punctuation
            profanity.contains_profanity(msg.replace('­', ''))  # message has invisible unicode character
        ):
            await message.delete()
            await message.channel.send(
                "{}, That word is not allowed in **{}**!".format(message.author.mention, message.guild))

    @commands.group(
        name='profanity',
        aliases=['prof', 'swears', 'sw', 'curses'],
        description='The command to change the settings for the anti-profanity system.'
    )
    async def anti_profanity(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='profanity')


def setup(bot):
    bot.add_cog(AutoMod(bot))
