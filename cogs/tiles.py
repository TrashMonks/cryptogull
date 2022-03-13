"""Commands for sending rendered game tiles as attachments."""
import asyncio
import concurrent.futures
import logging
import random
from datetime import datetime
from functools import partial

from discord import File
from discord.ext.commands import Cog, Bot, Context, command
from hagadias.qudtile import QUD_COLORS, QudTile
from hagadias.tileanimator import TileAnimator, GifHelper

from helpers.find_blueprints import find_name_or_displayname, fuzzy_find_nearest
from helpers.tile_variations import parse_variation_parameters, get_tile_variation_details
from helpers.corpus import Corpus
from shared import qindex


log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.corpus = Corpus()

    @command()
    async def tile(self, ctx: Context, *args):
        """Send the tile for the named Qud blueprint.

        Supported command formats:
          ?tile <object>
          ?tile <object> recolor <color1> <color2>
          ?tile <object> recolor random
          ?tile <object> variation [# or keyword or 'random'] [recolor...]
          ?tile <object> unidentified

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors
        variation => sends a variation of the tile, if one exists
        unidentified => sends the 'unidentified' variation of the tile

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        Colors reference: https://wiki.cavesofqud.com/Visual_Style#Palette
        """
        return await process_tile_request(ctx, *args)

    @command()
    async def smalltile(self, ctx: Context, *args):
        """Send the small (game size) tile for the named Qud blueprint.

        Supported command formats:
          ?smalltile <object>
          ?smalltile <object> recolor <color1> <color2>
          ?smalltile <object> recolor random
          ?smalltile <object> variation [# or keyword or 'random'] [recolor...]
          ?smalltile <object> unidentified

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors
        variation => sends a variation of the tile, if one exists
        unidentified => sends the 'unidentified' variation of the tile

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        Colors reference: https://wiki.cavesofqud.com/Visual_Style#Palette
        """
        return await process_tile_request(ctx, *args, smalltile=True)

    @command()
    async def randomtile(self, ctx: Context, *args, reading=""):
        """Send a random game tile to the channel.

        Supported command formats:
          ?randomtile
          ?randomtile recolor <color1> <color2>
          ?randomtile recolor random

        recolor => repaints the tile using <color1> as TileColor and <color2> as DetailColor
        recolor random => repaints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        Colors reference: https://wiki.cavesofqud.com/Visual_Style#Palette
        """
        name, args = get_random_tile_name(*args)
        return await(process_tile_request(ctx, name, *args, reading=reading))

    @command()
    async def hologram(self, ctx: Context, *args):
        """Sends a hologram of the named Qud object.

        Supported command formats:
          ?hologram <object>
          ?hologram <object> [variation...]
        """
        return await process_tile_request(ctx, *args, hologram=True)

    @command()
    async def animate(self, ctx: Context, *args):
        """Sends an animated tile for the named Qud object, if it has one.

        Supported command formats:
          ?animate <object>
          ?animate <object> [variation...]
        """
        return await process_tile_request(ctx, *args, animated=True)

    @command()
    async def tilebyfile(self, ctx: Context, *args):
        """Sends a tile based on the specified file path and colors.

        Supported command formats:
          ?tilebyfile <filepath> <color1> <color2>
          ?tilebyfile <filepath> random

        File names are relative to the Textures directory.
        Example: ?tilebyfile creatures/sw_glowfish.bmp o O

        color1/color2 => paints the tile using <color1> as TileColor and <color2> as DetailColor
        random => paints the tile using random colors

        Colors include: b, B, c, C, g, G, k, K, m, M, o, O, r, R, w, W, y, Y, transparent
        Colors reference: https://wiki.cavesofqud.com/Visual_Style#Palette
        """
        return await process_tile_by_file_request(ctx, *args)

    @command()
    async def horoscope(self, ctx: Context, *args):
        msg = self.corpus.generate_sentence()
        return await self.randomtile(ctx, "recolor", "random", reading=msg)


async def process_tile_request(ctx: Context, *args, smalltile=False,
                               animated=False, hologram=False, reading=""):
    log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
    query = ' '.join(args)
    # parse recolor parameters, if present
    if 'recolor' in query:
        query, recolor = [q.strip() for q in query.split('recolor', maxsplit=1)]
    else:
        recolor = ''
    # parse variation parameters, if present
    query, variation = parse_variation_parameters(query)
    # search for exact matches first
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
        use_variation = False
        has_variations = obj.number_of_tiles() > 1
        if variation != '':
            variation_result = get_tile_variation_details(obj, variation)
            if variation_result['err']:
                msg += variation_result['err'] + '\n'
            else:
                tile = variation_result['tile']
                use_variation = True
        if hologram:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                call = partial(get_bytesio_for_object, obj, tile, hologram=True)
                async with ctx.typing():
                    gif_bytesio = await loop.run_in_executor(pool, call)
            msg += 'Hologram of '
        elif animated:
            if TileAnimator(obj).has_gif:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    call = partial(get_bytesio_for_object, obj, tile)
                    async with ctx.typing():
                        gif_bytesio = await loop.run_in_executor(pool, call)
                msg += 'Animated '
            else:
                msg += f'Sorry, `{obj.name}` does not have an animated tile.\n'
        elif recolor != '':
            if recolor == 'random':
                colors = [random_qud_color(), random_qud_color()]
            else:
                colors = recolor.split()
            if len(colors) != 2 or not all(color in QUD_COLORS for color in colors):
                return await ctx.send('Couldn\'t understand optional `recolor` argument.'
                                      ' See `?help tile` for details.')
            # user requested a recolor of the tile, use the old tile to make a new one
            filename = tile.filename
            colorstring = tile.colorstring
            qudname = tile.qudname
            raw_transparent = tile.raw_transparent
            tile = QudTile(filename, colorstring, colors[0], colors[1], qudname,
                           raw_transparent)
        if gif_bytesio is not None:
            data = gif_bytesio
        elif smalltile:
            data = tile.get_bytesio()
        else:
            data = tile.get_big_bytesio()
        data.seek(0)
        if reading.isspace() or len(reading) == 0:
            msg += f"`{obj.name}` (display name: '{obj.displayname}'):"
            if use_variation:
                msg += f'\n*variation {variation_result["idx"]} - {variation_result["name"]}*'
            elif not smalltile and not gif_bytesio:
                notices = []
                if TileAnimator(obj).has_gif:
                    notices.append(f"can be animated (`?animate {obj.name}`)")
                if has_variations and variation == '':
                    notices.append(f'has {obj.number_of_tiles()} variations '
                                   f'(`?tile {obj.name} variation #`)')
                if len(notices) > 0:
                    msg += f'\nThis tile {" and ".join(notices)}'
        else:
            msg += f"**{obj.displayname}** ({colors[0]}, {colors[1]})\n{reading}"
        ext = '.png' if gif_bytesio is None else '.gif'
        return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}{ext}'))
    else:
        msg = f"Sorry, the Qud blueprint `{obj.name}` (display name: '{obj.displayname}')" \
              " doesn't have a tile."
        await ctx.send(msg)


async def process_tile_by_file_request(ctx: Context, *args):
    log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
    query = ' '.join(args)
    if len(args) <= 0:
        return await ctx.send('Not enough arguments. See `?help tilebyfile` for details.')
    if len(args) == 1:
        return await ctx.send('Not enough arguments. Specify *random* or *<color1> <color2>*. '
                              'See `?help tilebyfile` for details.')
    if query.endswith(' random'):
        query = query[:-7]
        colors = [random_qud_color(), random_qud_color()]
    else:
        params = query.split()
        if len(params) < 3:
            return await ctx.send('Need more arguments. See `?help tilebyfile` for details.')
        colors = params[-2:]
        query = ' '.join(params[:-2])
        if not all(color in QUD_COLORS for color in colors):
            return await ctx.send('Couldn\'t find all those colors. '
                                  'See `?help tilebyfile` for details.')
    filename = query.strip()
    try:
        tile = QudTile(filename, colors[0], colors[0], colors[1], filename)
    except FileNotFoundError:
        return await ctx.send(f'Could not find {filename} in the tiles set.')
    except PermissionError:
        return await ctx.send(f'The file {filename} is not allowed.')
    if tile.hasproblems:
        return await ctx.send('Was not able to generate that tile.')
    data = tile.get_big_bytesio()
    data.seek(0)
    msg = f'*Tile created from "{filename}":*'
    fname = datetime.now().strftime("%Y%m%d-%H%M%S")
    return await ctx.send(msg, file=File(fp=data, filename=f'{fname}.png'))


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


def get_random_tile_name(*args):
    names = list(qindex)
    name = 'Object'
    obj = qindex['Object']
    while obj.tile is None:
        name = random.choice(names)
        obj = qindex[name]
    if obj.number_of_tiles() > 1:
        if 'variation' not in args:
            args = ('variation',) + args
    return name, args


def random_qud_color():
    return random.choice(list(QUD_COLORS.keys()))
