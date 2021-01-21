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
from discord.ext.buttons import Paginator

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
                f"{(' ' if minutes else '') + str(int(seconds)) + 's' if seconds else ('0s' if not day and not hour and not minutes else '')}`")

    except TypeError:
        return 'indefinitely'

async def syntax(command, ctx, bot):
    params = []

    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(
                value) else f"<{key}>")

    params = " ".join(params)
    prefix = await retrieve_prefix(bot, ctx)

    return f"```{str(command)} {params}```"

async def retrieve_prefix(bot, message):
    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return "sl!"
        return data["prefix"]
    except:
        return "sl!"

async def send_punishment(member, guild, action, moderator, reason, duration=None):
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

"""
A helper section for using mongo db
Class document aims to make using mongo calls easy, saves
needing to know the syntax for it. Just pass in the db instance
on init and the document to create an instance on and boom
"""


class Document:
    def __init__(self, connection, document_name):
        """
        Our init function, sets up the conenction to the specified document
        Params:
         - connection (Mongo Connection) : Our database connection
         - documentName (str) : The document this instance should be
        """
        self.db = connection[document_name]
        self.logger = logging.getLogger(__name__)

    # <-- Pointer Methods -->
    async def update(self, dict):
        """
        For simpler calls, points to self.update_by_id
        """
        await self.update_by_id(dict)

    async def get_by_id(self, id):
        """
        This is essentially find_by_id so point to that
        """
        return await self.find_by_id(id)

    async def find(self, id):
        """
        For simpler calls, points to self.find_by_id
        """
        return await self.find_by_id(id)

    async def delete(self, id):
        """
        For simpler calls, points to self.delete_by_id
        """
        await self.delete_by_id(id)

    # <-- Actual Methods -->
    async def find_by_id(self, id):
        """
        Returns the data found under `id`
        Params:
         -  id () : The id to search for
        Returns:
         - None if nothing is found
         - If somethings found, return that
        """
        return await self.db.find_one({"_id": id})

    async def delete_by_id(self, id):
        """
        Deletes all items found with _id: `id`
        Params:
         -  id () : The id to search for and delete
        """
        if not await self.find_by_id(id):
            raise MemberNotFound

        await self.db.delete_many({"_id": id})

    async def insert(self, dict):
        """
        insert something into the db
        Params:
        - dict (Dictionary) : The Dictionary to insert
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        await self.db.insert_one(dict)

    async def upsert(self, dict):
        """
        Makes a new item in the document, if it already exists
        it will update that item instead
        This function parses an input Dictionary to get
        the relevant information needed to insert.
        Supports inserting when the document already exists
        Params:
         - dict (Dictionary) : The dict to insert
        """
        if await self.__get_raw(dict["_id"]) != None:
            await self.update_by_id(dict)
        else:
            await self.db.insert_one(dict)

    async def update_by_id(self, dict):
        """
        For when a document already exists in the data
        and you want to update something in it
        This function parses an input Dictionary to get
        the relevant information needed to update.
        Params:
         - dict (Dictionary) : The dict to insert
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$set": dict})

    async def unset(self, dict):
        """
        For when you want to remove a field from
        a pre-existing document in the collection
        This function parses an input Dictionary to get
        the relevant information needed to unset.
        Params:
         - dict (Dictionary) : Dictionary to parse for info
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$unset": dict})

    async def increment(self, id, amount, field):
        """
        Increment a given `field` by `amount`
        Params:
        - id () : The id to search for
        - amount (int) : Amount to increment by
        - field () : field to increment
        """
        if not await self.find_by_id(id):
            return

        await self.db.update_one({"_id": id}, {"$inc": {field: amount}})

    async def get_all(self):
        """
        Returns a list of all data in the document
        """
        data = []
        async for document in self.db.find({}):
            data.append(document)
        return data

    # <-- Private methods -->
    async def __get_raw(self, id):
        """
        An internal private method used to eval certain checks
        within other methods which require the actual data
        """
        return await self.db.find_one({"_id": id})
