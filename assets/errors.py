from discord.ext import commands

# custom errors

class AlreadyConnectedToChannel(commands.CommandError):
    """Bot is already connected to another channel"""
    pass

class RoleNotHighEnough(commands.CommandError):
    """Raises when the command invoker's role is not higher than the target's role"""
    pass

class IsAdministrator(commands.CommandError):
    """Raises when the member is an administrator, in the mute commands"""
    pass

class InvalidLimit(commands.CommandError):
    """For the purge commands. Raises when the limit is either below 1 or above 1000"""
    pass

class BotRoleNotHighEnough(commands.CommandError):
    """Raises when the bot's role is not higher than the target's role"""
    pass

class Blacklisted(commands.CommandError):
    """Raises when a member is blacklisted"""
    pass
