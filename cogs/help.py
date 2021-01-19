from datetime import datetime as dt

import discord
from discord.ext import commands
from utils import *


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command(
        name='help',
        aliases=['h', 'commands'],
        description='The help command')
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def help(self, ctx):
        prefix = await retrieve_prefix(self.bot, ctx)
        em = discord.Embed(
            title="Selenium's Commands",
            description=f'Prefix for this server: `{prefix}`',
            colour=MAIN,
            timestamp=dt.utcnow())

        em.set_footer(text='Invoked by ' + ctx.author.name,
                      icon_url=self.bot.user.avatar_url)
        cogs = [c for c in self.bot.cogs.keys()]
        cogs.remove('Events')
        cogs.remove('Help')
        cogs.remove('Dev')

        for cog in cogs:
            text = "\n"
            # getting a certain cog from a list of cogs
            for command in self.bot.get_cog(cog).walk_commands():
                if command.hidden:  # if command is hidden
                    continue

                elif command.parent is not None: # if the command has a parent
                    
                    continue

                text += f"{command.name}\n"

            em.add_field(name=cog, value=f"```{text}```", inline=True)

        em.add_field(
            name='Quick Links',
            value='[Join the support server](https://discord.gg/HANGYrUF2y)\n'
                  '[Invite Selenium (Administrator)]'
                  '(https://discord.com/oauth2/authorize?client_id=793572249059196959&permissions=8&scope=bot)\n'
                  '[Invite Selenium (Recommended)]'
                  '(https://discord.com/oauth2/authorize?client_id=793572249059196959&permissions=501083383&scope=bot)',
            inline=False)

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Help(bot))
