from assets import *

# Admin invite: https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=8&redirect_uri
# =https://127.0.0.1:5000/login&scope=bot
# Recommended invite:
# https://discord.com/oauth2/authorize?client_id=799328036662935572&permissions=536145143&redirect_uri=https
# ://127.0.0.1:5000/login&scope=bot

log = logging.getLogger(__name__)


# TODO: Update help paginator, use custom paginator instead of discord.ext.menus

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Help(bot))
