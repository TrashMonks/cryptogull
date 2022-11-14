"""Main entry point into the bot."""
import datetime
import logging
from pathlib import Path

import discord
from discord.ext.commands import CommandOnCooldown

from bot.cryptogull import CryptogullBot
from bot.shared import config

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

LOGDIR = Path(config['Log folder'])


def setup_logger() -> logging.Logger:
    """Create and return our top level Logger object."""
    LOGDIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    logfile = LOGDIR / f'{timestamp}.log'
    logger = logging.getLogger('bot')  # the actual logger instance
    logger.setLevel(logging.DEBUG)  # capture all log levels
    console_log = logging.StreamHandler()
    console_log.setLevel(logging.DEBUG)  # log levels to be shown at the console
    file_log = logging.FileHandler(logfile, 'w', 'utf8')
    file_log.setLevel(logging.DEBUG)  # log levels to be written to file
    formatter = logging.Formatter('{asctime} - {name} - {levelname} - {message}', style='{')
    console_log.setFormatter(formatter)
    file_log.setFormatter(formatter)
    logger.addHandler(console_log)
    logger.addHandler(file_log)
    return logger


def main():
    """Set up and pass control to the bot."""
    log = setup_logger()
    activity = discord.Game("?help in #bot-spam")
    bot = CryptogullBot(command_prefix=config['Prefix'], activity=activity, intents=intents)

    @bot.event
    async def on_ready():
        log.info(f'Logged in as {bot.user}.')

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.send(f'Please wait {error.retry_after:.0f} seconds.')
        raise error  # re-raise the error so all the errors will still show up in console

    bot.run(config['Discord token'])


if __name__ == '__main__':
    main()
