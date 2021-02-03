from discord.ext import commands

"""
Some custom erros I can raise for stuff
Wooooooooooooooo
"""

class AlreadyConnectedToChannel(commands.CommandError):
    pass

class RoleNotHighEnough(commands.CommandError):
    pass

class BotRoleNotHighEnough(commands.CommandError):
    pass

class TrackDoesNotExist(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidRepeatMode(commands.CommandError):
    pass