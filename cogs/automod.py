import collections
import re

from better_profanity import profanity

from .moderation import *

log = logging.getLogger(__name__)

async def automod_log(bot, message, action, reason) -> None:
    """
    Send an automod log
    """
    data = await bot.config.find_one({"_id": message.guild.id})
    try:
        automod = message.guild.get_channel(data['automod_logs'])

    except (TypeError, KeyError):
        return
    if not automod: return

    em = SaturnEmbed(
        title='Automod',
        description=f'**Member -** {message.author.mention}\n'
                    f'**Action -** {action}\n'
                    f'**Reason -** {reason}',
        colour=discord.Colour.orange(),
        timestamp=utc()
    )
    em.set_author(icon_url=message.author.avatar_url, name=message.author)
    await automod.send(embed=em)

async def profanity_check(bot, message):
    _data = await bot.config.find_one({"_id": message.guild.id})
    msg = str(message.content).lower()

    try:
        if _data['profanity_toggle']:  # check if profanity is enabled
            try:
                if _data['words']:  #
                    profanity.load_censor_words(_data['words'])

            except (TypeError, KeyError):
                profanity.load_censor_words_from_file(
                    bot.path + '/assets/profanity.txt')

            # anti-profanity
            if (
                    # message just has plain profanity
                    profanity.contains_profanity(msg) or
                    profanity.contains_profanity(
                        msg.replace(' ', '')) or  # message has spaces and remove the spaces
                    profanity.contains_profanity(
                        re.sub(r'[^\w\s]', '', msg)) or  # message has punctuation, remove punctuation
                    # message has invisible unicode character
                    profanity.contains_profanity(msg.replace('­', '')) or
                    profanity.contains_profanity(
                        "".join(collections.OrderedDict.fromkeys(msg)))  # duplicate chars
            ):
                if await profanity_command_check(bot, message):
                    return False  # make sure that they're not adding a word
                # in that case then don't do stuff

                await message.delete()
                em = SaturnEmbed(
                    description=f"{WARNING} That word is not allowed in **{message.guild}**!",
                    colour=GOLD)
                await message.channel.send(embed=em)
                await automod_log(
                    bot, message, "warning",
                    f"Said || {message.content} || which contains profanity")
                return True

            return False

    except (TypeError, KeyError):
        return False

async def spam_check(bot, message):
    _data = await bot.config.find_one({"_id": message.guild.id})
    try:
        if _data['spam_toggle'] and is_spamming(bot, message.author):  # check that spam is on and author is spamming
            _cache = get_cache(bot, message.author)  # make a copy of the cache
            # so it doesn't double the message
            await delete_cache(bot, message.author)

            if not message.author.guild_permissions.manage_messages:
                to_delete = len(_cache)
                try:
                    # purge the spam messages sent by the author
                    # I originally had the check to be lambda m: m in get_cache but it just didn't quite work
                    # because I was emptying the cache after the messages were purged
                    await message.channel.purge(
                        limit=to_delete,
                        check=lambda m: m in _cache)  # make sure that the message author is the spammer

                except discord.NotFound or discord.NoMoreItems or asyncio.QueueEmpty:
                    pass
                data = await bot.config.find_one({"_id": message.guild.id})
                try:
                    whitelist = data['spam_whitelist']
                    if message.author.id in whitelist: return
                    # check that the author isn't in the spam whitelist

                except (TypeError, KeyError):
                    pass  # if there is no whitelist

                try:
                    if not (mute_role := message.guild.get_role(_data['mute_role'])):
                        mute_role = await create_mute_role(bot, message)

                except (TypeError, KeyError):
                    # create the mute role
                    mute_role = await create_mute_role(bot, message)

                start = _cache[to_delete - 1].created_at
                end = _cache[0].created_at
                delta = (start - end).total_seconds()

                # mute the member, only if they can't mute other people so they have mute invincibility
                await mute_members(bot, message, message.author,
                                   "sending messages too quickly", mute_role, 10)
                await automod_log(
                    bot, message, "10 second mute",
                    f"Sent {to_delete} messages in {delta} seconds")

                em = SaturnEmbed(
                    description=f"{WARNING} Spam is not allowed in **{message.guild}**!",
                    colour=GOLD)
                await message.channel.send(embed=em)

    except (TypeError, KeyError):
        pass

async def update_cache(bot, message: discord.Message):
    """
    Update the bot's message cache.
    """
    try:
        if not bot.message_cache[message.author.id]:
            bot.message_cache[message.author.id] = []

    except (TypeError, KeyError):
        bot.message_cache[message.author.id] = []

    bot.message_cache[message.author.id].append(message)

def get_cache(bot, member) -> list or None:
    """
    Retrieve a member's message cache.
    """
    try:
        for message in bot.message_cache[member.id]:
            # filter out all items in the bot._cache that were created more than 5 seconds ago
            if utc() - datetime.timedelta(seconds=5) > message.created_at:
                bot.message_cache[member.id].remove(message)

            return bot.message_cache[member.id]

    except (TypeError, KeyError):
        return []

def is_spamming(bot, member):
    cache = bot.get_cache(member)

    if len(cache) > 5:
        return True

    return False

async def delete_cache(bot, member):
    """
    Delete a member's cache.
    """
    try:
        if not bot.message_cache[member.id]:
            return False

        bot.message_cache.pop(member.id)

    except (TypeError, KeyError):
        return False

async def profanity_command_check(bot, message: discord.Message):
    starts, prefix = False, None
    content = message.content
    for _prefix in await retrieve_raw_prefix(bot, message):
        if content.startswith(_prefix):
            starts = True
            prefix = _prefix

    if not starts:
        return False
    content = content.replace(prefix, '')
    if bot.get_command(content[:2]) or bot.get_command(content[:1]):
        return True

    else:
        return False


# noinspection SpellCheckingInspection
class AutoMod(commands.Cog, name='Auto Moderation'):
    """
    The Auto Moderation module. Includes all the commands to have a virtually endless task force of moderators.

    Includes anti-profanity and anti-spam.
    """
    def __init__(self, bot):
        self.bot = bot

    def get_censor_words(self):
        with open(self.bot.path + '/assets/profanity.txt', 'r') as f:
            file = f.read()

        return file.split('\n')

    def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild or not ctx.author.guild_permissions.manage_guild:
            return False
        return True

    # noinspection PyBroadException
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        await update_cache(self.bot, message)
        await profanity_check(self.bot, message)
        await spam_check(self.bot, message)

    @commands.group(
        name='profanity',
        aliases=['prof', 'swears', 'sw', 'curses'],
        description='The command to change the settings for the anti-profanity system.',
        invoke_without_command=True
    )
    async def anti_profanity(self, ctx):
        try:
            await ctx.invoke(self.bot.get_command('help'), entity='profanity')
        except:
            raise

    @anti_profanity.command(
        name='toggle',
        aliases=['switch', 'tggle'],
        description='Toggles the anti-profanity system on or off.'
    )
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def toggle_profanity(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['profanity_toggle']:
                toggle = False
            else:
                toggle = data['profanity_toggle']

        except (TypeError, KeyError):
            toggle = False

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"profanity_toggle": not toggle}}, upsert=True)
        status = "enabled" if not toggle else "disabled"
        em = SaturnEmbed(
            description=f"{CHECK} {status.title()} anti-profanity.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_profanity.command(
        name='add',
        aliases=['addword', 'addcurse', 'addswear', 'addprofanity'],
        description='Adds a curse word the anti-profanity system detects. '
                    f'Use -default to include the default wordlist.'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def add_curse(self, ctx, *, word: str):
        if word == "-default":
            words = self.get_censor_words()

        else:
            words = []

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        if words and word in words:
            em = SaturnEmbed(
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
                    em = SaturnEmbed(
                        description=f"{ERROR} That word is already recognized as a curse word.",
                        colour=RED)
                    return await ctx.send(embed=em)

                words.append(word)

        except (TypeError, KeyError):
            words.append(word)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"words": words}}, upsert=True)

        if word != '-default':
            await ctx.message.delete()

        em = SaturnEmbed(
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
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def remove_curse(self, ctx, *, word: str):
        words = self.get_censor_words()

        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['words']:
                words.remove(word)

            else:
                words = data['words']
                if word not in words:
                    em = SaturnEmbed(
                        description=f"{ERROR} That word is not recognized as a curse word.",
                        colour=RED)
                    return await ctx.send(embed=em)

                words.remove(word)

        except (TypeError, KeyError):
            words.remove(word)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"words": words}}, upsert=True)
        await ctx.message.delete()

        em = SaturnEmbed(
            description=f"{CHECK} Removed || {word} || as a registered curse word.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_profanity.command(
        name='clear',
        aliases=['clearsw', 'clearwords', 'clearcurses', 'clearswears'],
        description='Deletes all currently registered words. For deleting one word, use the `profanity delswears `'
    )
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def clear_curses(self, ctx):
        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$unset': {"words": 1}})
        em = SaturnEmbed(
            description=f"{CHECK} Deleted all recognized curse words.",
            color=GREEN)
        await ctx.send(embed=em)

    @commands.group(
        name='spam',
        aliases=['antispam', 'sp', 'asp', 'anti-spam'],
        description='The command to change the settings for the anti-spam system.',
        invoke_without_command=True
    )
    async def anti_spam(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='spam')

    @anti_spam.command(
        name='toggle',
        aliases=['switch', 'tggle'],
        description='Toggles the anti-spam system on or off.'
    )
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def toggle_antispam(self, ctx):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['spam_toggle']:
                toggle = False
            else:
                toggle = data['spam_toggle']

        except (TypeError, KeyError):
            toggle = False

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"spam_toggle": not toggle}}, upsert=True)
        status = "enabled" if not toggle else "disabled"
        em = SaturnEmbed(
            description=f"{CHECK} {status.title()} anti-spam.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_spam.command(
        name='whitelist',
        aliases=['disablefor', 'untrack'],
        description='Adds a member to the anti-spam whitelist. If they spam, the automod will ignore them.'
    )
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def whitelist_antispamspam(self, ctx, member: discord.Member):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['spam_whitelist']:
                whitelist = []

            else:
                whitelist = data['spam_whitelist']

        except (TypeError, KeyError):
            whitelist = []

        if member.id in whitelist:
            em = SaturnEmbed(
                description=f"{ERROR} {member.mention} is already whitelisted.",
                colour=RED)
            return await ctx.send(embed=em)

        whitelist.append(member.id)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"spam_whitelist": whitelist}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} Added {member.mention} to the anti-spam whitelist.",
            color=GREEN)
        await ctx.send(embed=em)

    @anti_spam.command(
        name='unwhitelist',
        aliases=['enablefor', 'track', 'blacklist'],
        description='Adds a member to the anti-spam whitelist. If they spam, the automod will ignore them.'
    )
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def unwhitelist_antispamspam(self, ctx, member: discord.Member):
        data = await self.bot.config.find_one({"_id": ctx.guild.id})
        try:
            if not data['spam_whitelist']:
                em = SaturnEmbed(
                    description=f"{ERROR} There are no whitelists in this guild.",
                    colour=RED)
                return await ctx.send(embed=em)

            else:
                whitelist = data['spam_whitelist']

        except (TypeError, KeyError):
            em = SaturnEmbed(
                description=f"{ERROR} There are no whitelists in this guild.",
                colour=RED)
            return await ctx.send(embed=em)

        if member.id not in whitelist:
            em = SaturnEmbed(
                description=f"{ERROR} {member.mention} is not whitelisted.",
                colour=RED)
            return await ctx.send(embed=em)

        whitelist.remove(member.id)

        await self.bot.config.update_one({"_id": ctx.guild.id},
                                         {'$set': {"spam_whitelist": whitelist}}, upsert=True)
        em = SaturnEmbed(
            description=f"{CHECK} Removed {member.mention} from the anti-spam whitelist.",
            color=GREEN)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(AutoMod(bot))
