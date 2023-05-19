import logging

from discord import Embed, Colour
from discord.ext.commands import Cog, Context, command


log = logging.getLogger('bot.' + __name__)


class Theinherentlyindescribablenatureoftheuniverse(Cog):
    @command()
    async def theinherentlyindescribablenatureoftheuniverse(self, ctx: Context):
        """Command to send relevant advice about the inherently indescribable nature of the universe.""" # noqa E501
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> asked for advice about the inherently indescribable nature of the universe.') # noqa E501
        embed = Embed(colour=Colour(0xf403f),
                      url="https://xjmlm.tumblr.com/post/653164468596064256",
                      description="(source: [X](https://xjmlm.tumblr.com/post/653164468596064256))")
        embed.set_image(url="https://media.tumblr.com/74ba793b581efa0df3c37c33d821b50d/5f992972e942e96a-4e/s1280x1920/8d75a96c261e0dfa9999ce3a7e8607c19c77cc62.jpg") # noqa E501
        return await ctx.send(embed=embed)
