import os
from pathlib import Path

import motor.motor_asyncio
from discord.ext import tasks
from dotenv import load_dotenv

from assets import *

load_dotenv()

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(module)s | %(message)s")

handler = logging.FileHandler(filename='saturn.log', encoding='utf-8', mode='w')
handler.setFormatter(formatter)

logger.addHandler(handler)


# noinspection PyMethodMayBeStatic
class Saturn(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            description="A multipurpose discord bot made in python.",
            intents=discord.Intents.all(),
            case_insensitive=True,
            owner_ids=[531501355601494026, 704355591686062202]
        )
        self.ready = False
        self.__name__ = 'Saturn'
        self.src = 'https://github.com/SynchronousDev/saturn-discord-bot'

        self.path = Path(__file__).parents[0]
        self.path = str(self.path)
        self.__version__ = '1.1.0'
        print("Loading info from .env file...")

        self.mongo_connection_url = os.environ.get("MONGO")
        self.TOKEN = os.environ.get("TOKEN")

        self.edit_snipes = {}
        self.snipes = {}
        self.banned_users = {}
        self.muted_users = {}
        self.message_cache = {}

        print("Initializing database...")
        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(self.mongo_connection_url))
        self.db = self.mongo[self.__name__]
        self.config = self.db["config"]
        self.mutes = self.db["mutes"]
        self.blacklists = self.db["blacklists"]
        self.tags = self.db["tags"]
        self.mod = self.db["mod"]
        self.bans = self.db["bans"]
        self.starboard = self.db["starboard"]

    def run(self):
        print(f"Running {self.__name__}...")
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command and ctx.guild:
            if await self.blacklists.find_one({"_id": ctx.author.id}):
                raise Blacklisted

            elif not self.ready:
                em = discord.Embed(
                    description=f"{WARNING} I'm not quite ready to receive commands yet!",
                    colour=GOLD)
                return await ctx.send(embed=em)

        await self.invoke(ctx)

    async def on_connect(self):
        self.change_pres.start()
        print(f"{self.__name__} connected")

    async def on_disconnect(self):
        self.change_pres.cancel()
        print(f"{self.__name__} disconnected")

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            for _file in os.listdir(self.path + '/cogs'):
                if _file.endswith('.py') and not _file.startswith('_'):
                    print(f"Loading {_file[:-3]} cog...")
                    self.load_extension(f"cogs.{_file[:-3]}")  # load all of the cogs

            self.load_extension('jishaku')  # i have jishaku here because i find it quite useful

            mutes, bans = [], []
            print("Initializing mute and ban cache...")
            async for _doc in self.mutes.find({}): mutes.append(_doc)
            for mute in mutes: self.muted_users[mute["_id"]] = mute
            async for _doc in self.bans.find({}): bans.append(_doc)
            for ban in bans: self.banned_users[ban["_id"]] = ban

            print(f"{self.__name__} is ready")

        else:
            print(f"{self.__name__} reconnected")

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.CommandNotFound):
            pass

    async def on_message(self, message):
        await self.process_commands(message)

    @tasks.loop(minutes=1)
    async def change_pres(self):
        await self.change_presence(
            activity=discord.Game(name=f"{PREFIX}help | V{self.__version__}"))


if __name__ == '__main__':
    # Load all of the cogs and initialize the databases
    Saturn = Saturn()
    Saturn.run()  # run the bot
    print("Event loop closed.")  # I can do this because it will not print until the event loop stops
    # all processes after this will not be run until the bot stops so oof
