import discord
from discord.ext import commands

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @commands.group(
        name='tag',
        aliases=['t'],
        description='The tag group. Create tags for your guild.'
    )
    async def tags(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='tag')

    @tags.command(
        name='create',
        aliases=['new'],
        description='Creates a new tag.')
    async def new_tag(self, ctx):
        pass
    
def setup(bot):
    bot.add_cog(Tags(bot))