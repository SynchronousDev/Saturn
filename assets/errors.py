from discord.ext import commands

"""
Some custom erros I can raise for stuff
Wooooooooooooooo
"""

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

class TrackDoesNotExist(commands.CommandError):
    """Raises when a remove_track is performed and no tracks were found"""
    pass

class NoVoiceChannel(commands.CommandError):
    """Not connected to a voice channel"""
    pass

class QueueIsEmpty(commands.CommandError):
    """Raiases when, as the name implies, the queue is empty"""
    pass

class Blacklisted(commands.CommandError):
    """Raises when a member is blacklisted"""
    pass

class NoTracksFound(commands.CommandError):
    """Raises when a ytsearch:query is performed and no tracks were found"""
    pass

class UrlNotFound(commands.CommandError):
    """Raises when an invalid url is parsed"""
    pass

class PlayerIsAlreadyPaused(commands.CommandError):
    """The player is already paused"""
    pass

class NoMoreTracks(commands.CommandError):
    """There are no more tracks in the queue"""
    pass

class NoPreviousTracks(commands.CommandError):
    """Raises when the `previous` command is called and there are no more tracks in the queue"""
    pass

class InvalidRepeatMode(commands.CommandError):
    """Raises when an invalid repeat mode was specified"""
    pass