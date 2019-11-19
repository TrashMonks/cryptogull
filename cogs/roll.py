"""Command to imitate an ingame dice roll. Can roll randomly, or return the summary of the roll."""
from hagadias.helpers import DiceBag
import logging

from discord import Colour, Embed
from discord.ext.commands import Cog, Context, command

log = logging.getLogger('bot.' + __name__)


class Roll(Cog):
    """Takes a dice string argument and either returns the stats for it or use as a base to roll.
    Syntax: ?dice (dice string)"""

    @command()
    async def dice(self, ctx: Context, *args):
        """Returns the (min, max) Average (average)."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        val = ' '.join(args)
        avg = DiceBag(val).average()
        min = DiceBag(val).minimum()
        max = DiceBag(val).maximum()
        msg = f'{val}: ({min}, {max}), average {avg}'
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
            return await ctx.send("There needs to be a string specified in a parsable way!")
        shakeResult = DiceBag(val).shake()  # randomly roll using stat value
        msg = f'{val}: **{shakeResult}**!'
        embedded_msg = Embed(colour=Colour(0xf403f), description=msg)
        return await ctx.send(embed=embedded_msg)
