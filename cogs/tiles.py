"""Commands for sending rendered game tiles as attachments."""
import asyncio
import concurrent.futures
import logging
import random
from functools import partial

from discord import File
from discord.ext.commands import Cog, Context, command
from hagadias.qudtile import QUD_COLORS, QudTile
from hagadias.tileanimator import TileAnimator, GifHelper

from helpers.find_blueprints import find_name_or_displayname, fuzzy_find_nearest
from shared import qindex

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    @command()
    async def tile(self, ctx: Context, *args):
        """Send the tile for the named Qud blueprint.

        Supported command formats:
          ?tile <object>
          ?tile <object> recolor <color1> <color2>
          ?tile <object> recolor random

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        """
        return await process_tile_request(ctx, *args)

    @command()
    async def smalltile(self, ctx: Context, *args):
        """Send the small (game size) tile for the named Qud blueprint.

        Supported command formats:
          ?smalltile <object>
          ?smalltile <object> recolor <color1> <color2>
          ?smalltile <object> recolor random

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        """
        return await process_tile_request(ctx, *args, smalltile=True)

    @command()
    async def randomtile(self, ctx: Context, *args):
        """Send a random game tile to the channel.

        Supported command formats:
          ?randomtile <object>
          ?randomtile <object> recolor <color1> <color2>
          ?randomtile <object> recolor random

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        """
        names = list(qindex)
        name = 'Object'
        obj = qindex['Object']
        while obj.tile is None:
            name = random.choice(names)
            obj = qindex[name]
        return await(process_tile_request(ctx, name, *args))

    @command()
    async def hologram(self, ctx: Context, *args):
        """Sends a hologram of the named Qud object.

        Supported command formats:
          ?hologram <object>
        """
        return await process_tile_request(ctx, *args, hologram=True)

    @command()
    async def animate(self, ctx: Context, *args):
        """Sends an animated tile for the named Qud object, if it has one.

        Supported command formats:
          ?animate <object>
        """
        return await process_tile_request(ctx, *args, animated=True)


async def process_tile_request(ctx: Context, *args, smalltile=False,
                               animated=False, hologram=False):
    log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
    query = ' '.join(args)
    if 'recolor' in query:
        query, recolor = [q.strip() for q in query.split('recolor', maxsplit=1)]
    else:
        recolor = ''
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
        msg = "Sorry, nothing matching that name was found. The closest blueprint name is" \
              f" `{obj.name}`."
        await ctx.send(msg)
    if obj.tile is not None:
        tile = obj.tile
        gif_bytesio = None
        msg = ''
        if hologram:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                call = partial(get_bytesio_for_object, obj, tile, hologram=True)
                gif_bytesio = await loop.run_in_executor(pool, call)
            msg += 'Hologram of '
        elif animated:
            if TileAnimator(obj).has_gif:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    call = partial(get_bytesio_for_object, obj, tile)
                    gif_bytesio = await loop.run_in_executor(pool, call)
                msg += 'Animated '
            else:
                msg += f"Sorry, `{obj.name}` does not have an animated tile.\n"
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
        if gif_bytesio is not None:
            data = gif_bytesio
        elif smalltile:
            data = tile.get_bytesio()
        else:
            data = tile.get_big_bytesio()
        data.seek(0)
        msg += f"`{obj.name}` (display name: '{obj.displayname}'):"
        if not smalltile and not gif_bytesio and TileAnimator(obj).has_gif:
            msg += f"\nThis tile can be animated (`?animate {obj.name}`)"
        ext = '.png' if gif_bytesio is None else '.gif'
        return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}{ext}'))
    else:
        msg = f"Sorry, the Qud blueprint `{obj.name}` (display name: '{obj.displayname}')" \
              " doesn't have a tile."
        await ctx.send(msg)


def get_bytesio_for_object(qud_object, qud_tile: QudTile, hologram=False):
    """Provided a QudObject and a QudTile, creates a GIF and retrieves the associated BytesIO
    directly.

    Args:
        qud_object: The QudObject for which to create a GIF
        qud_tile: The tile variant to use for GIF creation
        hologram: If True, create a holographic version of this tile instead of using its
                  default animation
    """
    animator = TileAnimator(qud_object, qud_tile)
    if hologram:
        animator.apply_hologram_material_random()
    gif = animator.gif
    if gif is not None:
        return GifHelper.get_bytesio(gif)
    return None
