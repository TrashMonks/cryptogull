import datetime
import logging
from pathlib import Path

import aiohttp
from discord.ext.commands import Bot

from cogs.cryochamber import Cryochamber
from cogs.decode import Decode
from cogs.tiles import Tiles
from cogs.wiki import Wiki
from cogs.dice import Dice

LOGDIR = Path('logs')


with open('discordtoken.sec') as f:
    token = f.read()
bot = Bot(command_prefix='?')


def setup_logger() -> logging.Logger:
    """Create and return the master Logger object."""
    LOGDIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    logfile = LOGDIR / f'{timestamp}.log'
    logger = logging.getLogger('bot')  # the actual logger instance
    logger.setLevel(logging.DEBUG)  # capture all log levels
    console_log = logging.StreamHandler()
    console_log.setLevel(logging.DEBUG)  # log levels to be shown at the console
    file_log = logging.FileHandler(logfile)
    file_log.setLevel(logging.DEBUG)  # log levels to be written to file
    formatter = logging.Formatter('{asctime} - {name} - {levelname} - {message}', style='{')
    console_log.setFormatter(formatter)
    file_log.setFormatter(formatter)
    logger.addHandler(console_log)
    logger.addHandler(file_log)
    return logger


log = setup_logger()


@bot.event
async def on_connect():
    bot.aiohttp_session = aiohttp.ClientSession()


@bot.event
async def on_ready():
    log.info(f'Logged in as {bot.user}.')


bot.add_cog(Decode(bot))
bot.add_cog(Tiles(bot))
bot.add_cog(Wiki(bot))
bot.add_cog(Dice(bot))
bot.add_cog(Cryochamber(bot))
bot.run(token)
