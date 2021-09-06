"""Commands for querying the Caves of Qud object tree."""
import asyncio
import concurrent.futures
import io
import logging
from functools import partial

from discord import Embed, File
from discord.ext import commands
from fuzzywuzzy import process

from helpers.find_blueprints import find_name_or_displayname
from shared import qindex

log = logging.getLogger('bot.' + __name__)


class BlueprintQuery(commands.Cog):
    """Query Caves of Qud game blueprints."""

    def __init__(self, bot: commands.Bot):
        """Build a cache of object IDs and display names for faster searching."""
        self.bot = bot
        self.ids = [qid for qid in qindex]
        self.displaynames = [qobject.displayname for qobject in qindex.values()]

    @commands.command()
    async def blueprint(self, ctx: commands.Context, *args):
        """Search both blueprint names and display names with at least two characters."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query) or len(query) < 2:
            return await ctx.send_help(ctx.command)
        loop = asyncio.get_running_loop()
        async with ctx.typing():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                call = partial(process.extract, query, self.ids, limit=5)
                id_matches_raw = await loop.run_in_executor(pool, call)
            id_matches = [match[0] for match in id_matches_raw]
            id_indices = [self.ids.index(match) for match in id_matches]
            with concurrent.futures.ThreadPoolExecutor() as pool:
                call = partial(process.extract, query, self.displaynames, limit=5)
                displayname_matches_raw = await loop.run_in_executor(pool, call)
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

    @commands.command()
    async def xml(self, ctx: commands.Context, *args):
        """Display the XMl source of a specific blueprint."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query) or len(query) < 2:
            return await ctx.send_help(ctx.command)
        try:
            obj = find_name_or_displayname(query, qindex)
        except LookupError:
            response = f'Sorry, could not find any blueprint called `{query}`. Try using ' \
                       'the "blueprint" command to find the blueprint you are looking for.'
            return await ctx.send(response)
        str_as_file = io.StringIO('  ' + obj.source)  # indent first <object> tag
        return await ctx.send('', file=File(fp=str_as_file, filename=obj.name + '.xml',
                                            spoiler=True))
