import datetime
import logging
import re
import yaml
from pathlib import Path

import discord

import gamedata
import qud_decode

LOGDIR = Path('logs')

with open("config.yml") as f:
    config = yaml.safe_load(f)

with open('discordtoken.sec') as f:
    token = f.read()
client = discord.Client()
gamecodes = gamedata.read_gamedata()
valid_charcode = re.compile(r"(?:^|\s)[AB][A-L][A-Z]{6}(?:[01ABCDEU][0-9A-Z])*")


def setup_logger() -> logging.Logger:
    """Create and return the master Logger object."""
    LOGDIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    logfile = LOGDIR / f'{timestamp}.log'
    logger = logging.getLogger(__name__)  # the actual logger instance
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


@client.event
async def on_ready():
    log.info(f'Logged in as {client.user}.')


@client.event
async def on_message(message: discord.message.Message):
    if not isinstance(message.channel, discord.channel.DMChannel)\
            and message.channel.id not in config['channels']:
        return

    if message.author.id in config['ignore'] or message.author == client.user:
        return

    match = valid_charcode.search(message.content)
    if match:
        code = match[0].strip()  # may have whitespace
        log.info(f'({message.channel}) <{message.author}> {message.content}')
        try:
            decode = qud_decode.decode(code, gamecodes)
            response = f"```less\nCode:      {code}\n" + decode + "\n```"
            await message.channel.send(response)
            log.info(f'Replied with {response}')
        except:
            log.exception(f"Exception while decoding and sending character code {code}.")


client.run(token)
