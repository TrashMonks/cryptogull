"""Commands for operating on the wiki API at https://cavesofqud.gamepedia.com/api.php

API request builder:
https://cavesofqud.gamepedia.com/Special:ApiSandbox#action=query&format=json&list=search&srsearch=intitle%3Amod&srwhat=title
API help:
https://cavesofqud.gamepedia.com/api.php?action=help&modules=query%2Bsearch
"""
import asyncio
import concurrent.futures
import functools
import logging
import time

from discord import Colour, Embed
from discord.ext.commands import Bot, Cog, Context, command
from fuzzywuzzy import process

from shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Wiki(Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.title_limit = config['wiki title search limit']
        self.fulltext_limit = config['wiki fulltext search limit']
        self.url = 'https://' + config['wiki'] + '/api.php'
        self.all_titles = {}  # mapping of titles to pageids, for conversion to URLs by API
        self.all_titles_stamp = 0.0  # after self.all_titles is filled, this will be its timestamp

    async def pageids_to_urls(self, pageids: list) -> list:
        """Helper function to return a list of the full URLs for a list of existing page IDs."""
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

    async def read_titles(self, namespace):
        fresh_titles = {}
        # there's a limit on how many titles we can fetch at a time (currently 5000 for bots)
        # and we may have more wiki articles than that someday, so fetch in batches
        got_all = False
        apfrom = ''  # the article title to 'continue' querying from, if necessary
        while not got_all:
            params = {'format': 'json',
                      'action': 'query',
                      'list': 'allpages',
                      'apfrom': apfrom,
                      'apnamespace': namespace,
                      'aplimit': 5000}  # TODO: add to config
            async with http_session.get(url=self.url, params=params) as reply:
                response = await reply.json()
            new_items = response['query']['allpages']
            for item in new_items:
                title = item['title']
                # filter out some Cargo tables that shouldn't be in main namespace
                if not title.startswith('DynamicObjectsTable:'):
                    fresh_titles[title] = item['pageid']
            if 'continue' in response:
                apfrom = response['continue']['apcontinue']
            else:
                got_all = True
        return fresh_titles

    async def refresh_titles_cache(self):
        """Helper function to get all article titles for custom search and fuzzy matching."""
        # TODO: put cache time limit in config
        if self.all_titles != {} and time.monotonic() - self.all_titles_stamp < 900:
            # we have cached titles, and they're less than 15 minutes old
            return
        # else, we need to fetch new titles and update timestamp
        new_titles = {}
        namespaces = [0, 14]  # Main, Category  TODO: add to config
        for namespace in namespaces:
            new_titles.update(await self.read_titles(namespace))
        self.all_titles = new_titles
        self.all_titles_stamp = time.monotonic()

    @command()
    async def wiki(self, ctx: Context, *args):
        """Search titles of articles for the given text."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        async with ctx.typing():
            await self.refresh_titles_cache()  # fetch, or refresh, self.all_pages
            query = ' '.join(args)
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                results = await loop.run_in_executor(
                    pool,
                    functools.partial(process.extractBests,
                                      query,
                                      self.all_titles.keys(),
                                      score_cutoff=75,
                                      limit=10))  # TODO: read from config
            if len(results) == 0:
                return await ctx.send(f'Sorry, no matches were found for that query.')
            pageids = [self.all_titles[item[0]] for item in results]  # map titles to IDs
            urls = await self.pageids_to_urls(pageids)
            reply = ''
            for title, url in zip((result[0] for result in results), urls):
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
