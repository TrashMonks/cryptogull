"""Commands for sending rendered strings as in game text as attachments."""
import io
import asyncio
import concurrent.futures
import logging

from discord import File
from discord.ext.commands import Cog, Context, command

from font import drawttf

log = logging.getLogger('bot.' + __name__)


class Say(Cog):
    """Reads the sent message in the specific channel and posts it."""

    @command()
    async def say(self, ctx: Context, *args):
        """Make cryptogull say something!"""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)

        image = drawttf(query)
        png_b = io.BytesIO()
        image.save(png_b, format='png')
        png_b.seek(0) 
        return await ctx.send(file=File(fp=png_b, filename=f'{query}.png'))
