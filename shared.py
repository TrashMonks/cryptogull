"""Shared resources for the bot and cogs.

Exports:
    config: a dictionary loaded with the global config from config.yml
    http_session: the global aiohttp ClientSession
    gameroot: the hagadias reader with the path to the local installation of Caves of Qud
    qud_object_root: the root object of the QudObject tree
    qindex: dictionary mapping object IDs to QudObjects
"""

import aiohttp
import asyncio
import yaml

from hagadias.gameroot import GameRoot


async def create_http_session():
    """Create the aiohttp session.

    aiohttp strongly advises the use of only one session per application, and also
    disallows the creation of this session from outside a coroutine."""
    session = aiohttp.ClientSession()
    return session


with open("config.yml", encoding='utf8') as f:
    config = yaml.safe_load(f)

http_session = asyncio.get_event_loop().run_until_complete(create_http_session())

gameroot = GameRoot(config['Qud install folder'])
qud_root_object, qindex = gameroot.get_object_tree()
