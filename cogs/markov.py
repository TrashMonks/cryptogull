"""Commands for random text generation."""
from helpers.corpus import corpus
import logging

from discord.ext.commands import Cog, Bot, Context, command

log = logging.getLogger('bot.' + __name__)


class Markov(Cog):
    """Markov shenanigans!"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.corpus = corpus

    @command()
    async def incorpus(self, ctx: Context, *args):
        """ Returns all corpus phrases that contain the arguments, ignoring
            capitalization and punctuation."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')

        msg = self.corpus.get_pairs(args)
        itemstruncated = 0
        if len(msg) == 0:
            return await ctx.send("That phrase doesn't seem to be in the corpus.")
        if len(msg) > 20:
            # Truncate list because some lists surpass 4k message limit.
            # TODO: add parameter to offset or paginate to let people see the rest
            itemstruncated = len(msg)-20
            msg = msg[:20]
        msgstr = "\"" + '\", \"'.join(msg) + "\""
        if itemstruncated > 0:
            msgstr += f", *...{itemstruncated} additional pairs hidden*"
        return await ctx.send(f"These phrases are in the corpus: {msgstr}")

    @command()
    async def sleeptalk(self, ctx: Context, *args):
        """Generate a sentence(s) akin to one you would see using telepathy on a sleeping creature.

        Does not require arguments, but can take one or two words to use
        as opening words. Due to how markov chains work, they must already
        exist in the corpus (word bank)."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')

        seed = ""
        if len(args) >= 1:
            if len(args) >= 3:
                return await ctx.send("You need less than 3 words!")
            seed = self.corpus.get_pair(args)
            if seed is None:
                return await ctx.send("That phrase doesn't seem to be in the corpus.")
        msg = self.corpus.generate_sentence(seed)
        return await ctx.send(msg)
