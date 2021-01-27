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

# Colours, emotes, and useful stuff

MAIN = 0xff00ff
RED = Color.red()
GREEN = Color.green()
GOLD = Color.gold()

ERROR = '<:SelCross:793577338062766091>  '
CHECK = '<:SelCheck:800778507680612353>  '
LOADING = '<a:SeleniumLoading:800924830098653194>'
BLANK = '\uFEFF'
LOCK = ':lock:'
UNLOCK = ':unlock:'
WEAK_SIGNAL = ':red_circle:'
MEDIUM_SIGNAL = ':yellow_circle:'
STRONG_SIGNAL = ':green_circle:'

time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d|w))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400, "w": 604800}

cwd = Path(__file__).parents[0]
cwd = str(cwd)

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
        day = time // (24 * 3600)
        time = time % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time
        return (f"`{str(int(day)) + 'd' if day else ''}"
                f"{(' ' if day else '') + str(int(hour)) + 'h' if hour else ''}"
                f"{(' ' if hour else '') + str(int(minutes)) + 'm' if minutes else ''}"
                f"{(' ' if minutes else '') + str(int(seconds)) + 's' if seconds else ''}`")

    except TypeError:
        return 'indefinitely'


async def syntax(command, ctx, bot):
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


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise commands.BadArgument(
                    f"{value} is an invalid time key! m|w|h|m|s|d are valid arguments"
                )
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")

        return round(time)

