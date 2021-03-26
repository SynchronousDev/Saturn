# noinspection PyUnresolvedReferences
import asyncio
import datetime
import logging

# noinspection PyUnresolvedReferences
import discord
import pytz
from discord.ext import commands

from .constants import *
from discord.ext import menus

# noinspection PyUnresolvedReferences
from .paginator import Paginator
# noinspection PyUnresolvedReferences
import typing as t

log = logging.getLogger(__name__)


# noinspection PyShadowingNames, PyBroadException, SpellCheckingInspection
async def get_prefix(bot, message) -> commands.when_mentioned_or():
    """
    For the bot's command_prefix. Not the same as the `retrieve_prefix` function.
    """
    # sphagetto code galore
    if not message.guild: return commands.when_mentioned_or(PREFIX)(bot, message)
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        if not data or not data['prefix']: return commands.when_mentioned_or(PREFIX)(bot, message)

        if isinstance(data['prefix'], str):
            return commands.when_mentioned_or(data['prefix'])(bot, message)

        pre = flatten(data['prefix'])
        return commands.when_mentioned_or(*pre)(bot, message)

    except Exception:
        return commands.when_mentioned_or(PREFIX)(bot, message)


def flatten(l) -> list:
    _list = []
    l = list(l)
    while l:
        e = l.pop()
        if isinstance(e, list):
            l.extend(e)

        else:
            _list.append(e)

    return list(reversed(_list))


# noinspection PyBroadException
def convert_time(time) -> str:
    """
    Convert time into a years, hours, minute, seconds thing.
    """
    # much better than the original one lol
    # man I suck at docstrings lol
    try:
        times = {}
        return_times = []
        time_dict = {
            "years": 31536000,
            "months": 2628000,
            "weeks": 604800,
            "days": 86400,
            "hours": 3600,
            "minutes": 60,
            "seconds": 1
        }
        for key, value in time_dict.items():
            times[str(key)] = {}
            times[str(key)]["value"] = int(time // value)
            time %= value

        for key, value in times.items():
            if not value['value']:
                continue

            return_times.append("{0} {1}".format(value['value'], key))

        return ' '.join(return_times) if return_times else '0 seconds'

    except Exception:
        return 'indefinitely'

def general_convert_time(time, to_places=2) -> str:
    """
    Used to get a more readable time conversion
    """
    times = convert_time(time).split(' ')
    return ' '.join(times[:to_places]) + (', ' if times[to_places:(to_places * 2)] else '') \
           + ' '.join(times[to_places:(to_places * 2)])

def convert_to_timestamp(time: datetime.datetime) -> str:
    """
    Convert a regular datetime object into something resembling a discord.Embed footer.
    """
    time = time.replace(tzinfo=datetime.timezone.utc)

    current = datetime.datetime.now(datetime.timezone.utc)
    day, _day = int(current.strftime("%d")), int(time.strftime("%d"))
    month, _month = int(current.strftime("%m")), int(time.strftime("%m"))
    year, _year = int(current.strftime("%Y")), int(time.strftime("%Y"))
    if month == _month and year == _year:
        est_time = time.astimezone(pytz.timezone('America/New_York'))

        fmt = '%I:%M %p'
        if day == _day:
            return est_time.strftime(f"Today at {fmt}")

        elif day - 1 == _day:
            return est_time.strftime(f"Yesterday at {fmt}")

    return time.strftime("%d/%m/%y")

async def syntax(command) -> str:
    """
    Get the syntax/usage for a command.
    """
    params = []

    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            value = str(value)
            if "optional" in str(value).lower() or "greedy" in str(value).lower():
                params.append(f"[{key}]")

            else:
                params.append(f"<{key}>")

    params = " ".join(params)
    return f"{str(command.qualified_name)} {params}"

# noinspection PyBroadException
async def retrieve_raw_prefix(bot, message) -> list:
    """
    A method for retrieving the raw prefix out of the database
    """
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        # make sure that we have a prefix in the data
        if not data or not data["prefix"]:
            return PREFIX

        # we don't have to put anything into the database
        # because it's always going to be s. unless they enter stuff into the database
        # and when they change the prefix it gets inserted into the db
        else:
            return data['prefix']

    except Exception:
        return PREFIX

async def error_arg_syntax(command, arg):
    cmd_syntax = await syntax(command)
    chars = cmd_syntax.rpartition(arg)[0]

    spaces = chars.count(' ')  # calculate how many spaces are in the sentence before the args
    num_of_letters = len(''.join(chars.split(' ')))  # get the number of letters minus the spaces

    before_pointers = ' ' * (spaces + num_of_letters)  # get the number of spaces before the pointer
    pointers = '^' * len(arg)

    return f"{cmd_syntax}\n{before_pointers}{pointers}"  # return the syntax with the ^^^^^ under
    # to indicate which argument is parsed wrongly

async def retrieve_prefix(bot, message) -> str:
    """
    Return the prefix as a readable string of prefixes.
    """
    prefix = await retrieve_raw_prefix(bot, message)
    if isinstance(prefix, str):
        return prefix
    elif isinstance(prefix, list):
        prefix = flatten(prefix)
        return ' | '.join(prefix)

# noinspection PyUnusedLocal
class ConfirmationMenu(menus.Menu):
    """
    A confirmation menu, for when you need to double-check that they actually want to do something.
    """
    def __init__(self, msg):
        super().__init__(timeout=30.0)
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        em = discord.Embed(
            description=f'{WARNING} Are you sure you want to {self.msg}?',
            colour=GOLD,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        return await ctx.send(embed=em)

    @menus.button(CHECK)  # confirmation
    async def do_confirm(self, payload):
        self.result = True
        self.stop()

    @menus.button(ERROR)  # deny
    async def do_deny(self, payload):
        self.result = False
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result

class Dueler:
    """
    A dueler class. Used for the duel command
    """

    def __init__(self, member: discord.Member):
        self.member = member
        self.health = 100

    def damage(self, amount):  # do damage
        self.health -= amount

    def heal(self, amount):  # heal hp
        self.health += amount

    def health(self):
        return self.health

    @property
    def name(self):
        return self.member.name

    def member(self):
        return self.member


async def starboard_embed(message, payload) -> discord.Embed:
    """
    Create a starboard embed
    """
    desc = message.content  # if not isinstance(message, discord.Embed) else message
    em = discord.Embed(
        colour=GOLD,
        description=desc,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    # attachments
    if len(message.attachments):
        attachment = message.attachments[0]

        em.add_field(name='Attachments', value=f"[{attachment.filename}]({attachment.url})", inline=False)
        em.set_image(url=attachment.url)

    # support for embeds
    if len(message.embeds):
        embed = message.embeds[0]
        em_desc = ""
        if embed.title: em_desc += f"__**{embed.title}**__\n"
        if embed.description: em_desc += (embed.description + '\n')
        if embed.fields:
            field = embed.fields[0]
            em.add_field(name=field.name, value=field.value, inline=False)

        if embed.footer: em_desc += embed.footer
        if embed.image:
            em.add_field(name='Embed Image', value=f"[Attachment]({embed.image.url})", inline=False)
            em.set_image(url=embed.image.url)

        if embed.thumbnail:
            em.add_field(name='Embed Image', value=f"[Attachment]({embed.thumbnail.url})", inline=False)
            em.set_image(url=embed.thumbnail.url)

        em.description = em_desc

    em.add_field(name='Original Message', value=f"[Jump!](https://discord.com/channels/"
                                                f"{payload.guild_id}/{payload.channel_id}/{message.id})")

    em.set_author(icon_url=message.author.avatar_url, name=message.author)
    em.set_footer(text=f'Message ID - {message.id}')
    return em

def clean_codeblock(content) -> str:
    """
    Clean a codeblock of the ``` and the pys.
    """
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content
