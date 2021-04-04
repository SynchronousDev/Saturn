from assets import *

# Admin invite: https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=8&redirect_uri
# =https://127.0.0.1:5000/login&scope=bot
# Recommended invite:
# https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=536145143&redirect_uri=https
# ://127.0.0.1:5000/login&scope=bot

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.unlisted_cogs = ("Events", "ErrorHandler", "Reaction Roles", "Dev", "Jishaku", 'Help')

    @staticmethod
    async def can_run(command, ctx) -> bool:
        """
        Check if a command can be run by the author.
        """
        try:
            if await command.can_run(ctx):
                return True

            else:
                return False

        except commands.CommandError:
            return False

    async def full_command_syntax(self, ctx: commands.Context, command: commands.Command) -> str or False:
        """
        Get the full command syntax.
        """
        if await self.can_run(command, ctx):
            if not command.parent:
                return await syntax(command)

            else:
                return f" ↳ {await syntax(command)}"

        else:
            return False

    async def cog_command_syntax(self, ctx: commands.Context, command: commands.Command) -> str or False:
        if await self.can_run(command, ctx):
            if not command.parent:
                return f"**{command.name} {'(has subcommands)' if isinstance(command, commands.Group) else ''}" \
                       f"**\n`{await syntax(command)}` - {command.description}\n "

        else:
            return False

    async def send_command_help(self, ctx, command):
        em = discord.Embed(
            title=f'Help for command {command.name}',
            description=command.description,
            colour=MAIN,
            timestamp=utc()
        )
        em.add_field(name='Syntax', value=await self.full_command_syntax(ctx, command))
        if command.aliases:
            em.add_field(name='Aliases', value=', '.join(command.aliases))

        cooldown = command.get_cooldown_retry_after(ctx)
        if cooldown > 0:
            em.add_field(name='Cooldown Remaining', value=convert_time(int(cooldown)))

        await ctx.send(embed=em)

    @commands.command(
        name='help',
        aliases=['h', 'commands', 'command', 'helpdesk'],
        description='The help command. Shows this message.'
    )
    async def help_command(self, ctx, *, entity: typing.Optional[str]):
        cogs = [c for c in self.bot.cogs]
        for cog in self.unlisted_cogs:
            cogs.remove(cog)

        entries = []

        # use this ↳ for subcommands

        # just command signature on general paginator
        # command signature and description on cog paginator, including cog description
        # command signature, description, cooldown, checks and stuff on command paginator

        if not entity:
            title = ["Saturn's Commmands"]
            title.extend(cogs)

            entries.append(
                f"Saturn is a multipurpose discord bot.\n"
                f"[Invite (Recommended)]({NORMAL_INVITE})\n"
                f"[Invite (Administrator)]({ADMIN_INVITE})\n\n" +
                '\n'.join([f"`Page {index} - {c}`" for index, c in enumerate(cogs, start=1)]) +
                f"\n\nPress the numbers emote to skip to a page.")
            for cog in cogs:
                _cog = self.bot.get_cog(cog)
                pages = ""

                for command in _cog.walk_commands():
                    invoke = await self.full_command_syntax(ctx, command)
                    if invoke:
                        pages += f"`{invoke}`\n"

                entries.append(pages)

            if not entries:
                entries = "There are no commands in this module that you have access too. Womp womp..."

            pager = Paginator(
                change_title=title,
                entries=entries, length=1,
                colour=MAIN)
            await pager.start(ctx)

        else:
            _cog = (str(entity).lower()).title()
            _cmd = str(entity).lower()
            filtered_commands = flatten(
                [[c for c in self.bot.get_cog(cog).walk_commands()] for cog in self.unlisted_cogs]
            )

            if entity.lower() == 'modules':
                desc = 'Need to know what commands are in a module? No worries!\nJust run ' \
                       'the help command and add in the module name.\n\n' + \
                       '\n'.join([f'`{str(cog).lower()}`' for cog in cogs])
                em = discord.Embed(
                    title="Saturn's Modules",
                    description=desc,
                    timestamp=utc(),
                    colour=MAIN
                )
                em.set_footer(text="Make sure the name of the module is exactly the same as listed above.")
                return await ctx.send(embed=em)

            elif cog := self.bot.get_cog(_cog) and _cog not in self.unlisted_cogs:
                for command in cog.walk_commands():
                    invoke = await self.cog_command_syntax(ctx, command)
                    if invoke:
                        entries.append(str(invoke))

                pager = Paginator(
                    title=f"Commands in the {cog.qualified_name} module",
                    entries=entries, length=6,
                    colour=MAIN)
                return await pager.start(ctx)

            elif command := self.bot.get_command(_cmd):
                if command in filtered_commands and ctx.author.id in self.bot.owner_ids:
                    return await self.send_command_help(ctx, command)
                elif command not in filtered_commands:
                    return await self.send_command_help(ctx, command)

            # TODO: get started on working on individual command help I guess

            em = discord.Embed(
                description=f"{ERROR} Command/module `{entity}` does not exist (or is not listed).",
                colour=RED)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Help(bot))