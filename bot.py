import datetime
import logging
from pathlib import Path

from discord import Game
from discord.ext.commands import Bot

from cogs.blueprints import BlueprintQuery
from cogs.bugs import Bugs
from cogs.cryochamber import Cryochamber
from cogs.decode import Decode
from cogs.dice import Dice
from cogs.hitdabricks import Hitdabricks
from cogs.pronouns import Pronouns
from cogs.reddit import Reddit
from cogs.say import Say
from cogs.tiles import Tiles
from cogs.wiki import Wiki
from shared import config

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
    activity = Game("?help in #bot-spam")
    bot = Bot(command_prefix=config['Prefix'], activity=activity)

    @bot.event
    async def on_ready():
        log.info(f'Logged in as {bot.user}.')

    bot.add_cog(BlueprintQuery(bot))
    bot.add_cog(Bugs(bot))
    bot.add_cog(Cryochamber(bot))
    bot.add_cog(Decode(bot))
    bot.add_cog(Dice(bot))
    bot.add_cog(Hitdabricks(bot))
    bot.add_cog(Pronouns(bot))
    bot.add_cog(Reddit(bot))
    bot.add_cog(Say(bot))
    bot.add_cog(Tiles(bot))
    bot.add_cog(Wiki(bot))
    bot.run(config['Discord token'])


if __name__ == '__main__':
    main()
