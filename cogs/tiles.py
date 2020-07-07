"""Commands for sending rendered game tiles as attachments."""
import asyncio
import concurrent.futures
import logging
import random

from discord import File
from discord.ext.commands import Cog, Context, command
from fuzzywuzzy import process
from hagadias.qudtile import QUD_COLORS, QudTile

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    @command()
    async def tile(self, ctx: Context, *args, smalltile=False):
        """Send the tile for the named Qud blueprint.

        Optional postfix: recolor color1 color2
        Append this to the command to recolor the tile with color1 as the tile color and color2
        as the detailcolor.  color1 and color2 should be Qud color codes like 'w' and 'c'."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if 'recolor' in query:
            query, recolor = [q.strip() for q in query.split('recolor')]
        else:
            recolor = ''
        # search for exact matches first
        obj = None
        for key, val in qindex.items():
            if query.lower() == key.lower():
                obj = val
                break
        if obj is None:
            # no matching blueprint name
            # but, is there a blueprint with a matching displayname?
            for blueprint, qobject in qindex.items():
                print(qobject.displayname)
                if qobject.displayname.lower() == query.lower():
                    obj = qobject
        if obj is None:
            if len(query) < 3:
                msg = "Sorry, that specific blueprint name wasn't found, and it's too" \
                      " short to search."
                return await ctx.send(msg)
            # there was no exact match, and the query wasn't too short, so offer an alternative
            loop = asyncio.get_running_loop()
            # doing a fuzzy match on the qindex keys can take about 2 seconds, so
            # run in an executor so we can keep processing other commands in the meantime
            with concurrent.futures.ThreadPoolExecutor() as pool:
                nearest = await loop.run_in_executor(pool,
                                                     process.extractOne,
                                                     query,
                                                     list(qindex))
            msg = "Sorry, nothing matching that name was found. The closest blueprint name is" \
                  f" `{nearest[0]}`."
            return await ctx.send(msg)
        if obj.tile is not None:
            tile = obj.tile
            if recolor != '':
                if recolor == 'random':
                    def random_color():
                        return random.choice(list(QUD_COLORS.keys()))
                    colors = [random_color(), random_color()]
                else:
                    colors = recolor.split()
                if len(colors) != 2 or not all(color in QUD_COLORS for color in colors):
                    return await ctx.send('Syntax error with optional `recolor` argument.'
                                          ' See `?help tile` for details.')
                # user requested a recolor of the tile, use the old tile to make a new one
                filename = obj.tile.filename
                colorstring = obj.tile.colorstring
                qudname = obj.tile.qudname
                raw_transparent = obj.tile.raw_transparent
                tile = QudTile(filename, colorstring, colors[0], colors[1], qudname,
                               raw_transparent)
            if smalltile:
                data = tile.get_bytesio()
            else:
                data = tile.get_big_bytesio()
            data.seek(0)
            msg = f"`{obj.name}` (display name: '{obj.displayname}'):"
            return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}.png'))
        else:
            msg = f"Sorry, the Qud blueprint `{obj.name}` (display name: '{obj.displayname}')" \
                  " doesn't have a tile."
            await ctx.send(msg)

    @command()
    async def smalltile(self, ctx: Context, *args):
        """Send the small (game size) tile for the named Qud blueprint.

        Optional arguments from the 'tile' command are allowed."""
        return await self.tile(ctx, *args, smalltile=True)
