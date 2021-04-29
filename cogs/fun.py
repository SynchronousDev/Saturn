from discord.ext.commands.converter import clean_content
from assets.cmd import Dueler
import io
import random
from io import BytesIO

from PIL import Image
from aiohttp import request

from assets import *

log = logging.getLogger(__name__)


# noinspection SpellCheckingInspection
class Fun(commands.Cog):
	"""
	The Fun module. These are commands that are just fun, and can spice up the chat.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		name='echo',
		aliases=['quote', 'say'],
		description='Quote your message in chat for others to see!')
	@commands.cooldown(
		1, 3, commands.BucketType.member)
	async def quote_cmd(self, ctx, channel: typing.Optional[discord.TextChannel], *, quote: str):
		channel = channel or ctx.channel

		await channel.send(f'*"{quote}"*\n\n- **{ctx.author}**')

	@commands.command(
		name='anonymousecho',
		aliases=['aquote', 'asay', 'aecho'],
		description='Quote your message in chat for others to see!')
	@commands.cooldown(
		1, 3, commands.BucketType.member)
	async def anonymous_quote_cmd(self, ctx, channel: typing.Optional[discord.TextChannel], *, quote: str):
		if not channel:
			await ctx.message.delete()

		else:
			await ctx.message.add_reaction(CHECK)

		await channel.send(f'*"{quote}"*\n\n- **Someone**')


	@commands.command(
		name='animalfact',
		aliases=['animalfacts', 'afacts', 'afact'],
		description='Get animal facts. API may be down sometimes, but still reliable.')
	@commands.cooldown(
		1, 2, commands.BucketType.member)
	async def animal_fact_cmd(self, ctx, *, animal: typing.Optional[str]):
		async with ctx.channel.typing():
			animals = ("dog", "cat", 'panda', 'fox', 'bird', 'koala')
			animal = animal or random.choice(animals)
			if animal not in animals:
				em = SaturnEmbed(
					description=f"{ERROR} Could not find any facts for `{animal}`.",
					color=RED)
				return await ctx.send(embed=em)

			URL = f'https://some-random-api.ml/facts/{animal.lower()}'
			IMAGE_URL = f"https://some-random-api.ml/img/{'birb' if animal == 'bird' else animal.lower()}"

			async with request('GET', IMAGE_URL, headers={}) as response:
				if response.status == 200:
					data = await response.json()
					image_link = data['link']

				else:
					image_link = None

			async with request('GET', URL, headers={}) as response:
				if response.status == 200:
					data = await response.json()
					fact_em = SaturnEmbed(
						title=f"Did you know?",
						description=data['fact'],
						color=MAIN)
					if IMAGE_URL is not None:
						fact_em.set_image(url=image_link)
					fact_em.set_footer(text='some-random-api.ml')
					return await ctx.send(embed=fact_em)

				if response.status == 503:
					status = SaturnEmbed(
						description=f"{ERROR} API is currently offline.",
						color=RED)
					return await ctx.send(embed=status)

				else:
					status = SaturnEmbed(
						description=f"{ERROR} API returned with a response status `{response.status}`",
						color=RED)
					return await ctx.send(embed=status)

	@commands.command(
		name='wasted',
		aliases=['waste'],
		description='Apply a wasted overlay to someone\'s avatar!'
	)
	@commands.cooldown(1, 1, commands.BucketType.member)
	async def wasted_avatar(self, ctx, member: typing.Optional[discord.Member]):
		async with ctx.channel.typing():
			member = member or ctx.author
			URL = f"https://some-random-api.ml/canvas/wasted/?avatar=" \
				  f"{member.avatar_url_as(format='png')}"
			async with request('GET', URL, headers={}) as response:
				if response.status == 200:
					data = io.BytesIO(await response.read())
					file = discord.File(data, 'wasted.jpg')
					em = SaturnEmbed(
						title=f"Wasted...",
						color=RED)
					em.set_image(url=f"attachment://wasted.jpg")
					em.set_footer(text='some-random-api.ml')
					return await ctx.send(embed=em, file=file)

				if response.status == 503:
					status = SaturnEmbed(
						description=f"{ERROR} API is currently offline.",
						color=RED)
					await ctx.send(embed=status)

				else:
					status = SaturnEmbed(
						description=f"{ERROR} API returned with a response status `{response.status}`",
						color=RED)
					await ctx.send(embed=status)

	@commands.command(
		name='rainbow',
		aliases=['rainbowify', 'party', 'skittle'],
		description='Apply a rainbow overlay to someone\'s avatar!'
	)
	@commands.cooldown(1, 1, commands.BucketType.member)
	async def rainbowify_avatar(self, ctx, member: typing.Optional[discord.Member]):
		async with ctx.channel.typing():
			member = member or ctx.author
			URL = f"https://some-random-api.ml/canvas/gay/?avatar=" \
				  f"{member.avatar_url_as(format='png')}"
			async with request('GET', URL, headers={}) as response:
				if response.status == 200:
					data = io.BytesIO(await response.read())
					file = discord.File(data, 'rainbow.jpg')
					em = SaturnEmbed(
						title=f"SKITTLE OVERLOAD...",
						color=discord.Colour.random()
					)
					em.set_image(url=f"attachment://rainbow.jpg")
					em.set_footer(text='some-random-api.ml')
					return await ctx.send(embed=em, file=file)

				if response.status == 503:
					status = SaturnEmbed(
						description=f"{ERROR} API is currently offline.",
						color=RED)
					await ctx.send(embed=status)

				else:
					status = SaturnEmbed(
						description=f"{ERROR} API returned with a response status `{response.status}`",
						color=RED)
					await ctx.send(embed=status)

	@commands.command(
		name='triggered',
		aliases=['trigger'],
		description='Apply a triggered overlay to someone\'s avatar!'
	)
	@commands.cooldown(1, 1, commands.BucketType.member)
	async def triggered_avatar(self, ctx, member: typing.Optional[discord.Member]):
		async with ctx.channel.typing():
			member = member or ctx.author
			URL = f"https://some-random-api.ml/canvas/triggered/?avatar=" \
				  f"{member.avatar_url_as(format='png')}"
			async with request('GET', URL, headers={}) as response:
				if response.status == 200:
					data = io.BytesIO(await response.read())
					file = discord.File(data, 'triggered.gif')
					em = SaturnEmbed(
						title=f"Very triggered indeed...",
						color=discord.Colour.orange()
					)
					em.set_image(url=f"attachment://triggered.gif")
					em.set_footer(text='some-random-api.ml')
					return await ctx.send(embed=em, file=file)

				if response.status == 503:
					status = SaturnEmbed(
						description=f"{ERROR} API is currently offline.",
						color=RED)
					await ctx.send(embed=status)

				else:
					status = SaturnEmbed(
						description=f"{ERROR} API returned with a response status `{response.status}`",
						color=RED)
					await ctx.send(embed=status)

	@commands.command(
		name='rps', aliases=['rockpaperscissors'],
		description='Play rock paper scissors with the bot! '
					'This is not rigged and outputs generated via the `random` module.')
	@commands.cooldown(1, 1, commands.BucketType.member)
	async def rps_cmd(self, ctx, choice):
		if choice.startswith('r'):
			choice = 'rock'

		elif choice.startswith('s'):
			choice = 'scissors'

		elif choice.startswith('p'):
			choice = 'paper'

		def random_choice(opts=None):
			if opts is None:
				opts = ["rock", "paper", "scissors"]

			return random.choice(opts)

		def determine_winner(choice1, choice2):
			winners = {
				"rock": {
					"rock": None,
					"paper": "paper",
					"scissors": "rock",
				},
				"paper": {
					"rock": "paper",
					"paper": None,
					"scissors": "scissors",
				},
				"scissors": {
					"rock": "rock",
					"paper": "scissors",
					"scissors": None,
				},
			}

			winner = winners[choice1][choice2]

			return winner

		options = ["rock", "paper", "scissors"]

		if choice in options:
			computer_choice = random_choice(options)

			winning_choice = determine_winner(choice, computer_choice)

			if winning_choice:
				if winning_choice == choice:
					win = SaturnEmbed(
						description=f"```You chose {choice}\n{self.bot.__name__} chose {computer_choice}```",
						color=GREEN)
					win.set_author(icon_url=ctx.author.avatar_url, name='You won!')
					await ctx.send(embed=win)

				elif winning_choice == computer_choice:
					loss = SaturnEmbed(
						description=f"```You chose {choice}\n{self.bot.__name__} chose {computer_choice}```",
						color=RED)
					loss.set_author(icon_url=ctx.author.avatar_url, name='You lost!')
					await ctx.send(embed=loss)
			else:
				tie = SaturnEmbed(
					description=f"```You both chose {choice}```",
					color=GOLD)
				tie.set_author(icon_url=ctx.author.avatar_url, name='You tied!')
				await ctx.send(embed=tie)
		else:
			invalid_choice = SaturnEmbed(
				description=f"{ERROR} Expected either `rock`, `paper` or `scissors`, not `{choice}`",
				color=RED)
			await ctx.send(embed=invalid_choice)

	@commands.command(
		name='rolldice', aliases=['rd', 'dice', 'roll'],
		description='Rolls some dice, with yourself? Or maybe roll a rick. Optional dice values.')
	@commands.cooldown(1, 2, commands.BucketType.member)
	async def roll_dice(self, ctx, amount: typing.Union[str, int], value: typing.Optional[int]):
		value = value or 6
		if amount.isdigit():
			amount = int(amount)

			if amount <= 100:
				# noinspection PyUnusedLocal
				rolls = [random.randint(1, value) for i in range(amount)]

				em = SaturnEmbed(
					description=f"```You rolled a {sum(rolls)}!```",
					color=MAIN)
				em.set_author(icon_url=ctx.author.avatar_url, name=f"{ctx.author.name}'s Dice Roll")
				return await ctx.send(embed=em)

			else:
				em = SaturnEmbed(
					description=f"{ERROR} {self.bot.__name__} tries to roll `{amount}` "
								f"dice but gets confused and fails.",
					color=RED)
				await ctx.send(embed=em)

		elif amount.isalpha():
			em = SaturnEmbed(
				title="Definitely not a suspicious link!",
				description="[Click me!](https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
				colour=MAIN)
			await ctx.send(embed=em)

		else:
			em = SaturnEmbed(
				description=f"{ERROR} {self.bot.__name__} tries to roll `{amount}` dice but gets confused and fails.",
				color=RED)
			await ctx.send(embed=em)

	@commands.command(
		name="8ball",
		aliases=['8b'],
		description='Ask the magic 8 ball a question, and you will get an answer! Not the most reliable psychic.')
	async def _8ball(self, ctx, *, question):
		# Define possible responses
		responses = ['It is certain',
					 'It is decidedly so',
					 'Without a doubt',
					 'Yes, definitely',
					 'You may rely on it',
					 'As I see it, yes',
					 'Most likely',
					 'Outlook is good',
					 'Yes',
					 'Signs indicate yes',
					 'Reply hazy, try again',
					 'Ask again later',
					 'Better not tell you now',
					 'I can\'t give a prediction at this time',
					 'Concentrate and ask again later',
					 'Don\'t count on it',
					 'No',
					 'Simon doesn\'t say so',
					 'My sources say no',
					 'Outlook is not so good',
					 'Very doubtful']
		yes = [
			'It is certain',
			'It is decidedly so',
			'Without a doubt',
			'Yes, definitely',
			'You may rely on it',
			'As I see it, yes',
			'Most likely',
			'Outlook is good',
			'Yes',
			'Signs indicate yes',
			'Duh... obviously yes'
		]
		em = SaturnEmbed(
			title=f'The Magic {self.bot.__name__} Ball',
			colour=ctx.author.colour,
			timestamp=utc()
		)

		em.add_field(
			name=question + '?',
			value=(random.choice(responses) + '.') if ctx.author.id != 531501355601494026 else random.choice(yes))
		em.set_thumbnail(url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36"
							 "/billiards_1f3b1.png")
		await ctx.reply(embed=em)

	@commands.command(
		name='duel',
		aliases=['fight'],
		description='Duel another person! Attacks are random.'
	)
	async def duel_member(self, ctx, member: discord.Member):
		p1, p2, play = Dueler(ctx.author), Dueler(member), True
		order = [(p1, p2), (p2, p1)]

		em = SaturnEmbed(
			title=f'Duel between {ctx.author.name} and {member.name}',
			timestamp=utc(),
			colour=MAIN
		)
		em.set_footer(text='Damage amounts are generated via the random module.')

		versus = Image.open(self.bot.path + "/assets/imgs/versus.jpg")

		asset, _asset = ctx.author.avatar_url_as(size=128), member.avatar_url_as(size=128)
		data, _data = BytesIO(await asset.read()), BytesIO(await _asset.read())
		p1_pfp, p2_pfp = Image.open(data), Image.open(_data)

		p1_pfp = p1_pfp.resize((164, 164))
		p2_pfp = p2_pfp.resize((164, 164))

		versus.paste(p1_pfp, (39, 63))
		versus.paste(p2_pfp, (416, 214))

		versus.save(self.bot.path + "/assets/imgs/profile.jpg")
		file = discord.File(self.bot.path + "/assets/imgs/profile.jpg", filename='profile.jpg')
		em.set_image(url=f"attachment://profile.jpg")
		msg = await ctx.send(file=file, embed=em)

		await asyncio.sleep(3)
		await msg.edit(embed=em)

		text = []
		while play:
			for attacker, defender in order:
				if attacker.health < 1:
					play = False
					break

				elif defender.health < 1:
					play = False
					break

				amount = random.randint(10, 50) 
				will_attack = random.choice([True, False, True])

				# if it returns True then member attacks
				# it's a 2/3 chance that the member will attack
				symbol, colour = '+' if not will_attack else '-', \
								 DIFF_GREEN if not will_attack else DIFF_RED
				if not will_attack:
					text.append("{} {}".format(symbol, random.choice(DUEL_HEAL_MESSAGES).format(attacker.name)))
					attacker.heal(amount if not (attacker.health + amount > 100) else (100 - attacker.health))

				else:
					text.append("{} {}".format(
						symbol, random.choice(DUEL_ATTACK_MESSAGES).format(attacker.name, defender.name)))
					defender.damage(amount if not (defender.health - amount < 0) else defender.health)

				em.description = "**{}** - {} HP\n**{}** - {} HP\n```diff\n{}```".format(
					p1.name, p1.health, p2.name, p2.health,
					'\n'.join(text[len(text) - 8:] if len(text) > 8 else text)
				)

				em.colour = colour
				await msg.edit(embed=em)
				await asyncio.sleep(1)

		winner = p1 if p1.health > p2.health else p2
		# noinspection PyUnusedLocal
		loser = p1 if winner == p2 else p2
		em.title = f":trophy: {winner.member.name.upper()} WINS!"
		em.colour = GOLD
		await msg.edit(embed=em)


def setup(bot):
	bot.add_cog(Fun(bot))
