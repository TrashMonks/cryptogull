import logging
import re
import random
import asyncio

import discord
from discord.ext.commands import Cog, Bot
from discord.message import Message
from bot.shared import config
from discord import DeletedReferencedMessage


log = logging.getLogger('bot.' + __name__)

orb_command = re.compile(r"(^\w?\^\w?orb)", re.IGNORECASE)
orbs = [
    '🔴',
    '🟠',
    '🟡',
    '🟢',
    '🔵',
    '🟣',
    '🟤',
    '⚫',
    '⚪',
    '🌕',
    '🪩',
    '🫧',
    '🔮',
    '🎱',
    '<:orb:1357170327657906307>',
    '<:baetyl:957116466673618994>'
]
strange_orbs = [
    '🥎',
    '⚽',
    '🏀',
    '🧋',
    '🧶',
    '🪀',
    '💿'
]
confirm_text = ["Launching orbs!",
                "Initiating orb strategy mode.",
                "With the power of every server member!",
                "Orbs."]


class Orb(Cog):
    """Initiate Orb Strategy.

    Usage: Reply to a message with '^orb this fool'
    other usages:
    ^orbify
    ^orb this delver, ex."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Orb']

    @Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.id in self.config['ignore'] or msg.author == self.bot.user:
            return  # ignore ignored users and bots
        if msg.reference is None:
            return
        if not orb_command.match(msg.content):
            return
        # Grab only replies. Or at least, as best it can with this
        # version of discord.py.
        msg_ref = msg.reference
        if (not msg_ref.resolved or
           type(msg_ref.resolved) is DeletedReferencedMessage):

            log.info(f'({msg.channel}) <{msg.author}> tried to orb someone but was unsuccessful.')
            msg.channel.send(
                "I couldn't see the msg you replied to, sorry.")
        if msg_ref.message_id:
            # Grab message the reply was for.
            replied_msg = await msg.channel.fetch_message(msg_ref.message_id)
            if replied_msg.author.id == msg.author.id:
                # You can't orb yourself
                return  # change to pass for lonely testers
            log.info(f'({msg.channel}) <{msg.author}> orbed {replied_msg.author}')
            # Shuffle order of orb, and add in a few Strange Orb
            random_orbs = random.sample(orbs, k=16)
            for strange_orb in random.sample(strange_orbs,
                                             k=random.randrange(1, 3)):
                random_orbs.insert(random.randrange(0, len(random_orbs)),
                                   strange_orb)
            # Orb this fool!
            msg.channel.send(confirm_text[random.randrange(0, 4)])
            for orb in random_orbs:
                try:
                    await replied_msg.add_reaction(orb)
                except discord.errors.HTTPException as e:
                    print(f"Error when trying to grab emoji {orb}:{e.text}")
                await asyncio.sleep(0.5)
