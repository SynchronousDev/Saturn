import collections
import json
import logging
import re
from pathlib import Path
from datetime import datetime as dt

import discord
from discord import Color
from discord.ext import commands
import functools

# Colours, emotes, and useful stuff

MAIN = 0x660dd9
RED = Color.red()
GREEN = Color.green()
GOLD = Color.gold()

ERROR = '<:SelError:804756495044444160>'
CHECK = '<:SelCheck:804756481831993374>'
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
SPOTIFY_URL_REGEX = r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*track[/:]*[A-Za-z0-9?=]+"
YOUTUBE_URL_REGEX = r"(?:https?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/"\
                    r"(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]+)"


def convert_time(time):
    try:
        # not exactly what I would call the most efficient process
        # but it gets the job done
        times = []
        years = time // 31536000
        time %= 31536000
        if years >= 1:
            times.append(str(years) + ' years')
        months = time // 2628000
        time %= 2628000
        if months >= 1:
            times.append(str(months) + ' months')
        weeks = time // 604800
        time %= 604800
        if weeks >= 1:
            times.append(str(weeks) + ' weeks')
        days = time // 86400
        time %= 86400
        if days >= 1:
            times.append(str(days) + ' days')
        hours = time // 3600
        time %= 3600
        if hours >= 1:
            times.append(str(hours) + ' hours')
        minutes = time // 60
        time %= 60
        if minutes >= 1:
            times.append(str(minutes) + ' minutes')
        seconds = time
        if seconds >= 1:
            times.append(str(seconds) + ' seconds')

        return f"{' '.join(times) if len(times) else '0 seconds'}"

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


async def send_punishment(bot, member, guild, action, moderator, reason, duration=None):
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

    _action = action + ((' lasting ' + duration) if duration else '')

    await create_log(bot, member, guild, _action, moderator, reason)

async def get_member_modlogs(bot, member, guild):
    """
    Fetch mod logs for a specific guild
    Will only fetch the first 100 punishments, because ya know, operation times suck
    """
    logs = []
    cursor = bot.mod.find({"member": member.id, "guild_id": guild.id})
    for document in await cursor.to_list(length=100):
        logs.append(document)

    return logs

async def get_guild_modlogs(bot, guild):
    """
    Fetch mod logs for a specific guild
    """
    logs = []
    cursor = bot.mod.find({"guild_id": guild.id})
    for document in await cursor.to_list(length=100):
        logs.append(document)

    return logs

async def get_last_caseid(bot, guild):
    logs = await get_guild_modlogs(bot, guild)
    await update_log_caseids(bot, guild)

    if not logs:
        case_id = 1

    else:
        try:
            case_id = int(logs[-1]["case_id"]) + 1

        except KeyError:
            case_id = 1

    return case_id

async def create_log(bot, member, guild, action, moderator, reason):
    """
    Create a new log object in the database
    """
    case_id = await get_last_caseid(bot, guild)

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

async def update_log(bot, case_id, guild, action, reason):
    """
    Update a mod log
    Used to update reasons for punishments
    """
    logs = await get_guild_modlogs(bot, guild)

    schema = {
        "action": action,
        "reason": reason
    }
    await bot.mod.update_one({"guild_id": guild.id, "case_id": case_id}, {"$set": schema}, upsert=True)

async def update_log_caseids(bot, guild):
    logs = await get_guild_modlogs(bot, guild)

    for i, log in enumerate(logs, start=1):
        if i != log['case_id']:
            await bot.mod.update_one(
                {"guild_id": guild.id, "case_id": log['case_id']}, {"$set": {"case_id": i}}, upsert=True)

async def delete_log(bot, id, guild):
    await bot.mod.delete_one({"guild_id": guild.id, "case_id": id})
    await update_log_caseids(bot, guild)

def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content
