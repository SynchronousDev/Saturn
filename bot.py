import asyncio
import json
import logging
import os
import typing as t
from datetime import datetime as dt

import discord
from discord.ext import commands

import motor.motor_asyncio

from utils import *

print('{}\n------'.format(cwd))

secret_file = json.load(open(cwd + '/config/secrets.json'))
logging.basicConfig(level=logging.INFO)

async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("sl!")(bot, message)

    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or("sl!")(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except:
        return commands.when_mentioned_or("sl!")(bot, message)


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=discord.Intents.all(),
    case_insensitive=True,
    owner_id=531501355601494026)
bot.config_token = secret_file['token']
bot.connection_url = secret_file['mongo']

@bot.event
async def on_ready():
    # The on ready event. Fires when the bot is ready
    print(f"------\nLogged in as {bot.user.name} (ID {bot.user.id})\n------")

    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["seleniumV2"]
    bot.config = Document(bot.db, "config")
    bot.blacklists = Document(bot.db, "blacklists")

    await bot.change_presence(
        activity=discord.Game(name=f"in {len(bot.guilds)} server and {len(bot.users)} users | sl!help"))

@bot.event
async def on_message(message):
    if not message.author.bot:           
        if (user := await bot.blacklists.find_by_id(message.author.id)) is not None:
            if (message.content.startswith(await retrieve_prefix(bot, message)) and 
                len(message.content) > (len(await retrieve_prefix(bot, message)))):
                em = discord.Embed(
                        description=f"{ERROR} You are blacklisted from using this bot.",
                        colour=RED)
                await message.channel.send(embed=em)
                return
        pass

    await bot.process_commands(message)

if __name__ == '__main__':
    for file in os.listdir(cwd+'/cogs'):
        if file.endswith('.py') and not file.startswith('_'):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)
