import typing as t
from aiohttp import request
from assets import *
import random

log = logging.getLogger(__name__) 


class Miscellaneous(commands.Cog):
    """
    The Miscellaneous cog. These are commands that are just fun, and can spice up the chat.

    Warning: The commands in the Miscellaneous cog are not the same as the commands in the Utility cog.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='echo',
        aliases=['quote', 'say'],
        description='Quote your message in chat for others to see!')
    @commands.cooldown(
        1, 3, commands.BucketType.member)
    async def quote_cmd(self, ctx, channel: t.Optional[discord.TextChannel], *, quote: str):
        channel = channel or ctx.channel
        author = ctx.author
        await channel.send(f'*"{quote}"*\n\n - {author.mention}')

    @commands.command(
        name='anonymousecho',
        aliases=['aquote', 'asay', 'aecho'],
        description='Quote your message in chat for others to see!')
    @commands.cooldown(
        1, 3, commands.BucketType.member)
    async def anonymous_quote_cmd(self, ctx, channel: t.Optional[discord.TextChannel], *, quote: str):
        channel = channel or ctx.channel
        author = ctx.author
        await channel.send(f'*"{quote}"*\n\n - Anonymous')

    @commands.command(
        name='fact',
        aliases=['facts'],
        description='Get Animal facts. API may be down sometimes, but still reliable.')
    @commands.cooldown(
        1, 3, commands.BucketType.member)
    async def fact_cmd(self, ctx, animal: str):
        if animal.lower() in ("dog", "cat", 'panda', 'fox', 'bird', 'koala'):
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
                    fact_em = discord.Embed(
                        title=f"{animal.title()} fact",
                        description=data['fact'],
                        color=MAIN)
                    if IMAGE_URL is not None:
                        fact_em.set_image(url=image_link)
                    else:
                        pass
                    await ctx.send(embed=fact_em)
                    return
                if response.status == 503:
                    status = discord.Embed(
                        description=f"{ERROR} API is currently offline",
                        color=RED)
                    await ctx.send(embed=status)
                else:
                    status = discord.Embed(
                        description=f"{ERROR} API returned with a response status `{response.status}`",
                        color=RED)
                    await ctx.send(embed=status)
        else:
            no_facts = discord.Embed(
                description=f"{ERROR} API could not find any facts for animal `{animal}`",
                color=RED)
            await ctx.send(embed=no_facts)

    @commands.command(
        name='rps', aliases=['rockpaperscissors'],
        description='Play rock paper scissors with the bot! '
                    'This is not rigged and is generated via the `random` module.')
    @commands.cooldown(1, 1, commands.BucketType.member)
    async def rps_cmd(self, ctx, choice):
        if choice.startswith('r'):
            choice = 'rock'

        elif choice.startswith('s'):
            choice = 'scissors'

        elif choice.startswith('p'):
            choice = 'paper'

        def random_choice(options=None):
            if options is None:
                options = ["rock", "paper", "scissors"]
            return random.choice(options)

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
                    win = discord.Embed(
                        description=f"```You chose {choice}\nSaturn chose {computer_choice}```",
                        color=GREEN)
                    win.set_author(icon_url=ctx.author.avatar_url, name='You won!')
                    await ctx.send(embed=win)

                elif winning_choice == computer_choice:
                    loss = discord.Embed(
                        description=f"```You chose {choice}\nSaturn chose {computer_choice}```",
                        color=RED)
                    loss.set_author(icon_url=ctx.author.avatar_url, name='You lost!')
                    await ctx.send(embed=loss)
            else:
                tie = discord.Embed(
                    description=f"```You both chose {choice}```",
                    color=GOLD)
                tie.set_author(icon_url=ctx.author.avatar_url, name='You tied!')
                await ctx.send(embed=tie)
        else:
            invalid_choice = discord.Embed(
                description=f"{ERROR} Expected either `rock`, `paper` or `scissors`, not `{choice}`",
                color=RED)
            await ctx.send(embed=invalid_choice)

    @commands.command(
        name='rolldice', aliases=['rd', 'dice', 'roll'],
        description='Rolls some dice, with yourself? Or maybe roll a rick. Optional dice values.')
    @commands.cooldown(1, 2, commands.BucketType.member)
    async def roll_dice(self, ctx, amount: t.Union[str, int], value: t.Optional[int]):
        value = value or 6
        if amount.isdigit():
            amount = int(amount)

            if amount <= 10:
                rolls = [random.randint(1, value) for i in range(amount)]

                em = discord.Embed(
                    description=('\n'.join(f"**Dice {i + 1}** rolled a **{roll}**"
                                           for i, roll in enumerate(rolls))
                                 + f"```Total !sum - {sum(rolls)}```"),
                    color=MAIN)
                em.set_author(icon_url=ctx.author.avatar_url, name=f"{ctx.author.name}'s Dice Roll")
                await ctx.send(embed=em)

            else:
                em = discord.Embed(
                    description=f"{ERROR} Cannot roll that many dice. Maximum number of dice is `10`",
                    color=RED)
                await ctx.send(embed=em)

        elif amount.isalpha():
            await ctx.send("https://www.youtube.com/watch?v=dQw4w9WgXcQ Well, you asked for it!")

    @commands.command(
        name="8ball",
        aliases=['8b'],
        description='Ask the magic 8 ball a question, and you will get an answer! Not the most reliable psychic.')
    async def _8ball(self, ctx):
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
        await ctx.reply(f'{random.choice(responses)}')


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
