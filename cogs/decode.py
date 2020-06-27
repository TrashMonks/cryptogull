import logging
import re

from discord.channel import DMChannel
from discord.ext.commands import Bot, Cog
from discord.message import Message

from helpers.qud_decode import Character
from shared import config

log = logging.getLogger('bot.' + __name__)

valid_charcode = re.compile(r"(?:^|\s)[AB][A-L][A-Z]{6}(?:[01ABCDEU][0-9A-Z])*")


class Decode(Cog):
    """Feature cog: listener that responds to character build codes."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Decode']

    @Cog.listener()
    async def on_message(self, message: Message):
        """Process all incoming messages."""
        if not isinstance(message.channel, DMChannel) \
                and message.channel.id not in self.config['channels']:
            return

        if message.author.id in self.config['ignore'] or message.author == self.bot.user:
            return

        match = valid_charcode.search(message.content)
        if match:
            code = match[0].strip()  # may have whitespace
            log.info(f'({message.channel}) <{message.author}> {message.content}')
            try:
                char = Character.from_charcode(code)
                sheet = char.make_sheet()
                response = f"```less\nCode:      {code}\n" + sheet + "\n```"
                if char.origin == 'post200':
                    response += 'Game version: beta.'
                elif char.origin == 'pre200':
                    response += 'Game version: stable.'
                await message.channel.send(response)
            except:  # noqa E722
                log.exception(f"Exception while decoding and sending character code {code}.")
