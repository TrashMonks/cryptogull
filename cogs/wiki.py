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

    async def get_full_urls(self, pageids):
        """Return a list of the full URLs for a list of existing page IDs."""
        str_pageids = [str(pageid) for pageid in pageids]
        params = {'format': 'json',
                  'action': 'query',
                  'prop': 'info',
                  'inprop': 'url',
                  'pageids': '|'.join(str_pageids)}
        async with self.bot.aiohttp_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        urls = [response['query']['pages'][str(pageid)]['fullurl'] for pageid in pageids]
        return urls

    @commands.command()
    async def wiki(self, ctx, *args):
        """Search article titles for the given text, and embed a list of matching articles."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'prefixsearch',
                  'pslimit': self.limit,
                  'pssearch': ' '.join(args)}
        async with self.bot.aiohttp_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        if 'error' in response:
            try:
                info = ''.join(response['error']['info'])
                return await ctx.send(f'Sorry, that query resulted in a search error: {info}')
            except ValueError as e:
                log.exception(e)
                return await ctx.send(f'Sorry, that query resulted in a search error with no'
                                      ' error message. Exception logged.')
        results = response['query']['prefixsearch']
        if len(results) == 0:
            return await ctx.send('Sorry, that query didn\'t find any article titles.')
        urls = await self.get_full_urls([item['pageid'] for item in results])
        reply = ''
        for item, url in zip(results, urls):
            title = item['title']
            reply += f'\n[{title}]({url})'
        embed = discord.Embed(colour=discord.Colour(0xc3c9b1),
                              description=reply)
        await ctx.send(embed=embed)
