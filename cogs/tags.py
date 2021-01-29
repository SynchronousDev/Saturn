import string

from assets import *

class Tags(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.accepted_chars = string.ascii_letters + string.digits + '_-'

	@commands.command(
		name='tags',
		description='View all of your guild\'s tags')
	async def view_tags(self, ctx):
		tags = []
		cursor = self.bot.tags.find({"guild_id": ctx.guild.id})
		for document in await cursor.to_list(length=100):
			tags.append(document)

		found = False
		content = None

		em = discord.Embed(
			title='{0}\'s  Tags ({1})'.format(ctx.guild, len(tags)), colour=MAIN)

	@commands.group(
		name='tag',
		aliases=['t'],
		description='The tag group. Create tags for your guild.',
		invoke_without_command=True)
	async def tag_cmd(self, ctx, name):
		tags = []
		cursor = self.bot.tags.find({"guild_id": ctx.guild.id})
		for document in await cursor.to_list(length=100):
			tags.append(document)

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
		cursor = self.bot.tag_cmd.find({"guild_id": ctx.guild.id})
		for document in await cursor.to_list(length=100):
			tags.append(document)

		for tag in tags:
			if tag['name'] == str(name):
				em = discord.Embed(
					description=f"{ERROR} The tag `{name}` already exists.",
					colour=RED)
				await ctx.send(embed=em)

		data = {
			"guild_id": ctx.guild.id,
			"author": ctx.author.id,
			"name": name,
			"content": content
		}
		await self.bot.tag_cmd.insert_one(data)

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
		tags = []
		cursor = self.bot.tag_cmd.find({"guild_id": ctx.guild.id})
		for document in await cursor.to_list(length=100):
			tags.append(document)

		found = False

		for tag in tags:
			if tag['name'] == str(name):
				if tag['guild_id'] == ctx.guild.id:
					if tag['author'] == ctx.author.id:
						self.bot.tag_cmd.delete_one({"guild_id": ctx.guild.id, "name": str(name), "author": ctx.author.id})
						found = True

					else:
						em = discord.Embed(
							description=f"{ERROR} The tag `{name}` does not belong to you.",
							colour=RED)
						await ctx.send(embed=em)

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
        
def setup(bot):
	bot.add_cog(Tags(bot))