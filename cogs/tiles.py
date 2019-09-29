"""Commands for sending rendered game tiles as attachments."""

import logging

from discord import File
from discord.ext.commands import Cog, Context, command
from hagadias.qudtile import QUD_COLORS, QudTile

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord.

    Optional postfix: recolor color1 color2
    Append this to the command to recolor the tile with color1 as the tile color and color2
    as the detailcolor.  color1 and color2 should be Qud color codes like 'w' and 'c'."""

    @command()
    async def tile(self, ctx: Context, *args):
        """Send the tile for the named Qud object."""
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
        # search for partial matches if necessary
        if obj is None:
            if len(query) < 3:
                msg = "Sorry, that specific object wasn't found, and it's too short to search."
                return await ctx.send(msg)
            for key, val in qindex.items():
                if query.lower() in key.lower():
                    obj = val
                    break
        if obj is None:
            msg = "Sorry, nothing matching that object was found."
            return await ctx.send(msg)
        if obj.tile is not None:
            tile = obj.tile
            if recolor != '':
                colors = recolor.split()
                if len(colors) != 2 or not all(color in QUD_COLORS for color in colors):
                    return await ctx.send('Syntax error with optional `recolor` argument.'
                                          ' See `?help tile for details.')
                # user requested a recolor of the tile, use the old tile to make a new one
                filename = obj.tile.filename
                colorstring = obj.tile.colorstring
                qudname = obj.tile.qudname
                raw_transparent = obj.tile.raw_transparent
                tile = QudTile(filename, colorstring, colors[0], colors[1], qudname,
                               raw_transparent)
            data = tile.get_bytesio()
            data.seek(0)
            msg = f"`{obj.name}` (display name: '{obj.displayname}'):"
            return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}.png'))
        else:
            msg = f"Sorry, the Qud object `{obj.name}` (display name: '{obj.displayname}')" \
                  " doesn't have a tile."
            await ctx.send(msg)
