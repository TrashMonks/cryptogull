"""Commands for querying the Caves of Qud object tree."""
import logging

from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command
from fuzzywuzzy import process

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class BlueprintQuery(Cog):
    """Query Caves of Qud game blueprints."""

    def __init__(self, bot: Bot):
        """Build a cache of object IDs and display names for faster searching."""
        self.bot = bot
        self.ids = [qid for qid in qindex]
        self.displaynames = [qobject.displayname for qobject in qindex.values()]

    @command()
    async def blueprint(self, ctx: Context, *args):
        """Search both blueprint names and display names with at least two characters."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query) or len(query) < 2:
            return await ctx.send_help(ctx.command)
        id_matches_raw = process.extract(query, self.ids, limit=5)
        id_matches = [match[0] for match in id_matches_raw]
        id_indices = [self.ids.index(match) for match in id_matches]
        displayname_matches_raw = process.extract(query, self.displaynames, limit=5)
        displayname_matches = [match[0] for match in displayname_matches_raw]
        displayname_indices = [self.displaynames.index(match) for match in displayname_matches]
        embed = Embed(description="Matches:")
        # build embed field for ID matches
        field = []
        for index in id_indices:
            field.append(f"`{self.ids[index]}` ('{self.displaynames[index]}')")
        embed.add_field(name='Blueprint names (and display name):',
                        value='\n'.join(field),
                        inline=True)
        # build embed field for display name matches
        field = []
        for index in displayname_indices:
            field.append(f"'{self.displaynames[index]}' (`{self.ids[index]}`)")
        embed.add_field(name='Display names (and blueprint name):',
                        value='\n'.join(field),
                        inline=True)
        await ctx.send(embed=embed)
