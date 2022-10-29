"""Command to imitate an ingame dice roll. Can roll randomly, or return the summary of the roll."""
import logging

from discord import Colour, Embed
from discord.ext.commands import Cog, Context, command
from hagadias.dicebag import DiceBag

log = logging.getLogger('bot.' + __name__)


class Dice(Cog):
    """Simulate or roll dice from dice strings, like `2d6+3`."""

    @command()
    async def dice(self, ctx: Context, *args):
        """Give statistical information about a dice string.

        Example strings: `14d8`, `4d6+5`, `1d8+1d6+1d4`"""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        val = ''.join(args)
        if len(val) < 3:  # this argument is way too short, you don't need a bot for this.
            return await ctx.send("That string is too short to be parsed (< 3 characters).")
        try:
            avgval = DiceBag(val).average()
            minval = DiceBag(val).minimum()
            maxval = DiceBag(val).maximum()
            msg = f'Expected value: {avgval} (minimum: {minval}, maximum: {maxval})'
        except ValueError as e:
            msg = f'{e}'
        embedded_msg = Embed(colour=Colour(0xf403f), description=msg)
        return await ctx.send(embed=embedded_msg)

    # Randomly rolls based on the string provided using Hagadias's dice roll helper.
    # Syntax: ?roll (dice string)
    # The dice string can only contain [0-9][d-+]. Unlike the Qud wiki module, it parses
    # ranges ex. "1-5" as subtraction.
    @command()
    async def roll(self, ctx: Context, *args):
        """Simulate a roll of a dice string.

        Example strings: `14d8`, `4d6+5`, `1d8+1d6+1d4`"""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        val = ''.join(args)
        if val == "":
            return await ctx.send("There needs to be a string specified!")
        if len(val) < 3:  # This argument is way too short, you don't need a bot for this.
            return await ctx.send("That string is too short to be parsed (< 3 characters)")
        try:
            result = DiceBag(val).shake()  # randomly roll using stat value
            msg = f':game_die: {val}: **{result}**!'
        except ValueError as e:
            msg = f'{e}'
        embedded_msg = Embed(colour=Colour(0xf403f), description=msg)
        return await ctx.send(embed=embedded_msg)
