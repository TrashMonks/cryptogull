"""Commands for sending rendered game tiles as attachments."""
import asyncio
import concurrent.futures
import logging
import random

from discord import File
from discord.ext.commands import Cog, Context, command
from fuzzywuzzy import process
from hagadias.qudtile import QUD_COLORS, QudTile
from hagadias.tileanimator import TileAnimator, GifHelper

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    @command()
    async def tile(self, ctx: Context, *args, smalltile=False, hologram=False):
        """Send the tile for the named Qud blueprint.

        Supported command formats:
          ?tile <object>
          ?tile <object> recolor <color1> <color2>
          ?tile <object> recolor random

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        """
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
            await ctx.send(msg)
            # send the tile for the nearest match
            obj = qindex[nearest[0]]
        if obj.tile is not None:
            tile = obj.tile
            gif = None
            if hologram:
                animator = TileAnimator(obj, tile)
                animator.apply_hologram_material_random()
                gif = animator.gif
            elif recolor != '':
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
            if gif is not None:
                data = GifHelper.get_bytesio(gif)
            elif smalltile:
                data = tile.get_bytesio()
            else:
                data = tile.get_big_bytesio()
            data.seek(0)
            msg = f"`{obj.name}` (display name: '{obj.displayname}'):"
            ext = '.png' if gif is None else '.gif'
            return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}{ext}'))
        else:
            msg = f"Sorry, the Qud blueprint `{obj.name}` (display name: '{obj.displayname}')" \
                  " doesn't have a tile."
            await ctx.send(msg)

    @command()
    async def smalltile(self, ctx: Context, *args):
        """Send the small (game size) tile for the named Qud blueprint.

        Optional arguments from the 'tile' command are allowed."""
        return await self.tile(ctx, *args, smalltile=True)

    @command()
    async def randomtile(self, ctx: Context, *args):
        """Send a random game tile to the channel.

        Optional arguments from the 'tile' command are allowed."""
        names = list(qindex)
        name = 'Object'
        obj = qindex['Object']
        while obj.tile is None:
            name = random.choice(names)
            obj = qindex[name]
        return await(self.tile(ctx, name, *args))

    @command()
    async def hologram(self, ctx: Context, *args):
        """Sends a hologram of the specified Qud object."""
        return await self.tile(ctx, *args, hologram=True)
