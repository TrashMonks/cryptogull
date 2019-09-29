"""Commands for operating on the wiki API at https://cavesofqud.gamepedia.com/api.php

API request builder:
https://cavesofqud.gamepedia.com/Special:ApiSandbox#action=query&format=json&list=search&srsearch=intitle%3Amod&srwhat=title
API help:
https://cavesofqud.gamepedia.com/api.php?action=help&modules=query%2Bsearch
"""

import logging

from discord import Colour, Embed
from discord.ext.commands import Bot, Cog, Context, command

from shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Wiki(Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.title_limit = config['wiki title search limit']
        self.fulltext_limit = config['wiki fulltext search limit']
        self.url = 'https://' + config['wiki'] + '/api.php'

    async def pageids_to_urls(self, pageids: list) -> list:
        """Return a list of the full URLs for a list of existing page IDs."""
        str_pageids = [str(pageid) for pageid in pageids]
        params = {'format': 'json',
                  'action': 'query',
                  'prop': 'info',
                  'inprop': 'url',
                  'pageids': '|'.join(str_pageids)}
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        urls = [response['query']['pages'][str(pageid)]['fullurl'] for pageid in pageids]
        return urls

    @command()
    async def wiki(self, ctx: Context, *args):
        """Search titles of articles for the given text."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'search',
                  'srnamespace': '0|14',
                  'srwhat': 'text',
                  'srlimit': self.title_limit,
                  'srsearch': 'intitle:' + ' '.join(args)}
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        if 'error' in response:
            try:
                info = ''.join(response['error']['info'])
                return await ctx.send(f'Sorry, that query resulted in a search error: {info}')
            except ValueError as e:
                log.exception(e)
                return await ctx.send(f'Sorry, that query resulted in a search error with no'
                                      ' error message. Exception logged.')
        results = response['query']['search']
        if len(results) == 0:
            return await ctx.send('Sorry, that query didn\'t find any article titles.')
        urls = await self.pageids_to_urls([item['pageid'] for item in results])
        reply = ''
        for match, url in zip(results, urls):
            title = match['title']
            reply += f'\n[{title}]({url})'
        embed = Embed(colour=Colour(0xc3c9b1),
                      description=reply)
        await ctx.send(embed=embed)

    @command()
    async def wikisearch(self, ctx: Context, *args):
        """Search all articles for the given text."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'search',
                  'srsearch': ' '.join(args),
                  'srnamespace': 0,
                  'srwhat': 'text',
                  'srlimit': self.fulltext_limit,
                  'srprop': 'snippet'}
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        if 'error' in response:
            try:
                info = ''.join(response['error']['info'])
                return await ctx.send(f'Sorry, that query resulted in a search error: {info}')
            except ValueError as e:
                log.exception(e)
                return await ctx.send(f'Sorry, that query resulted in a search error with no'
                                      ' error message. Exception logged.')
        matches = response['query']['searchinfo']['totalhits']
        if matches == 0:
            return await ctx.send(f'Sorry, no matches were found for that query.')
        results = response['query']['search']
        urls = await self.pageids_to_urls([item['pageid'] for item in results])
        reply = ''
        for num, (match, url) in enumerate(zip(results, urls), start=1):
            title = match['title']
            reply += f'[{title}]({url}): '
            snippet = match['snippet'].replace('<span class="searchmatch">', '**')
            snippet = snippet.replace('</span>', '**')
            reply += snippet + '\n'
        embed = Embed(colour=Colour(0xc3c9b1),
                      description=reply)
        await ctx.send(embed=embed)
