import contextlib
import inspect
import io
import re
import textwrap
import traceback
# from traceback import format_exception

from assets import *

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.env = {}
        self.stdout = io.StringIO()

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    # TODO: add command to reset cooldowns for any command (global?)

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def test(self, ctx):
        await ctx.send(convert_to_timestamp(utc()))

    @commands.command(
        name='blacklist',
        aliases=['bl'],
        description='A developer command. Blacklists a user from using the bot.')
    async def blacklist_cmd(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = 'no reason provided'):
        await self.bot.blacklists.update_one({"_id": member.id},
                                             {'$set': {"reason": reason}}, upsert=True)

        em = SaturnEmbed(
            description=f"{CHECK} Blacklisted {member.mention} for `{reason}`.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='unblacklist',
        aliases=['ubl'],
        description='A developer command. Unblacklists a user from using the bot.')
    async def unblacklist_cmd(self, ctx, member: discord.Member, *,
                              reason: typing.Optional[str] = 'no reason provided'):
        try:
            await self.bot.blacklists.delete_one({"_id": member.id})

        except commands.MemberNotFound:
            em = SaturnEmbed(
                description=f"{ERROR} {member.mention} is not blacklisted from this bot.",
                colour=RED)
            await ctx.send(embed=em)

        em = SaturnEmbed(
            description=f"{CHECK} Unblacklisted {member.mention} for `{reason}`.",
            colour=GREEN)
        await ctx.send(embed=em)

    @commands.command(
        name='eval',
        aliases=['ev', 'exec', 'evaluate'],
        description='The eval command. Executes code (only accessible by me)')
    async def eval(self, ctx, *, code):
        code = code.strip("`")
        if re.match('py(thon)?\n', code):
            code = "\n".join(code.split("\n")[1:])

        if code == 'exit':
            self.env = {}
            em = SaturnEmbed(
                description=f"{CHECK} Exiting session and clearing envs.",
                colour=GREEN)
            return await ctx.send(embed=em)

        envs = {
            "discord": discord,
            "commands": commands,
            "ctx": ctx,
            "bot": self.bot,
            "self": self,
            "datetime": datetime,
            "inspect": inspect,
            "contextlib": contextlib,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "member": ctx.author,
            "msg": ctx.message
        }
        self.env.update(envs)

        # noinspection RegExpAnonymousGroup
        if not re.search(  # Check if it's an expression
                r"^(return|import|for|while|def|class|raise|print"
                r"from|exit|[a-zA-Z0-9]+\s*=)", code, re.M) and len(
                    code.split("\n")) == 1:
            code = "_ = " + code

        code_ = f"""
async def func():
    try:
        with contextlib.redirect_stdout(self.stdout):
{textwrap.indent(code, '            ')}
        if '_' in locals():
            if inspect.isawaitable(_):
                _ = await _
            return _
    finally:
        self.env.update(locals())
"""
        try:
            exec(code_, self.env)
            func = self.env['func']
            res = await func()
            colour = DIFF_GREEN

        except Exception:
            res = traceback.format_exc()
            colour = DIFF_RED

        res = str(res)

        pager = Paginator(
            entries=[res[i: i + (2000 - len(code))]
                     for i in range(0, len(res), (2000 - len(code)))],
            length=1,
            colour=colour,
            title="Eval Job Completed" if colour == DIFF_GREEN else "Eval Failed",
            footer=f'{self.bot.__name__} Eval command',
            prefix=f"```py\n{code.strip('_ = ')}```\n```py\n",
            suffix='```'
        )

        await pager.start(ctx)

    @commands.command(
        name='logout',
        aliases=['exit'],
        description='A developer command. Closes the websocket connection and logs the bot out.')
    async def logout_cmd(self, ctx):
        em = SaturnEmbed(
            description=f"{CHECK} Closing the websocket connection.",
            color=GREEN)
        await ctx.send(embed=em, delete_after=2)

        await self.bot.logout()

    @commands.command(
        name='global_toggle',
        aliases=['gtoggle', 'gt'],
        description='A developer command. Enable or disable commands globally.')
    async def global_toggle(self, ctx, *, command):
        _command = self.bot.get_command(command)

        if not _command:
            em = SaturnEmbed(
                description=f"{ERROR} Command `{command}` does not exist.",
                colour=RED)
            return await ctx.send(embed=em)

        elif ctx.command == _command or _command in [c for c in self.bot.get_cog('Dev').walk_commands()] \
                or _command == self.bot.get_command('help'):
            em = SaturnEmbed(
                description=f"{ERROR} This command cannot be disabled.",
                colour=RED)
            return await ctx.send(embed=em)

        else:
            _command.enabled = not _command.enabled
            for _cmd in self.bot.get_cog(_command.cog.qualified_name).walk_commands():
                if _cmd.parent == _command:
                    _cmd.enabled = not _cmd.enabled

            status = "enabled" if _command.enabled else "disabled"
            em = SaturnEmbed(
                description=f"{CHECK} {status.title()} `{_command.qualified_name}` and its subcommands.",
                color=GREEN)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Dev(bot))
