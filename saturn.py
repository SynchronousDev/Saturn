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

intents = discord.Intents.all()
mentions = discord.AllowedMentions.all()
mentions.everyone = False


# noinspection PyMethodMayBeStatic
class Saturn(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            description="A multipurpose discord bot made in python.",
            intents=intents,
            case_insensitive=True,
            owner_ids=[531501355601494026],
            allowed_mentions=mentions
        )
        self.ready = False
        self.__name__ = 'Saturn'
        self.src = 'https://github.com/SynchronousDev/saturn-discord-bot'

        self.path = Path(__file__).parents[0]
        self.path = str(self.path)
        self.__version__ = '1.1.0'

        self.mongo_connection_url = os.environ.get("MONGO")
        self.TOKEN = os.environ.get("TOKEN")

        self.edit_snipes = {}
        self.snipes = {}
        self.banned_users = {}
        self.muted_users = {}
        self.message_cache = {}

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

    # async def on_error(self, error, *args, **kwargs):
    #     if error == "on_command_error":
    #         em = SaturnEmbed(
    #             title="Something went wrong...",
    #             description="An unexpected event happened.",
    #             colour=RED
    #         )
    #         await self.stdout.send(embed=em)

    #     em = SaturnEmbed(
    #         title="An unexpected error occurred...",
    #         description="Please check logs for more details.",
    #         colour=RED
    #     )
    #     await self.stdout.send(embed=em)
    #     raise

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command and ctx.guild:
            if not ctx.guild.me.guild_permissions.send_messages:
                em = SaturnEmbed(
                    description=f"{WARNING} Oops! I can't send messages! Please update my permissions and try again.",
                    colour=GOLD)
                return await ctx.author.send(embed=em)

            elif not ctx.guild.me.guild_permissions.embed_links:
                return await ctx.send("Hey! Please enable the `Embed Links` permission for me!")

            elif not ctx.guild.me.guild_permissions.external_emojis:
                em = SaturnEmbed(
                    description=f"{WARNING} Oops! Please make sure that I have the following permissions:"
                                f"```Send Messages, Embed Links, Use External Emojis```",
                    colour=GOLD)
                return await ctx.send(embed=em)

            if await self.blacklists.find_one({"_id": ctx.author.id}):
                raise Blacklisted

            elif not self.ready:
                em = SaturnEmbed(
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

    # noinspection PyAttributeOutsideInit
    async def on_ready(self):
        self.default_guild = self.get_guild(793577103794634842)
        self.stdout = self.default_guild.get_channel(833871407544008704)
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
            em = SaturnEmbed(
                description=f"{CHECK} Connected and ready!",
                colour=GREEN)
            await self.stdout.send(embed=em)

        else:
            print(f"{self.__name__} reconnected")
            em = SaturnEmbed(
                description=f"{INFO} Reconnected!",
                colour=BLUE)
            await self.stdout.send(embed=em)

    async def on_message(self, message):
        await self.process_commands(message)

    @tasks.loop(minutes=1)
    async def change_pres(self):
        await self.change_presence(
            activity=discord.Game(name=f"I'm in beta."))


if __name__ == '__main__':
    # Load all of the cogs and initialize the databases
    Saturn = Saturn()
    Saturn.run()  # run the bot
    print("Event loop closed.")  # I can do this because it will not print until the event loop stops
    # all processes after this will not be run until the bot stops so oof
