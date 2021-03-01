import discord

# Colours, emotes, and useful stuff

MAIN = 0x5A00D8
RED = discord.Colour.red()
GREEN = discord.Colour.green()
DIFF_GREEN = 0x677c1e
DIFF_RED = 0xFF0000
GOLD = discord.Colour.gold()

ERROR = '<:SatError:804756495044444160>'
CHECK = '<:SatCheck:804756481831993374>'
BLANK = '\uFEFF'
LOCK = ':lock:'
UNLOCK = ':unlock:'
WEAK_SIGNAL = ':red_circle:'
MEDIUM_SIGNAL = ':yellow_circle:'
STRONG_SIGNAL = ':green_circle:'
SATURN = '<:Saturn:813806979847421983>'
NO_REPEAT = '⏭'
REPEAT_ONE = '🔂'
REPEAT_ALL = '🔁'
MUTE = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
       'speaker-with-cancellation-stroke_1f507.png'
UNMUTE = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
         'speaker-with-three-sound-waves_1f50a.png'
WARN = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
       'warning-sign_26a0.png'
NO_ENTRY = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
      'no-entry_26d4.png'
UNBAN = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/mozilla/36/' \
        'door_1f6aa.png'
# weird emotes and stuff yay?

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s(" \
            r")<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
SPOTIFY_URL_REGEX = r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*track[/:]*[A-Za-z0-9?=]+"
SPOTIFY_PLAYLIST_URL_REGEX = r"[\bhttps://open.\b]*spotify[\b.com\b]*[/:]*playlist[/:]*[A-Za-z0-9?=]+"
YOUTUBE_URL_REGEX = r"(?:https?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/" \
                    r"(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]+)"
INVITE_URL_REGEX = r"discord(?:\.com|app\.com|\.gg)/(?:invite/)?([a-zA-Z0-9\-]{2,32})"
# i barely understand these regexes omg

DUEL_HEAL_MESSAGES = [
    "{} drinks a chug jug and gains {} health!",
    "{} pulls out a first aid kit and uses it, replenishing {} hp!",
    "{} prays to the dueling gods and instantly regains {} health!",
    "{} found an exploit in the code and exploited it for {} hp!",
    "{} freezes time and waits 5 eternities to replenish {} health!",
    "{} gets a gift from the gods and gets an instant health boost of {}!",
    "{} heals {} hp!",
    "{} eats a golden apple for {} health!",
    "{} ender pearls to another dimension and slowly replenishes {} hp!",
    "{} ate a {} hp apple to keep the doctor away!",
]
DUEL_ATTACK_MESSAGES = [
    "{} does an impressive combo on {} for {} damage!",
    "{} steals all of {}'s lunch money, inflicts {} damage and throws them into the sun!",
    "{} absolutely DESTROYS {} for {} damage!",
    "{} forces {} to look at Synchronous' code and it deals {} damage!",
    "{} pulls out a machine gun and BLIZZASTED {} into shreds for {} damage!",
    "{} snipes {} from 2 MILES AWAY for {} damage!",
    "{} throws around {} like a small child, dealing {} damage!",
    "{} karate-chopped {} and broke all 206 bones of his body, dealing {} damage!",
    "{} nukes {} for {} damage!",
    "{} went a bit too far and dismembered {} for {} damage!",
    "{} punched {} so hard he got knocked into the next year, dealing {} damage!",
    "{} slammed {} into Davy Jones' locker, dealing {} damage!",
    "{} got a jetpack and flew it straight over {}'s head, burning away {} health!",
    "{} did some weird stuff and {} turned into a pile of ashes, eating up {} health!",
    "{} drove a car straight into {}, dealing {} damage!",
    "{} throws {} into the void, dealing {} damage!",
    "{} boiled up a huge pot of water and poured it onto {}, melting away {} health!",
    "{} did some crap from Harry Potter and suffocated {} for {} damage!",
    "{} slapped {} with a big stinky fish and destroyed {}'s sense of smell, dealing {} damage!",
    "{} forced {} to watch YouTube rewind and instantly lost {} health!",
    "{} did nothing, but {} accidentally walked off a cliff, instantly losing {} health!",
    "{} took a leaf out of Mad-Eye Moody's book and turned {} into a ferret, dealing {} damage!",
    "{} pulled out a stick and started whipping it at {}, dealing {} damage!",
    "{} drove a Jeep Wrangler over {} many times, dealing {} damage!",
    "{} pulled out a baseball bat and sent {}'s head flying, dealing {} damage!",
    "{} rickrolled {}, and lost {} health out of embarrassment!"
]