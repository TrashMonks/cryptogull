"""Commands for operating on the wiki API at https://cavesofqud.gamepedia.com/api.php

API request builder:
https://cavesofqud.gamepedia.com/Special:ApiSandbox#action=query&format=json&list=search&srsearch=intitle%3Amod&srwhat=title
API help:
https://cavesofqud.gamepedia.com/api.php?action=help&modules=query%2Bsearch
"""

import logging
from typing import Optional, Tuple

from discord import Colour, Embed
from discord.ext.commands import Bot, Cog, Context, command

from shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Wiki(Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Wiki']
        self.title_limit = self.config['title search limit']
        self.fulltext_limit = self.config['fulltext search limit']
        self.url = 'https://' + self.config['site'] + '/api.php'

    async def pageids_to_urls_and_snippets(self, pageids: list) -> Tuple[list, list]:
        """Return a list of the full URLs for a list of existing page IDs.

        While the query list=search API does return snippets, in our case the snippets are always
        just QBE template HTML with no useful text. So here, we pull a better snippet using the
        TextExtracts API (prop=extracts) in addition to pulling the page URLs with prop=info
        """
        str_pageids = [str(pageid) for pageid in pageids]
        params = {'format': 'json',
                  'action': 'query',
                  'prop': 'info|extracts',
                  'inprop': 'url',
                  'exlimit': len(str_pageids),
                  'exintro': 1,
                  'explaintext': 1,
                  'exchars': 120,
                  'pageids': '|'.join(str_pageids)}
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        urls = [response['query']['pages'][str(pageid)]['fullurl'] for pageid in pageids]
        summaries = [response['query']['pages'][str(pageid)]['extract'] for pageid in pageids]
        summaries = list(map(lambda s: s.replace('\n', ' '), summaries))
        return urls, summaries

    async def wiki_helper(self, limit: Optional[int], ctx: Context, *args):
        """Search the titles of articles on the official Caves of Qud wiki.
        Since title search was removed with the Unified Community Platform upgrade, this is
        the same as a generic search.
        """
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query):  # If no search term specified, return basic help
            return await ctx.send_help(ctx.command)
        params = {'action': 'opensearch',
                  'search': query,
                  'namespace': '0|14|10000',
                  'limit': self.title_limit if limit is None else limit,
                  'profile': 'fuzzy',
                  'redirects': 'resolve',
                  'format': 'json'}
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        if 'error' in response:
            if response['error']['code'] == 'internal_api_error_TypeError':
                await ctx.send('Sorry, that query didn\'t find any article titles.'
                               ' Performing fulltext search:')
                return await(self.wikisearch(ctx, *args))
            else:
                try:
                    info = ''.join(response['error']['info'])
                    return await ctx.send(f'Sorry, that query caused a search error: "{info}"')
                except ValueError as e:
                    log.exception(e)
                    return await ctx.send('Sorry, that query caused a search error with no'
                                          ' error message. Exception logged.')
        titles = response[1]
        urls = response[3]
        reply = ''
        for title, url in zip(titles, urls):
            reply += f'\n[{title}]({url})'
        embed = Embed(colour=Colour(0xc3c9b1),
                      description=reply)
        await ctx.send(embed=embed)

    @command()
    async def wiki(self, ctx: Context, *args):
        return await self.wiki_helper(None, ctx, *args)

    @command()
    async def wikipage(self, ctx: Context, *args):
        return await self.wiki_helper(1, ctx, *args)

    @command()
    async def wikisearch(self, ctx: Context, *args):
        """Search the text of articles on the official Caves of Qud wiki."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        srsearch = ' '.join(args)
        if srsearch == '' or str.isspace(srsearch):  # no search term specified, return basic help
            return await ctx.send_help(ctx.command)
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'search',
                  'srsearch': srsearch,
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
                return await ctx.send('Sorry, that query resulted in a search error with no'
                                      ' error message. Exception logged.')
        matches = len(response['query']['search'])
        if matches == 0:
            return await ctx.send('Sorry, no matches were found for that query.')
        results = response['query']['search']
        urls, snips = await self.pageids_to_urls_and_snippets([item['pageid'] for item in results])
        reply = ''
        for num, (match, url, snip) in enumerate(zip(results, urls, snips), start=1):
            title = match['title']
            reply += f'[{title}]({url})'
            if snip is not None and snip != '' and snip != '...':
                reply += f': {snip}'
            reply += '\n'
        embed = Embed(colour=Colour(0xc3c9b1),
                      description=reply)
        await ctx.send(embed=embed)
