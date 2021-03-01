import os

import motor.motor_asyncio
from discord.ext import tasks

from assets import *

# import speed
# can't forget to import speed guys


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

default_prefix = "s."


# noinspection PyShadowingNames
async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or(default_prefix)(bot, message)

    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        if not data or "prefix" not in data:
            return commands.when_mentioned_or(default_prefix)(bot, message)

        return commands.when_mentioned_or(data["prefix"])(bot, message)

    except Exception:
        return commands.when_mentioned_or(default_prefix)(bot, message)

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=discord.Intents.all(),
    case_insensitive=True,
    owner_ids=[531501355601494026])
bot.cwd = Path(__file__).parents[0]
bot.cwd = str(bot.cwd)
bot.version = '1.0.0'

bot.configuration = json.load(open(bot.cwd + '/assets/configuration.json'))

bot.muted_users = {}
bot.banned_users = {}
bot.snipes = {}
bot.config_token = bot.configuration['token']
bot.connection_url = bot.configuration['mongo']
bot.spotify_client_id = bot.configuration['spotify_client_id']
bot.spotify_client_secret = bot.configuration['spotify_client_secret']

@bot.event
async def on_ready():
    # The on ready event. Fires when the bot is ready
    print(f"------\nLogged in as {bot.user.name}"
          f" (ID {bot.user.id})\n------\nTime: {dt.now()}\n------")

    data = []
    async for document in bot.mutes.find({}):
        data.append(document)

    for mute in data:
        bot.muted_users[mute["_id"]] = mute

    bans = []
    async for document in bot.bans.find({}):
        bans.append(document)

    for ban in bans:
        bot.banned_users[ban["_id"]] = ban


@bot.event
async def on_connect():
    change_pres.start()
    print("------\nSaturn connected")


@bot.event
async def on_disconnect():
    print("------\nSaturn disconnected")
    change_pres.cancel()


@tasks.loop(minutes=1)
async def change_pres():
    await bot.change_presence(
        activity=discord.Game(name=f"in {len(bot.guilds)} server and {len(bot.users)} users"
                                   f" | {default_prefix}help | Version {bot.version}"))


@bot.before_invoke
async def blacklist_check(ctx):
    if await bot.blacklists.find_one({"_id": ctx.author.id}) is not None:
        raise Blacklisted

    else:
        pass

if __name__ == '__main__':
    """Load all of the cogs and initialize the databases"""
    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["saturn"]
    bot.config = bot.db["config"]
    bot.mutes = bot.db["mutes"]
    bot.blacklists = bot.db["blacklists"]
    bot.tags = bot.db["tags"]
    bot.mod = bot.db["mod"]
    bot.bans = bot.db["bans"]
    bot.starboard = bot.db["starboard"]

    for file in os.listdir(bot.cwd + '/cogs'):
        if file.endswith('.py') and not file.startswith('_'):
            bot.load_extension(f"cogs.{file[:-3]}")

    bot.load_extension('jishaku') # i have jishaku here because i find it quite useful

    bot.run(bot.config_token)  # run the bot
    # all processes after this will not be run until the bot stops so oof
