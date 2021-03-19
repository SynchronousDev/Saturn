import asyncio
from datetime import datetime as dt
import logging

import discord
from discord.ext import commands

from .constants import *
from discord.ext import menus
from .paginator import Paginator
from cogs.moderation import mute_members

import collections
import re

from better_profanity import profanity


class SaturnPaginator(Paginator):
    pass

# noinspection PyShadowingNames, PyBroadException, SpellCheckingInspection
async def get_prefix(bot, message):
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


def flatten(l):
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
def convert_time(time):
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
            times[str(key)]["value"] = time // value
            time %= value

        for key, value in times.items():
            if not value['value']:
                continue

            return_times.append("{0} {1}".format(value['value'], key))

        return ' '.join(return_times) if return_times else '0 seconds'

    except Exception:
        return 'indefinitely'


async def syntax(command):
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
    return f"```{str(command.qualified_name)} {params}```"


# noinspection PyBroadException
async def retrieve_raw_prefix(bot, message):
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


async def retrieve_prefix(bot, message):
    """
    Return the prefix as a readable string
    """
    prefix = await retrieve_raw_prefix(bot, message)
    if isinstance(prefix, str):
        return prefix
    elif isinstance(prefix, list):
        prefix = flatten(prefix)
        return ' | '.join(prefix)

# noinspection PyUnusedLocal
class ConfirmationMenu(menus.Menu):
    def __init__(self, msg):
        super().__init__(timeout=30.0)
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        em = discord.Embed(
            description=f'{WARNING} Are you sure you want to {self.msg}?',
            colour=GOLD,
            timestamp=dt.utcnow()
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


# noinspection PyBroadException,SpellCheckingInspection
async def create_log(bot, member, guild, action, moderator, reason, duration=None):
    """
    Send details about a punishment and log it in the mod logs channel.
    """
    colours = {
        "kick": {"colour": discord.Colour.orange(), "emote": NO_ENTRY},
        "ban": {"colour": discord.Colour.red(), "emote": NO_ENTRY},
        "mute": {"colour": discord.Colour.orange(), "emote": MUTE},
        "unmute": {"colour": discord.Colour.green(), "emote": UNMUTE},
        "warn": {"colour": discord.Colour.gold(), "emote": WARN},
        "unban": {"colour": discord.Colour.gold(), "emote": UNBAN},
        "softban": {"colour": discord.Colour.red(), "emote": NO_ENTRY},
        "tempban": {"colour": discord.Colour.red(), "emote": NO_ENTRY}
    }
    colour = GOLD
    emote = None
    for key, value in colours.items():
        if str(key) == str(action.lower()):
            colour, emote = value["colour"], value["emote"]

    try:
        em = discord.Embed(
            colour=colour,
            timestamp=dt.utcnow()
        )
        em.set_thumbnail(url=emote)
        desc = f"**Guild** - {guild}\n" \
               f"**Moderator** - {moderator.mention}\n" \
               f"**Action** - {action.title()}\n" \
               f"**Reason** - {reason}\n"
        if duration:
            desc += f"**Duration** - {duration}\n"

        em.description = desc

        await member.send(embed=em)

    except discord.Forbidden:
        pass

    except Exception as e:
        raise e

    # send it to the log channel because why not lol
    data, mod_logs = await bot.config.find_one({"_id": guild.id}), None
    try:
        mod_logs = guild.get_channel(data['mod_logs'])

    except KeyError or TypeError:
        pass

    action_ = action
    if action.find("ban") != -1:
        action_ += "ned"

    elif action in ("mute", "unmute"):
        action_ += "d"

    else:
        action_ += "ed"

    em = discord.Embed(
        title=f'Member {action_.title()}',
        colour=colour,
        timestamp=dt.utcnow()
    )
    em.set_thumbnail(url=emote)
    em.set_author(icon_url=member.avatar_url, name=member.name)
    em.set_footer(text='Case no. {}'.format(await get_last_case_id(bot, guild)))
    em.add_field(name='Member', value=member.mention, inline=False)
    em.add_field(name='Moderator', value=moderator.mention, inline=False)
    if duration:
        em.add_field(name='Duration', value=duration, inline=False)

    if reason:
        em.add_field(name='Reason', value=reason, inline=False)

    try:
        await mod_logs.send(embed=em)

    except AttributeError:
        pass

    _action = action + ((' lasting ' + duration) if duration else '')
    # get the action + duration for formatting purposes

    await _create_log(bot, member, guild, _action, moderator, reason)  # create the log


async def get_member_mod_logs(bot, member, guild):
    """
    Fetch mod logs for a specific guild
    Will only fetch the first 10000 punishments, because ya know, operation times suck
    """
    logs = []
    cursor = bot.mod.find({"member": member.id, "guild_id": guild.id})
    for document in await cursor.to_list(length=10000):
        logs.append(document)

    return logs


async def get_guild_mod_logs(bot, guild):
    """
    Fetch mod logs for a specific guild
    """
    logs = []
    cursor = bot.mod.find({"guild_id": guild.id})
    for document in await cursor.to_list(length=10000):
        logs.append(document)

    return logs


# noinspection SpellCheckingInspection
async def get_last_case_id(bot, guild):
    logs = await get_guild_mod_logs(bot, guild)
    await update_log_caseids(bot, guild)

    if not logs:
        case_id = 1

    else:
        try:
            case_id = int(logs[-1]["case_id"]) + 1

        except KeyError:
            case_id = 1

    return case_id


async def _create_log(bot, member, guild, action, moderator, reason):
    """
    Create a new log object in the database
    """
    case_id = await get_last_case_id(bot, guild)

    schema = {
        "guild_id": guild.id,
        "case_id": case_id,
        "member": member.id,
        "action": action,
        "moderator": moderator.id,
        "reason": reason,
        "time": dt.utcnow()
    }
    await bot.mod.insert_one(schema)


# noinspection PyUnusedLocal
async def update_log(bot, case_id, guild, action, reason):
    """
    Update a mod log
    Used to update reasons for punishments
    """
    logs = await get_guild_mod_logs(bot, guild)

    schema = {
        "action": action,
        "reason": reason
    }
    await bot.mod.update_one({"guild_id": guild.id, "case_id": case_id}, {"$set": schema}, upsert=True)


async def starboard_embed(message, payload):
    desc = message.content  # if not isinstance(message, discord.Embed) else message
    em = discord.Embed(
        colour=GOLD,
        description=desc,
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
    return em


async def update_log_caseids(bot, guild):
    logs = await get_guild_mod_logs(bot, guild)

    for i, log in enumerate(logs, start=1):
        if i != log['case_id']:
            await bot.mod.update_one(
                {"guild_id": guild.id, "case_id": log['case_id']}, {"$set": {"case_id": i}}, upsert=True)


async def delete_log(bot, id, guild):
    await bot.mod.delete_one({"guild_id": guild.id, "case_id": id})
    await update_log_caseids(bot, guild)


def clean_codeblock(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content
