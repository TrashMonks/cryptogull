import base64
import gzip
import json
import logging
import re

from discord import File, Embed
from discord.channel import DMChannel
from discord.ext.commands import Bot, Cog
from discord.message import Message

from helpers.qud_decode import Character, Pre202Character
from shared import config

log = logging.getLogger('bot.' + __name__)

# pre-2.0.202 character codes: like "BARFIGHTBABE"
pre202_charcode = re.compile(r"(?:^|\s)[AB][A-L][A-Z]{6}(?:[0-9A-Z][0-9A-Z](?:#\d)?)*")
# 2.0.202 and later character codes are gzipped, base64-encoded strings, so hard to distinguish
# to save decoding efforts, limit to at least 80 characters long (4*20) - all build strings should
# longer than this)

# regex breakdown:
# (?:[A-Za-z0-9+/]{4})  Groups of 4 ASCII characters (4 base64 chars decode to 3 binary octets)
# {20}                  times 20, for a baseline of 80 characters
# (?:[A-Za-z0-9+/]{4})* The same again, but an arbitrary number of times (to go beyond 80 chars)
# (?:[A-Za-z0-9+/]{2}== An ending group: 2 base64 chars and 2 padding signs
# |                     or,
# [A-Za-z0-9+/]{3}=     the other ending group - 3 base64 chars and 3 padding signs
# These last 3 lines are combined with ()? meaning the end may not be padded at all, and the
# base64 may end with a group of 4 characters instead
_ = r"(?:[A-Za-z0-9+/]{4}){20}(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"
base64_charcode = re.compile(_)


class Decode(Cog):
    """Feature cog: listener that responds to character build codes."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Decode']

    @Cog.listener()
    async def on_message(self, message: Message):
        """Search specific incoming messages for character build codes."""
        if not isinstance(message.channel, DMChannel) \
                and message.channel.id not in self.config['channels']:
            return  # only do interpretations in DMs or configured channels
        if message.author.id in self.config['ignore'] or message.author == self.bot.user:
            return  # ignore ignored users and bots
        # Do we have a pre-202 character build code (e.g. "BARFIGHTBABE"?)
        match = pre202_charcode.search(message.content)
        if match:
            code = match[0].strip()
            log.info(f'({message.channel}) <{message.author}> {message.content}')
            try:
                char = Pre202Character.from_charcode(code)
                sheet = char.make_sheet()
                response = f'```less\n{sheet}\n```\n**Build code:** {code}'
                if len(response) > 2048:
                    await message.channel.send('The character sheet for that build code'
                                               ' is too large to fit into a Discord message.')
                else:
                    thumbnail = char.tile.get_big_bytesio()
                    thumbnail.seek(0)
                    img_filename = ''.join(ch for ch in char.class_name if ch.isalnum()) + '.png'
                    embedfile = File(fp=thumbnail, filename=f'{img_filename}')
                    embed = Embed(description=response, color=0x2AA18B)
                    embed.set_thumbnail(url=f'attachment://{img_filename}')
                    await message.channel.send(embed=embed, file=embedfile)
            except:  # noqa E722
                log.exception(f"Exception while decoding and sending character code {code}.")
        else:
            # No pre-2.0.202 match, but is there a base64-encoded build code (post-2.0.202?)
            match = base64_charcode.search(message.content)
            if match:
                # the real test - it may be a long jumble of characters, but
                # does it base64-decode, gunzip, and json parse cleanly?
                try:
                    decode = base64.b64decode(match[0])
                    unzip = gzip.decompress(decode).decode(encoding='utf-8')
                    code = json.loads(unzip)
                except Exception:  # noqa
                    pass  # it probably wasn't a build code!
                else:
                    char = Character(code)
                    sheet = char.make_sheet()
                    response = f'```{sheet}```'
                    if len(response) > 2048:
                        await message.channel.send('The character sheet for that build code'
                                                   ' is too large to fit into a Discord message.')
                    await message.channel.send(response)
