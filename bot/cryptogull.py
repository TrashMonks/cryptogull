"""Custom Bot class."""
from discord.ext.commands import Bot

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


class CryptogullBot(Bot):
    """Inherit from Bot to override setup_hook."""
    async def setup_hook(self):
        await self.add_cog(BlueprintQuery(self))
        await self.add_cog(Bugs(self))
        await self.add_cog(Cryochamber(self))
        await self.add_cog(Decode(self))
        await self.add_cog(Dice(self))
        await self.add_cog(Hitdabricks(self))
        await self.add_cog(Markov(self))
        await self.add_cog(Pronouns(self))
        await self.add_cog(Reddit(self))
        await self.add_cog(Say(self))
        await self.add_cog(Tiles(self))
        await self.add_cog(Wiki(self))
