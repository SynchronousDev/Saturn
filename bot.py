import os

from discord.ext import tasks

import motor.motor_asyncio

from assets import *


logging.basicConfig(level=logging.INFO)
default_prefix = "sl!"

async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or(default_prefix)(bot, message)

    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or(default_prefix)(bot, message)

        return commands.when_mentioned_or(data["prefix"])(bot, message)

    except:
        return commands.when_mentioned_or(default_prefix)(bot, message)

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=discord.Intents.all(),
    case_insensitive=True,
    owner_id=531501355601494026)
bot.cwd = Path(__file__).parents[0]
bot.cwd = str(bot.cwd)
bot.version = '0.0.1'

bot.configuration = json.load(open(bot.cwd + '/assets/configuration.json'))

print('{}\n------'.format(bot.cwd))

bot.muted_users = {}
bot.config_token = bot.configuration['token']
bot.connection_url = bot.configuration['mongo']
bot.spotify_client_id = bot.configuration['spotify_client_id']
bot.spotify_client_secret = bot.configuration['spotify_client_secret']

bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
bot.db = bot.mongo["seleniumV2"]
bot.config = bot.db["config"]
bot.mutes = bot.db["mutes"]
bot.blacklists = bot.db["blacklists"]
bot.tags = bot.db["tags"]

@bot.event
async def on_ready():
    # The on ready event. Fires when the bot is ready
    print(f"------\nLogged in as {bot.user.name}"
          f" (ID {bot.user.id})\n------\nTime: {dt.now()}")

    data = []
    async for document in bot.mutes.find({}):
        data.append(document)

    for mute in data:
        bot.muted_users[mute["_id"]] = mute

    change_pres.start()

@bot.event
async def on_connect():
    print("------\nSelenium connected")

@bot.event
async def on_disconnect():
    print("------\nSelenium disconnected")
    change_pres.cancel()


@tasks.loop(minutes=1)
async def change_pres():
    await bot.change_presence(
        activity=discord.Game(name=f"in {len(bot.guilds)} server and {len(bot.users)} users"
                                   f" | sl!help | Version {bot.version}"))

@bot.before_invoke
async def blacklist_check(ctx):
    if await bot.blacklists.find_one({"_id": ctx.author.id}) is not None:
        raise Blacklisted

    else:
        pass 
    

if __name__ == '__main__':
    for file in os.listdir(bot.cwd + '/cogs'):
        if file.endswith('.py') and not file.startswith('_'):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)
    print("Running Selenium")
