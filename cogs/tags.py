import discord
from discord.ext import commands
import string

from utils import *

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.accepted_chars = string.ascii_letters + string.digits + '_-'

    @commands.group(
        name='tag',
        aliases=['t'],
        description='The tag group. Create tags for your guild.',
        invoke_without_command=True
    )
    async def tags(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='tag')

    @tags.command(
        name='create',
        aliases=['new'],
        description='Creates a new tag.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def new_tag(self, ctx, name, *, content):
        for letter in name:
            if letter not in list(self.accepted_chars):
                em = discord.Embed(
                    description=f"{ERROR} The tag `{content}` contains unacceptable characters. "
                                f"Tag names can only contain letters, digits, hyphens and underscores.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        data = {
            "guild_id": ctx.guild.id,
            "author": ctx.author.id,
            "name": name,
            "content": content
        }
        await self.bot.tags.insert_one(data)

        em = discord.Embed(
            description=f"{CHECK} The tag `{name}` was created.",
            colour=MAIN)
        await ctx.send(embed=em)

    @tags.command(
        name='delete',
        aliases=['del'],
        description='Delets an existing tag.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def delete_tag(self, ctx, name):
        data = await self.bot.tags.find(ctx.guild.id)


        em = discord.Embed(
            description=f"{CHECK} The tag `{name}` was deleted.",
            colour=MAIN)
        await ctx.send(embed=em)
    
def setup(bot):
    bot.add_cog(Tags(bot))