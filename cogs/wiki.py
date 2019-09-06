import logging

from discord.ext import commands

log = logging.getLogger('bot.' + __name__)


class Wiki(commands.Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wiki(self, ctx, args):
        pass
