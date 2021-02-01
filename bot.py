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
version = '0.0.1'

configuration = json.load(open(bot.cwd + '/assets/configuration.json'))

print('{}\n------'.format(bot.cwd))

bot.muted_users = {}
bot.config_token = configuration['token']
bot.connection_url = configuration['mongo']
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
                                   f" | sl!help | Version {version}"))


@bot.event
async def on_message(message):
    if not message.author.bot:
        if (user := await bot.blacklists.find_one({"_id": message.author.id})) is not None:
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
    for file in os.listdir(bot.cwd + '/cogs'):
        if file.endswith('.py') and not file.startswith('_'):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)
    print("Running Selenium")
