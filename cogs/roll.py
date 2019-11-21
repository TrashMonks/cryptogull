"""Command to imitate an ingame dice roll. Can roll randomly, or return the summary of the roll."""
import logging

from discord import Colour, Embed
from discord.ext.commands import Cog, Context, command
from hagadias.dicebag import DiceBag

log = logging.getLogger('bot.' + __name__)


class Roll(Cog):
    """Takes a dice string argument and either returns the stats for it or use as a base to roll.
    Syntax: ?dice (dice string)"""

    @command()
    async def dice(self, ctx: Context, *args):
        """Returns the (min, max) Average (average)."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        val = ' '.join(args)
        try:
            avgval = DiceBag(val).average()
            minval = DiceBag(val).minimum()
            maxval = DiceBag(val).maximum()
            msg = f'{val}: ({minval}, {maxval}), average {avgval}'
        except ValueError as e:
            msg = f'{e}'
        embedded_msg = Embed(colour=Colour(0xf403f), description=msg)
        return await ctx.send(embed=embedded_msg)

    """Randomly rolls based on the string provided using Hagadias's dice roll helper.
    Syntax: ?roll (dice string)
    The dice string can only contain [0-9][d-+]. Unlike the Qud wiki module, it parses
    ranges ex. "1-5" as subtraction."""
    @command()
    async def roll(self, ctx: Context, *args):
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        val = ' '.join(args)
        if val == "":
            return await ctx.send("There needs to be a string specified!")
        try:
            shakeResult = DiceBag(val).shake()  # randomly roll using stat value
            msg = f':game_die: {val}: **{shakeResult}**!'
        except ValueError as e:
            msg = f'{e}'
        embedded_msg = Embed(colour=Colour(0xf403f), description=msg)
        return await ctx.send(embed=embedded_msg)
