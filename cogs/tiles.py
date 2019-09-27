"""Commands for sending rendered game tiles as attachments."""

import logging

from discord import File
from discord.ext.commands import Cog, Context, command

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class Tiles(Cog):
    """Send game tiles to Discord."""

    @command()
    async def tile(self, ctx: Context, *args):
        """Send the tile for the named Qud object."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
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
            data = obj.tile.get_bytesio()
            data.seek(0)
            msg = f"`{obj.name}` (display name: '{obj.displayname}'):"
            return await ctx.send(msg, file=File(fp=data, filename=f'{obj.displayname}.png'))
        else:
            msg = f"Sorry, the Qud object {obj.name} ({obj.displayname}) doesn't have a tile."
            await ctx.send(msg)
