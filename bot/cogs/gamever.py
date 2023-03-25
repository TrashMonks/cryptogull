"""Command to report the current version of Caves of Qud being used by the bot."""
import logging

from discord.ext.commands import Cog, Context, command

from bot.shared import gameroot

log = logging.getLogger('bot.' + __name__)


class GameVersion(Cog):
    @command()
    async def gameversion(self, ctx: Context):
        """Report the version of Caves of Qud being used by the bot."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        msg = f"Current Caves of Qud version being used is {gameroot.gamever}."
        await ctx.send(msg)
