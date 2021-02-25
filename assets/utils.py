import collections
import json
import logging
import re
from pathlib import Path
from datetime import datetime as dt, timedelta

import discord
from discord import Color
from discord.ext import commands
import functools

# Colours, emotes, and useful stuff

MAIN = 0x5A00D8
RED = Color.red()
GREEN = Color.green()
GOLD = Color.gold()

ERROR = '<:SatError:804756495044444160>'
CHECK = '<:SatCheck:804756481831993374>'
BLANK = '\uFEFF'
LOCK = ':lock:'
UNLOCK = ':unlock:'
WEAK_SIGNAL = ':red_circle:'
MEDIUM_SIGNAL = ':yellow_circle:'
STRONG_SIGNAL = ':green_circle:'
SATURN = '<:Saturn:813806979847421983>'
NO_REPEAT = '⏭'
REPEAT_ONE = '🔂'
REPEAT_ALL = '🔁'
MUTE = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
       'speaker-with-cancellation-stroke_1f507.png'
UNMUTE = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
         'speaker-with-three-sound-waves_1f50a.png'
WARN = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
       'warning-sign_26a0.png'
NO_ENTRY = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
      'no-entry_26d4.png'
UNBAN = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
        'door_1f6aa.png'
# weird emotes and stuff yay?

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
SPOTIFY_URL_REGEX = r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*track[/:]*[A-Za-z0-9?=]+"
YOUTUBE_URL_REGEX = r"(?:https?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/" \
                    r"(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]+)"
INVITE_URL_REGEX = r"discord(?:\.com|app\.com|\.gg)/(?:invite/)?([a-zA-Z0-9\-]{2,32})"
# i barely understand these regexes omg

def convert_time(time):
    # much better than the original one lol
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

        return ' '.join(return_times)

    except Exception as e:
        return 'indefinitely'


async def syntax(command):
    params = []

    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(
                value) else f"<{key}>")

    params = " ".join(params)
    return f"```{str(command.qualified_name)} {params}```"


async def retrieve_prefix(bot, message):
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        # Make sure we have a useable prefix
        if not data or not data["prefix"]:
            return "s."

        else:
            return data["prefix"]
    except Exception as e:
        return "s."


async def purge_msgs(bot, ctx, limit, check):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(
        limit=limit,
        after=dt.utcnow() - timedelta(weeks=2),
        check=check)

    if not len(deleted):
        em = discord.Embed(
            description=f"{ERROR} Could not find any messages to delete.\n"
                        f"```Messages older than 2 weeks cannot be deleted```",
            color=RED)
        return await ctx.send(embed=em)

    em = discord.Embed(
        description=f"{CHECK} Deleted {len(deleted, )} messages in {ctx.channel.mention}",
        color=GREEN)
    await ctx.send(embed=em, delete_after=2)


async def create_mute_role(bot, ctx):
    perms = discord.Permissions(
        send_messages=False, read_messages=True)
    mute_role = await ctx.guild.create_role(name='Muted', permissions=perms,
                                            reason='Could not find a muted role in the process of muting or unmuting.')

    await bot.config.update_one({"_id": ctx.guild.id},
                                {'$set': {"mute_role_id": mute_role.id}}, upsert=True)

    for channel in ctx.guild.channels:
        try:
            await channel.set_permissions(mute_role, read_messages=True, send_messages=False)

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

    return mute_role


async def send_punishment(bot, member, guild, action, moderator, reason, duration=None):
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
        if duration:
            em = discord.Embed(
                description=f"**Guild** - {guild}\n"
                            f"**Moderator** - {moderator.mention}\n"
                            f"**Action** - {action.title()}\n"
                            f"**Duration** - {duration}\n"
                            f"**Reason** - {reason}",
                colour=colour,
                timestamp=dt.utcnow())
            em.set_thumbnail(url=emote)
            await member.send(embed=em)

        else:
            em = discord.Embed(
                description=f"**Guild** - {guild}\n"
                            f"**Moderator** - {moderator.mention}\n"
                            f"**Action** - {action.title()}\n"
                            f"**Reason** - {reason}",
                colour=colour,
                timestamp=dt.utcnow())
            em.set_thumbnail(url=emote)
            await member.send(embed=em)

    except Exception as e:
        pass

    # send it to the log channel because why not lol
    data = await bot.config.find_one({"_id": guild.id})
    mod_logs = guild.get_channel(data['mod_logs'])

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
    em.set_footer(text='Case no. {}'.format(await get_last_caseid(bot, guild)))
    em.add_field(name='Member', value=member.mention, inline=False)
    em.add_field(name='Moderator', value=moderator.mention, inline=False)
    if duration:
        em.add_field(name='Duration', value=duration, inline=False)

    if reason:
        em.add_field(name='Reason', value=reason, inline=False)

    await mod_logs.send(embed=em)

    _action = action + ((' lasting ' + duration) if duration else '')
    # get the action + duration for formatting purposes

    await create_log(bot, member, guild, _action, moderator, reason)  # create the log


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
