import logging
import re

from discord.ext import commands
import discord

import gamedata
import qud_decode

log = logging.getLogger('bot.' + __name__)

valid_charcode = re.compile(r"(?:^|\s)[AB][A-L][A-Z]{6}(?:[01ABCDEU][0-9A-Z])*")


class Decode(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.gamecodes = gamedata.read_gamedata()

    @commands.Cog.listener()
    async def on_message(self, message: discord.message.Message):
        if not isinstance(message.channel, discord.channel.DMChannel) \
                and message.channel.id not in self.config['channels']:
            return

        if message.author.id in self.config['ignore'] or message.author == self.bot.user:
            return

        match = valid_charcode.search(message.content)
        if match:
            code = match[0].strip()  # may have whitespace
            log.info(f'({message.channel}) <{message.author}> {message.content}')
            try:
                decode = qud_decode.decode(code, self.gamecodes)
                response = f"```less\nCode:      {code}\n" + decode + "\n```"
                await message.channel.send(response)
                log.info(f'Replied with {response}')
            except:  # noqa E722
                log.exception(f"Exception while decoding and sending character code {code}.")
        await self.bot.process_commands(message)
