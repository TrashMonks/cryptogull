"""Commands for sending rendered game tiles as attachments."""
import logging

from discord import File
from discord.ext.commands import Cog, Bot, Context, command

from bot.helpers.corpus import corpus
from bot.helpers.tiles import get_tile_data, TileError, get_random_tile_name, get_tile_data_by_file

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.corpus = corpus

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
        log.info(f"Selected random tile blueprint: {name}")
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
        """Alias for ?randomtile recolor random, with a special reading from Cryptogull."""
        msg = self.corpus.generate_sentence()
        return await self.randomtile(ctx, "recolor", "random", reading=msg)


async def process_tile_request(ctx: Context, *args, **kwargs):
    """
    Interface between the Discord layer and the Discord-agnostic tile helper.
    """
    log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
    try:
        msg, filedata, filename = await get_tile_data(*args, **kwargs)
    except TileError as e:
        return await ctx.send(str(e))
    await ctx.send(msg, file=File(fp=filedata, filename=filename))


async def process_tile_by_file_request(ctx: Context, *args):
    """
    Interface between the Discord layer and the Discord-agnostic tile-by-file helper.
    """
    log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
    try:
        msg, filedata, filename = await get_tile_data_by_file(*args)
    except TileError as e:
        return await ctx.send(str(e))
    await ctx.send(msg, file=File(fp=filedata, filename=filename))
