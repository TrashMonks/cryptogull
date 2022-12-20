import datetime
import logging
from pathlib import Path

import discord
from discord.ext.commands import Bot, CommandOnCooldown

from bot.cogs.blueprints import BlueprintQuery
from bot.cogs.bugs import Bugs
from bot.cogs.cryochamber import Cryochamber
from bot.cogs.decode import Decode
from bot.cogs.dice import Dice
from bot.cogs.hitdabricks import Hitdabricks
from bot.cogs.markov import Markov
from bot.cogs.pronouns import Pronouns
from bot.cogs.reddit import Reddit
from bot.cogs.say import Say
from bot.cogs.tiles import Tiles
from bot.cogs.wiki import Wiki

from bot.shared import config

intents = discord.Intents.default()
intents.members = True

LOGDIR = Path(config['Log folder'])


def setup_logger() -> logging.Logger:
    """Create and return the master Logger object."""
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
    log = setup_logger()
    activity = discord.Game("?help in #bot-spam")
    bot = Bot(command_prefix=config['Prefix'], activity=activity, intents=intents)

    @bot.event
    async def on_ready():
        log.info(f'Logged in as {bot.user}.')

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.send(f'Please wait {error.retry_after:.0f} seconds.')
        raise error  # re-raise the error so all the errors will still show up in console

    bot.add_cog(BlueprintQuery(bot))
    bot.add_cog(Bugs(bot))
    bot.add_cog(Cryochamber(bot))
    bot.add_cog(Decode(bot))
    bot.add_cog(Dice(bot))
    bot.add_cog(Hitdabricks(bot))
    bot.add_cog(Markov(bot))
    bot.add_cog(Pronouns(bot))
    bot.add_cog(Reddit(bot))
    bot.add_cog(Say(bot))
    bot.add_cog(Tiles(bot))
    bot.add_cog(Wiki(bot))
    bot.run(config['Discord token'])


if __name__ == '__main__':
    main()
