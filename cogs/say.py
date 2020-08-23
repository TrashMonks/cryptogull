"""Commands for sending rendered strings as in game text as attachments."""
import io
import logging
import re
from discord.ext.commands import CommandError

from discord import File
from discord.ext.commands import Cog, Context, command

from helpers.font import drawttf, DrawException

log = logging.getLogger('bot.' + __name__)


class Say(Cog):
    """Reads the sent message in the specific channel and posts it."""

    @command()
    async def say(self, ctx: Context):
        """Make cryptogull say something!

        Format: ?say [-{border}[:{title}]] {text}

        Border options:
            -d, -dialogueclassic: Classic dialogue border. Specify a title
              to make it appear on the upper left. If it's more than one word,
              group it together with single quotation marks.

              Example: ?say -d:Mehmet Live and drink, friend. May you find shade in Joppa.
              Example: ?say -d:'Drowsing Urchin' Sleeeeeeeep.

            -p, -popupclassic: Classic popup border. Defaults to this if not specified.

              Example: ?say -p There are hostiles nearby!
        """
        # Regex tester: https://regex101.com/r/O0RVHC/2
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        msg = ctx.message.content[5:]
        exp = re.compile('(?P<type>-\w+)?(:)?(?(2)(\'(?P<option>.+?)\'|(?P<option2>\w+)))\s?(?P<text>.+)', flags=re.MULTILINE | re.DOTALL) # noqa E501
        match = exp.fullmatch(msg)
        if match is None:
            raise CommandError('wrong syntax: ' + msg)
        if match.group('text') is None:
            raise CommandError('wrong syntax: ' + msg)
        optionalarg = match.group('option')
        if optionalarg is None:
            optionalarg = match.group('option2')
            if optionalarg is None:
                optionalarg = (ctx.message.author.nick if ctx.message.author.nick
                               else ctx.message.author.name)
        try:
            image = drawttf(match.group('text'), match.group('type'), optionalarg)
        except DrawException as e:
            return await ctx.send(e.message + ' See `?help say` for syntax.')
        else:
            png_b = io.BytesIO()
            image.save(png_b, format='png')
            png_b.seek(0)
            return await ctx.send(file=File(fp=png_b,
                                  filename=f'{match.group("text")}-{ctx.message.author.id}.png'))
