import string
import typing as t

from assets import *

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Tags(commands.Cog):
    """
    The Tags module. Includes all commands that are related to making tags.

    Not much else other than tags in this module.
    """
    def __init__(self, bot):
        self.bot = bot
        self.accepted_chars = string.ascii_letters + string.digits + '_-'

    async def get_tag_content(self, ctx):
        tags = []
        cursor = self.bot.tags.find({"guild_id": ctx.guild.id})
        for document in await cursor.to_list(length=100):
            tags.append(document)

        return tags

    @commands.command(
        name='tags',
        description='View all of your guild\'s tags')
    async def view_tags(self, ctx):
        tags = await self.get_tag_content(ctx)
        em = discord.Embed(
            title='{0}\'s Tags ({1})'.format(ctx.guild, len(tags)), colour=MAIN)

        desc = []
        for tag in tags:
            desc.append(tag['name'])

        em.description = '`' + ', '.join(desc) + '`' if len(desc) \
            else 'This guild does not have any tags!'

        await ctx.send(embed=em)

    @commands.group(
        name='tag',
        aliases=['t'],
        description='The tag group. Create tags for your guild.',
        invoke_without_command=True)
    async def tag_cmd(self, ctx, name: t.Optional[str], member: t.Optional[discord.Member]):
        if not name:
            await ctx.invoke(self.bot.get_command('help'), entity='tag')
            return

        if member:
            tags = []
            cursor = self.bot.tags.find({"guild_id": ctx.guild.id, "author": member.id})
            for document in await cursor.to_list(length=100):
                tags.append(document)

        else:
            tags = await self.get_tag_content(ctx)

        found = False
        content = None

        for tag in tags:
            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    content = tag['content']
                    found = True

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        await ctx.send(content)

    @tag_cmd.command(
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

        tags = []
        cursor = self.bot.tags.find({"guild_id": ctx.guild.id})
        for document in await cursor.to_list(length=100):
            tags.append(document)

        for tag in tags:
            if tag['name'] == str(name):
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` already exists.",
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
            colour=GREEN)
        await ctx.send(embed=em)

    @tag_cmd.command(
        name='delete',
        aliases=['del'],
        description='Delets an existing tag.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def delete_tag(self, ctx, name):
        tags = await self.get_tag_content(ctx)

        found = False

        for tag in tags:
            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    if tag['author'] == ctx.author.id:
                        self.bot.tags.delete_one({"guild_id": ctx.guild.id, "name": str(name), "author": ctx.author.id})
                        found = True

                    else:
                        em = discord.Embed(
                            description=f"{ERROR} The tag `{name}` does not belong to you.",
                            colour=RED)
                        await ctx.send(embed=em)
                        return

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        em = discord.Embed(
            description=f"{CHECK} The tag `{name}` was deleted.",
            colour=GREEN)
        await ctx.send(embed=em)

    @tag_cmd.command(
        name='raw',
        description='Gets a tag\'s raw content. This means no markdown.')
    async def raw_tag(self, ctx, name):
        tags = await self.get_tag_content(ctx)

        found = False
        content = None

        for tag in tags:
            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    content = tag['content']
                    found = True

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        await ctx.send('```\n' + content + '```')

    @tag_cmd.command(
        name='rename',
        aliases=['retitle'],
        description='Renames a tag.')
    async def rename_tag(self, ctx, name, new_name):
        tags = await self.get_tag_content(ctx)

        found = False

        for tag in tags:
            if tag['name'] == str(new_name):
                em = discord.Embed(
                    description=f"{ERROR} A tag already exists with a name or alias `{new_name}`",
                    colour=RED)
                await ctx.send(embed=em)
                return

            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    if tag['author'] == ctx.author.id:
                        self.bot.tags.update_one(
                            {"guild_id": ctx.guild.id, "name": name},
                            {'$set': {"name": new_name}}, upsert=True)
                        found = True

                    else:
                        em = discord.Embed(
                            description=f"{ERROR} The tag `{name}` does not belong to you.",
                            colour=RED)
                        await ctx.send(embed=em)
                        return

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        em = discord.Embed(
            description=f"{CHECK} The tag `{name}` was renamed to `{new_name}`",
            colour=GREEN)
        await ctx.send(embed=em)

    @tag_cmd.command(
        name='edit',
        aliases=['ed'],
        description='Edits a tag.')
    async def edit_tag(self, ctx, name, *, new_content):
        tags = await self.get_tag_content(ctx)

        found = False

        for tag in tags:
            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    if tag['author'] == ctx.author.id:
                        self.bot.tags.update_one(
                            {"guild_id": ctx.guild.id, "name": str(name), "author": ctx.author.id},
                            {'$set': {"content": new_content}}, upsert=True)
                        found = True

                    else:
                        em = discord.Embed(
                            description=f"{ERROR} The tag `{name}` does not belong to you.",
                            colour=RED)
                        await ctx.send(embed=em)
                        return

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        em = discord.Embed(
            description=f"{CHECK} The tag `{name}` was edited.",
            colour=GREEN)
        await ctx.send(embed=em)

    @tag_cmd.command(
        name='owner',
        aliases=['transferowner', 'ownership', 'author'],
        description='Transfer a tag\'s owner to someone else.')
    async def transfer_tag_ownership(self, ctx, name, new_author: discord.Member):
        tags = await self.get_tag_content(ctx)

        found = False

        for tag in tags:
            if tag['name'] == str(name):
                if tag['guild_id'] == ctx.guild.id:
                    if tag['author'] == ctx.author.id:
                        self.bot.tags.update_one(
                            {"guild_id": ctx.guild.id, "name": str(name), "author": ctx.author.id},
                            {'$set': {"author": new_author}}, upsert=True)
                        found = True

                    else:
                        em = discord.Embed(
                            description=f"{ERROR} The tag `{name}` does not belong to you.",
                            colour=RED)
                        await ctx.send(embed=em)
                        return

        else:
            if not found:
                em = discord.Embed(
                    description=f"{ERROR} The tag `{name}` does not exist.",
                    colour=RED)
                await ctx.send(embed=em)
                return

        em = discord.Embed(
            description=f"{CHECK} The tag `{name}`'s author has "
                        f"been transferred to {new_author.mention}.",
            colour=GREEN)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Tags(bot))
