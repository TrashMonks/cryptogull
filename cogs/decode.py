import logging
import re

from discord import File, Embed
from discord.channel import DMChannel
from discord.ext.commands import Bot, Cog
from discord.message import Message

from helpers.qud_decode import Character
from shared import config

log = logging.getLogger('bot.' + __name__)

valid_charcode = re.compile(r"(?:^|\s)[AB][A-L][A-Z]{6}(?:[0-9A-Z][0-9A-Z](?:#\d)?)*")


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
        match = valid_charcode.search(message.content)
        if not match:
            return  # no code found

        code = match[0].strip()
        log.info(f'({message.channel}) <{message.author}> {message.content}')
        try:
            char = Character.from_charcode(code)
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
