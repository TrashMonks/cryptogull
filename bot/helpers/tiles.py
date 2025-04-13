"""Helper functionality for the Tiles cog."""

import asyncio
import concurrent.futures
import random
from datetime import datetime
from functools import partial

from hagadias.constants import QUD_COLORS
from hagadias.qudtile import QudTile
from hagadias.tileanimator import TileAnimator, GifHelper, StandInTiles

from bot.helpers.find_blueprints import find_name_or_displayname, fuzzy_find_nearest
from bot.helpers.tile_variations import parse_variation_parameters, get_tile_variation_details
from bot.shared import qindex


class TileError(Exception):
    pass


async def get_tile_data(*args,
                        smalltile: bool = False,
                        animated: bool = False,
                        hologram: bool = False,
                        reading: str = ""):
    """
    Worker function for producing tiles for the Tiles cog.
    This function does not know about Discord so that it can be unit tested easily.

    :param args: The remaining arguments provided in the Discord message.
    :param smalltile: If True, produces a pixel-for-pixel size tile (16x24).
                      If False, produces a large 160x240 tile.
    :param animated: Whether to animate the tile (assuming it can be animated).
    :param hologram: Whether to produce a hologram tile.
    :param reading: used for horoscopes or something idk
    :return: A tuple containing the textual message to send to the channel, the file data as binary
             data, and the name of the file (for attachment purposes)
    """
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
            raise TileError("Sorry, that specific blueprint name wasn't found,"
                            " and it's too short to search.")
        # there was no exact match, and the query wasn't too short, so offer an alternative
        obj = await fuzzy_find_nearest(query, qindex)
        raise TileError("Sorry, nothing matching that name was found."
                        f" The closest blueprint name is `{obj.name}`.")
    if obj.tile is None:
        raise TileError(f"Sorry, the Qud blueprint `{obj.name}`"
                        f" (display name: '{obj.displayname}')"
                        " doesn't have a tile.")
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
            msg += f'Sorry, `{obj.name}` does not have an animated tile.\n'
    elif recolor != '':
        if recolor == 'random':
            colors = [random_qud_color(), random_qud_color()]
        else:
            colors = recolor.split()
        if len(colors) != 2 or not all(color in QUD_COLORS for color in colors):
            raise TileError('Couldn\'t understand optional `recolor` argument.'
                            ' See `?help tile` for details.')
        # user requested a recolor of the tile, use the old tile to make a new one
        filename = tile.filename
        colorstring = tile.colorstring
        qudname = tile.qudname
        raw_transparent = tile.raw_transparent
        tile_provider = StandInTiles.get_tile_provider_for(obj)
        tile = QudTile(filename, colorstring, colors[0], colors[1], qudname,
                       raw_transparent, image_provider=tile_provider)
    if gif_bytesio is not None:
        filedata = gif_bytesio
    elif smalltile:
        filedata = tile.get_bytesio()
    else:
        filedata = tile.get_big_bytesio()
    filedata.seek(0)
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
    filename = f'{obj.displayname}{ext}'
    return msg, filedata, filename


async def get_tile_data_by_file(*args):
    query = ' '.join(args)
    if len(args) <= 0:
        raise TileError('Not enough arguments. See `?help tilebyfile` for details.')
    if len(args) == 1:
        raise TileError('Not enough arguments. Specify *random* or *<color1> <color2>*. '
                        'See `?help tilebyfile` for details.')
    if query.endswith(' random'):
        query = query[:-7]
        colors = [random_qud_color(), random_qud_color()]
    else:
        params = query.split()
        if len(params) < 3:
            raise TileError('Need more arguments. See `?help tilebyfile` for details.')
        colors = params[-2:]
        query = ' '.join(params[:-2])
        if not all(color in QUD_COLORS for color in colors):
            raise TileError('Couldn\'t find all those colors. See `?help tilebyfile` for details.')
    filename = query.strip()
    try:
        tile = QudTile(filename, colors[0], colors[0], colors[1], filename)
    except FileNotFoundError:
        raise TileError(f'Could not find {filename} in the tiles set.')
    except PermissionError:
        raise TileError(f'The file {filename} is not allowed.')
    if tile.hasproblems:
        raise TileError('Was not able to generate that tile.')
    filedata = tile.get_big_bytesio()
    filedata.seek(0)
    msg = f'*Tile created from "{filename}":*'
    fname = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f'{fname}.png'
    return msg, filedata, filename


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
    names = [
        name for name, obj in qindex.items()
        if obj.tile is not None and obj.source_file.name != 'HiddenObjects.xml'
    ]
    name = random.choice(names)
    obj = qindex[name]
    if obj.number_of_tiles() > 1:
        if 'variation' not in args:
            args = ('variation',) + args
    return name, args


def random_qud_color():
    return random.choice(list(QUD_COLORS.keys()))
