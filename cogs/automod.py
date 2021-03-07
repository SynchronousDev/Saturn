import re

from better_profanity import profanity

from assets import *
import collections

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class AutoMod(commands.Cog, name='Auto Moderation'):
    def __init__(self, bot):
        self.bot = bot

    async def get_censor_words(self):
        with open(self.bot.path + '/assets/profanity.txt', 'r') as f:
            file = f.read()

        return file.split('\n')

    async def profanity_command_check(self, message):
        starts, prefix = False, None
        content = message.content
        for _prefix in await retrieve_raw_prefix(self.bot, message):
            if content.startswith(_prefix):
                starts = True
                prefix = _prefix

        if not starts: return False
        content = content.replace(prefix, '')
        if self.bot.get_command(content[:2]) or self.bot.get_command(content[:1]):
            return True

        else:
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        data = await self.bot.config.find_one({"_id": message.guild.id})
        msg = message.content.lower()

        try:
            if data['profanity_toggle']:
                try:
                    if data['words']:
                        profanity.load_censor_words(data['words'])

                except KeyError:
                    profanity.load_censor_words_from_file(self.bot.path + '/assets/profanity.txt')

                # anti-profanity
                if (
                    profanity.contains_profanity(msg) or  # message just has plain profanity
                    profanity.contains_profanity(
                        msg.replace(' ', '')) or  # message has spaces and remove the spaces
                    profanity.contains_profanity(
                        re.sub(r'[^\w\s]', '', msg)) or  # message has punctuation, remove punctuation
                    profanity.contains_profanity(msg.replace('­', '')) or  # message has invis unicode character
                    profanity.contains_profanity("".join(collections.OrderedDict.fromkeys(msg)))  # duplicate chars
                ):
                    if await self.profanity_command_check(message): return
                    await message.delete()
                    await message.channel.send(
                        "{}, That word is not allowed in **{}**!".format(message.author.mention, message.guild))

        except KeyError or TypeError:
            pass

    @commands.group(
        name='profanity',
        aliases=['prof', 'swears', 'sw', 'curses'],
        description='The command to change the settings for the anti-profanity system.',
        invoke_without_command=True
    )
    async def anti_profanity(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='profanity')

    @anti_profanity.command(
        name='toggle',
        aliases=['switch'],
        description='Toggles the anti-profanity system on or off.'
    )
    async def toggle_profanity(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['profanity_toggle']:
                toggle = False
            else:
                toggle = data['profanity_toggle']

        except KeyError or TypeError:
            toggle = False

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"profanity_toggle": not toggle}}, upsert=True)
        status = "enabled" if not toggle else "disabled"
        em = discord.Embed(
            description=f"{CHECK} {status.title()} anti-profanity.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_profanity.command(
        name='add',
        aliases=['addword', 'addcurse', 'addswear', 'addprofanity'],
        description='Adds a curse word the anti-profanity system detects. '
                    'Use -default to include the default Saturn wordlist.'
    )
    async def add_curse(self, ctx, *, word: str):
        if word == "-default":
            words = await self.get_censor_words()

        else:
            words = []

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        if words and word in words:
            em = discord.Embed(
                description=f"{ERROR} That word is already recognized as a curse word.",
                colour=RED)
            return await ctx.send(embed=em)

        try:
            _ = data['words']
            if not data['words']:
                words.append(word)

            else:
                words = data['words']
                if word in words:
                    em = discord.Embed(
                        description=f"{ERROR} That word is already recognized as a curse word.",
                        colour=RED)
                    return await ctx.send(embed=em)

                words.append(word)

        except KeyError or TypeError:
            words.append(word)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"words": words}}, upsert=True)

        if word != '-default':
            await ctx.message.delete()

        em = discord.Embed(
            description=f"{CHECK} Added "
                        f"{f'|| {word} ||' if word != '-default' else 'the default wordlist'} "
                        f"as a recognized curse word.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_profanity.command(
        name='delete',
        aliases=['remove', 'delcurse', 'removeswear', 'delprofanity'],
        description='Removes a curse word the anti-profanity system detects.'
    )
    async def remove_curse(self, ctx, *, word: str):
        words = await self.get_censor_words()

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['words']:
                words.remove(word)

            else:
                words = data['words']
                if word not in words:
                    em = discord.Embed(
                        description=f"{ERROR} That word is not recognized as a curse word.",
                        colour=RED)
                    return await ctx.send(embed=em)

                words.remove(word)

        except KeyError or TypeError:
            words.remove(word)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"words": words}}, upsert=True)
        await ctx.message.delete()

        em = discord.Embed(
            description=f"{CHECK} Removed || {word} || as a registered curse word.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_profanity.command(
        name='clear',
        aliases=['clearsw', 'clearwords', 'clearcurses', 'clearswears'],
        description='Deletes all currently registered words. For deleting one word, use the `profanity delswears `'
    )
    async def clear_curses(self, ctx):
        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$unset': {"words": 1}})
        em = discord.Embed(
            description=f"{CHECK} Deleted all recognized curse words.",
            color=GREEN)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(AutoMod(bot))
