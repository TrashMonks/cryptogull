"""Command to send the most helpful advice for Qud."""
import logging

from discord import Embed, Colour
from discord.ext.commands import Cog, Context, command


log = logging.getLogger('bot.' + __name__)


class Hitdabricks(Cog):

    @command()
    async def hitdabricks(self, ctx: Context, *args):
        """Send golden advice."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> hit da bricks!')
        embed = Embed(colour=Colour(0xf403f),
                      url="https://twitter.com/dasharez0ne/status/979810839749210112",
                      description="(source: [dasharez0ne](https://twitter.com/dasharez0ne/"
                      + "status/979810839749210112))")

        embed.set_image(url="https://pbs.twimg.com/media/DZj8pB8VMAAxPNR?format=jpg&name=small")
        return await ctx.send(embed=embed)
