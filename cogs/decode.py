import logging
import re

from discord.channel import DMChannel
from discord.ext.commands import Bot, Cog, Context, command
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
        """Search specific incoming messages for character build codes."""
        if not isinstance(message.channel, DMChannel) \
                and message.channel.id not in self.config['channels']:
            return  # only do interpretations in DMs or configured channels
        if message.author.id in self.config['ignore'] or message.author == self.bot.user:
            return  # ignore ignored users and bots
        if message.content[1:8].lower() == 'upgrade':
            return  # don't try to interpret the code in an upgrade command
        match = valid_charcode.search(message.content)
        if not match:
            return  # no code found

        code = match[0].strip()
        log.info(f'({message.channel}) <{message.author}> {message.content}')
        try:
            char = Character.from_charcode(code)
            sheet = char.make_sheet()
            response = f"```less\nCode:      {code}\n" + sheet + "\n```"
            if char.origin == 'post200':
                response += 'Game version: >= 2.0.200.0'
            elif char.origin == 'pre200':
                response += 'Game version: < 2.0.200.0.\n'
                response += 'This code is from an old version of the game. '
                response += 'To get that character now, you need to use '
                response += char.upgrade() + ' instead.'
            await message.channel.send(response)
        except:  # noqa E722
            log.exception(f"Exception while decoding and sending character code {code}.")

    @command()
    async def upgrade(self, ctx: Context, code=None):
        """Upgrade a character build code from pre-2.0.200.0 to post-2.0.200.0.

        Takes the old (pre-2020 'beta' branch) build code and gives the new one."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        if code is None:
            return await ctx.send_help(ctx.command)
        match = valid_charcode.search(code)
        if not match:
            return await ctx.send(f"Sorry, but `{code}` doesn't seem to contain a"
                                  f" valid character build code.")
        code = match[0].strip()
        char = Character.from_charcode(code)
        return await ctx.send(char.upgrade())
