import collections
import json
import logging
import re
from pathlib import Path
from datetime import datetime as dt

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import MemberNotFound
from datetime import datetime as dt, timedelta
import functools

# Colours, emotes, and useful stuff

MAIN = 0x660dd9
RED = Color.red()
GREEN = Color.green()
GOLD = Color.gold()

ERROR = '<:SelError:804756495044444160>'
CHECK = '<:SelCheck:804756481831993374>'
LOADING = '<a:SeleniumLoading:800924830098653194>'
BLANK = '\uFEFF'
LOCK = ':lock:'
UNLOCK = ':unlock:'
WEAK_SIGNAL = ':red_circle:'
MEDIUM_SIGNAL = ':yellow_circle:'
STRONG_SIGNAL = ':green_circle:'
SHARD = '<:SeleniumShard:806598937381306418>'
NO_REPEAT = '⏭'
REPEAT_ONE = '🔂'
REPEAT_ALL = '🔁'
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])) "


"""
JSON utilities
Used to save time and not having to use `with open` every single time I load json lol
"""


def read_json(file):
    # Reads stuff from a json file
    with open(f"{cwd}/config/{file}.json", "r") as f:
        data = json.load(f)
    return data


def write_json(data, file):
    # Dumps stuff from a json file
    with open(f"{cwd}/config/{file}.json", "w") as f:
        json.dump(data, f, indent=4)


def convert_time(time):
    try:
        # not exactly what I would call the most efficient process
        # but it gets the job done
        times = []
        years = time // 31536000
        time %= 31536000
        months = time // 2628000
        time %= 2628000
        weeks = time // 604800
        time %= 604800
        days = time // 86400
        time %= 86400
        hours = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        # this is a very slow and messy process but I can't seem to think of a better way to do it
        # especially because I'm calculating more than just hours and minutes and seconds, I'm going into years
        # but be honest, how many of you guys have cooldowns lasting 5 decades?
        if years >= 1:
            times.append(str(years) + ' years')
        if months >= 1:
            times.append(str(months) + ' months')
        if weeks >= 1:
            times.append(str(weeks) + ' weeks')
        if days >= 1:
            times.append(str(days) + ' days')
        if hours >= 1:
            times.append(str(hours) + ' hours')
        if minutes >= 1:
            times.append(str(minutes) + ' mintues')
        if seconds >= 1:
            times.append(str(seconds) + ' seconds')
        return f"`{' '.join(times) if len(times) else '0 seconds'}`"

    except Exception:
        return '`indefinitely`'

async def syntax(command):
    params = []

    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(
                value) else f"<{key}>")

    params = " ".join(params)
    return f"```{str(command)} {params}```"


async def retrieve_prefix(bot, message):
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        # Make sure we have a useable prefix
        if not data or not data["prefix"]:
            return "sl!"

        else:
            return data["prefix"]
    except Exception as e:
        return "sl!"


async def create_mute_role(bot, ctx):
    perms = discord.Permissions(
        send_messages=False, read_messages=True)
    mute_role = await ctx.guild.create_role(name='Muted', colour=RED, permissions=perms,
                                            reason='Could not find a muted role')

    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(mute_role, read_messages=True, send_messages=False)

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

    await bot.config.update_one({"_id": ctx.guild.id},
                                {'$set': {"mute_role_id": mute_role.id}}, upsert=True)

    return mute_role


async def send_punishment(member, guild, action, moderator, reason, duration=None):
    try:
        if duration:
            em = discord.Embed(
                description=f"**Guild** - {guild}\n"
                            f"**Moderator** - {moderator.mention}\n"
                            f"**Action** - {action.title()}\n"
                            f"**Duration** - {duration}\n"
                            f"**Reason** - {reason}",
                colour=RED,
                timestamp=dt.now())
            await member.send(embed=em)

        else:
            em = discord.Embed(
                description=f"**Guild** - {guild}\n"
                            f"**Moderator** - {moderator.mention}\n"
                            f"**Action** - {action.title()}\n"
                            f"**Reason** - {reason}",
                colour=RED,
                timestamp=dt.now())
            await member.send(embed=em)

    except discord.Forbidden:
        pass

    except discord.HTTPException:
        pass


def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content
