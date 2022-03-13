"""Commands for random text generation."""
from helpers.corpus import Corpus
import logging
import re

from discord.ext.commands import CommandError
from discord.ext import commands

from discord.ext.commands import Cog, Bot, Context, command

log = logging.getLogger('bot.' + __name__)


class Markov(Cog):
    """Markov shenanigans!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.corpus = Corpus()

    @command()
    async def sleeptalk(self, ctx: Context, *args):
        """Generate a single sentence akin to one you would see using telepathy on a sleeping creature.

        Does not require arguments, but can take a two word phrase to use as opening words. Due to how markov chains work, they must already exist in the corpus."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')

        seed = ""
        if len(args) == 1:
            possiblepairs = []
            for pair in self.corpus.chain:
                regex = fr"\b{args[0]}\b"
                if re.search(regex, pair, flags=re.IGNORECASE) is not None:
                    possiblepairs.append(pair)
            if len(possiblepairs) == 0:
                return await ctx.send(f"You need two words, and {args[0]} isn't in the corpus.")
            return await ctx.send("You need two words. Try these: \""+"\", \"".join(possiblepairs) + "\"")
        if len(args) == 2:
            query = ' '. join(args)
            if query in self.corpus.chain:
                seed = query
            else:
                return await ctx.send(f"\"{query}\" is not in the corpus. Try another word combination!")
        if len(args) >= 3:
            return await ctx.send("You only need two words!")
        msg = self.corpus.generate_sentence(seed)
        return await ctx.send(msg)
