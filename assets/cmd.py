from .strings import *
from .constants import *
from discord.ext import commands

# noinspection PyShadowingNames, PyBroadException, SpellCheckingInspection
async def get_prefix(bot, message) -> commands.when_mentioned_or():
    """
    For the bot's command_prefix. Not the same as the `retrieve_prefix` function.
    """
    # sphagetto code galore
    if not message.guild: return commands.when_mentioned_or(PREFIX)(bot, message)
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        if not data or not data['prefix']: return commands.when_mentioned_or(PREFIX)(bot, message)

        if isinstance(data['prefix'], str):
            return commands.when_mentioned_or(data['prefix'])(bot, message)

        pre = flatten(data['prefix'])
        return commands.when_mentioned_or(*pre)(bot, message)

    except Exception as e:
        return commands.when_mentioned_or(PREFIX)(bot, message)

# noinspection SpellCheckingInspection
async def syntax(cmd) -> str:
    """
    Get the syntax/usage for a command.
    """
    params = []

    for key, value in cmd.params.items():
        if key not in ("self", "ctx"):
            value = str(value)

            if key.lower() == 'time_and_reason':  # this is a special case for the timed bans and mute commands
                params.append("[time] [reason]")  # both are optional

            elif "optional" in value.lower() or "greedy" in value.lower():
                params.append(f"[{key}]")

            else:
                params.append(f"<{key}>")

    params = " ".join(params)
    return f"{str(cmd.qualified_name)} {params}"

# noinspection PyBroadException
async def retrieve_raw_prefix(bot, message) -> list:
    """
    A method for retrieving the raw prefix out of the database
    """
    try:
        data = await bot.config.find_one({"_id": message.guild.id})

        # make sure that we have a prefix in the data
        if not data or not data["prefix"]:
            return PREFIX

        # we don't have to put anything into the database
        # because it's always going to be s. unless they enter stuff into the database
        # and when they change the prefix it gets inserted into the db
        else:
            return data['prefix']

    except Exception:
        return PREFIX

async def error_arg_syntax(cmd, arg):
    cmd_syntax = await syntax(cmd)
    chars = cmd_syntax.rpartition(arg)[0]

    spaces = chars.count(' ')  # calculate how many spaces are in the sentence before the args
    num_of_letters = len(''.join(chars.split(' ')))  # get the number of letters minus the spaces

    before_pointers = ' ' * (spaces + num_of_letters)  # get the number of spaces before the pointer
    pointers = '^' * len(arg)

    return f"{cmd_syntax}\n{before_pointers}{pointers}"  # return the syntax with the ^^^^^ under
    # to indicate which argument is parsed wrongly

async def retrieve_prefix(bot, message) -> str:
    """
    Return the prefix as a readable string of prefixes.
    """
    prefix = await retrieve_raw_prefix(bot, message)
    if isinstance(prefix, str):
        return prefix
    elif isinstance(prefix, list):
        prefix = flatten(prefix)
        return ' | '.join(prefix)

async def starboard_embed(message, payload) -> discord.Embed:
    """
    Create a starboard embed
    """
    desc = message.content  # if not isinstance(message, discord.Embed) else message
    em = discord.Embed(
        colour=GOLD,
        description=desc,
        timestamp=utc()
    )

    # attachments
    if len(message.attachments):
        attachment = message.attachments[0]

        em.add_field(name='Attachments', value=f"[{attachment.filename}]({attachment.url})", inline=False)
        em.set_image(url=attachment.url)

    # support for embeds
    if len(message.embeds):
        embed = message.embeds[0]
        em_desc = ""
        if embed.title: em_desc += f"__**{embed.title}**__\n"
        if embed.description: em_desc += (embed.description + '\n')
        if embed.fields:
            field = embed.fields[0]
            em.add_field(name=field.name, value=field.value, inline=False)

        if embed.footer: em_desc += embed.footer
        if embed.image:
            em.add_field(name='Embed Image', value=f"[Attachment]({embed.image.url})", inline=False)
            em.set_image(url=embed.image.url)

        if embed.thumbnail:
            em.add_field(name='Embed Image', value=f"[Attachment]({embed.thumbnail.url})", inline=False)
            em.set_image(url=embed.thumbnail.url)

        em.description = em_desc

    em.add_field(name='Original Message', value=f"[Jump!](https://discord.com/channels/"
                                                f"{payload.guild_id}/{payload.channel_id}/{message.id})")

    em.set_author(icon_url=message.author.avatar_url, name=message.author)
    em.set_footer(text=f'Message ID - {message.id}')
    return em
