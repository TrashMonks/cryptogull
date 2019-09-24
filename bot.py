import datetime
import logging
from pathlib import Path

import aiohttp
import yaml
from discord.ext.commands import Bot

from cogs.decode import Decode
from cogs.wiki import Wiki

LOGDIR = Path('logs')

with open("config.yml") as f:
    config = yaml.safe_load(f)

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


bot.add_cog(Decode(bot, config))
bot.add_cog(Wiki(bot, config))
bot.run(token)
