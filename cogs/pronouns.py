"""Command for retrieving the in-game pronouns of a game Object."""
import logging

from discord.ext.commands import Bot, Cog, Context, command

from helpers.find_blueprints import find_name_or_displayname, fuzzy_find_nearest
from shared import genders, qindex

log = logging.getLogger('bot.' + __name__)


class Pronouns(Cog):
    """Find pronouns of in-game creatures."""
    def __init__(self, bot: Bot):
        self.bot = bot

    @command()
    async def pronouns(self, ctx: Context, *args):
        """Say the pronouns of this creature or character."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        try:
            obj = find_name_or_displayname(query, qindex)
        except LookupError:
            if len(query) < 3:
                msg = "Sorry, that specific blueprint name wasn't found, and it's too" \
                      " short to search."
                return await ctx.send(msg)
            # there was no exact match, and the query wasn't too short, so offer an alternative
            async with ctx.typing():
                obj = await fuzzy_find_nearest(query, qindex)
        if obj.pronouns is not None:
            result = obj.pronouns
        elif obj.gender is not None:
            gender = genders[obj.gender]
            result = '/'.join([gender['Subjective'],
                               gender['Objective'],
                               gender['PossessiveAdjective']])
        else:
            msg = f"`{obj.name}` (\"{obj.displayname}\") has neither pronouns nor a gender" \
                  " specified. Their pronouns may be randomly determined or determined by other" \
                  " in-game rules."
            await ctx.send(msg)
            return
        msg = f"Pronouns for `{obj.name}` (\"{obj.displayname}\"): {result}"
        await ctx.send(msg)
