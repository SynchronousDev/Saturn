from assets import *

# Admin invite: https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=8&redirect_uri
# =https://127.0.0.1:5000/login&scope=bot
# Recommended invite:
# https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=536145143&redirect_uri=https
# ://127.0.0.1:5000/login&scope=bot

log = logging.getLogger(__name__)


# TODO: Update help paginator, use custom paginator instead of discord.ext.menus

# noinspection SpellCheckingInspection
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.unlisted_cogs = ("Events", "ErrorHandler", "Reaction Roles", "Dev", "Jishaku", 'Help')

    @staticmethod
    async def full_command_syntax(ctx, command):
        try:
            if await command.can_run(ctx):
                pass

            else:
                return False

        except commands.CommandError:
            return False

        if not command.parent:
            return await syntax(command)

        else:
            return f" ↳ {await syntax(command)}"

    @commands.command(
        name='help',
        aliases=['h', 'commands', 'command', 'helpdesk'],
        description='The help command. Shows this message.'
    )
    async def help_command(self, ctx, entity: t.Optional[str]):
        cogs = [c for c in self.bot.cogs]
        for cog in self.unlisted_cogs:
            cogs.remove(cog)

        entries = []

        # use this ↳ for subcommands

        # just command signature on general paginator
        # command signature and description on cog paginator, including cog description
        # command signature, description, cooldown, checks and stuff on command paginator

        if not entity:
            for cog in cogs:
                _cog = self.bot.get_cog(cog)
                pages = ""

                for command in _cog.walk_commands():
                    invoke = await self.full_command_syntax(ctx, command)
                    if invoke:
                        pages += f"`{invoke}`\n"

                if not pages:
                    pages = "There are no commands in this module that you have access too. Womp womp..."

                entries.append(pages)

            pager = Paginator(
                change_title=cogs,
                entries=entries, length=1,
                colour=MAIN)
            await pager.start(ctx)

        else:
            if self.bot.get_command(entity):
                await ctx.send("TBD")


def setup(bot):
    bot.add_cog(Help(bot))
