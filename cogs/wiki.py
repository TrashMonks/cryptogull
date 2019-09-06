import logging

import discord
from discord.ext import commands

log = logging.getLogger('bot.' + __name__)


class Wiki(commands.Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot, config):
        self.bot = bot
        self.limit = config['wiki search limit']
        self.url = 'https://' + config['wiki'] + '/api.php'

    @commands.command()
    async def wiki(self, ctx, *args):
        """Search article titles for the given text, and embed a list of matching articles."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'action': 'opensearch',
                  'format': 'json',
                  'search': ' '.join(args)}
        async with self.bot.aiohttp_session.get(url=self.url, params=params) as response:
            results = await response.json()
        if 'error' in results:
            try:
                info = ''.join(results['error']['info'])
                return await ctx.send(f'Sorry, that query resulted in a search error: {info}')
            except ValueError:
                return await ctx.send(f'Sorry, that query resulted in a search error.')
        if len(results[1]) == 0:
            return await ctx.send('Sorry, that query didn\'t find any article titles.')
        reply = ''
        for _, title, link in zip(range(self.limit), results[1], results[3]):
            reply += f'\n[{title}]({link})'
        embed = discord.Embed(colour=discord.Colour(0xc3c9b1),
                              description=reply)
        await ctx.send(embed=embed)
