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

    async def pageids_to_urls(self, pageids):
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
        """Search article titles for the given text, and embed a list of matching articles.

        Using prefixsearch, a sample API response for 'sun':
{'batchcomplete': '',
 'query': {'prefixsearch': [{'ns': 0,
                             'pageid': 1439,
                             'title': 'Sun-dried banana'},
                            {'ns': 0, 'pageid': 4059, 'title': 'Sunder Mind'},
                            {'ns': 0,
                             'pageid': 1992,
                             'title': 'Sun and moon mask'}]}}

        Using srsearch and intitle:, a sample API response for 'sun':
{'batchcomplete': '',
 'query': {'search': [{'ns': 0,
                       'pageid': 1439,
                       'size': 616,
                       'snippet': '<span class="searchmatch">sun</span>-dried '
                                  'banana    <span '
                                  'class="searchmatch">sun</span>-dried banana '
                                  'Moisture was baked out of fruit by the salt '
                                  '<span class="searchmatch">sun</span>, but '
                                  'Spindle glitter still alights the '
                                  'disc-chip.  Perfect  In India',
                       'timestamp': '2019-09-03T19:42:32Z',
                       'title': 'Sun-dried banana',
                       'wordcount': 57},
                      {'ns': 0,
                       'pageid': 1992,
                       'size': 403,
                       'snippet': '<span class="searchmatch">sun</span> and '
                                  'moon mask    <span '
                                  'class="searchmatch">sun</span> and moon '
                                  'mask This is a spectacularly crafted <span '
                                  'class="searchmatch">sun</span> and moon '
                                  'mask. It makes you feel uneasy.  Perfect',
                       'timestamp': '2019-08-28T22:48:07Z',
                       'title': 'Sun and moon mask',
                       'wordcount': 23},
                      {'ns': 0,
                       'pageid': 1990,
                       'size': 382,
                       'snippet': 'smiling <span '
                                  'class="searchmatch">sun</span> mask    '
                                  'smiling <span '
                                  'class="searchmatch">sun</span> mask This is '
                                  'a very fancy smiling <span '
                                  'class="searchmatch">sun</span> mask. It '
                                  'smells faintly of ancient, dried grapes.  '
                                  'Perfect',
                       'timestamp': '2019-08-28T22:48:06Z',
                       'title': 'Smiling sun mask',
                       'wordcount': 22},
                      {'ns': 0,
                       'pageid': 1995,
                       'size': 485,
                       'snippet': 'Issachari <span '
                                  'class="searchmatch">sun</span> veil    '
                                  'Issachari <span '
                                  'class="searchmatch">sun</span> veil A veil '
                                  'cut from a thin, flame-retardant fabric '
                                  'woven by the Issachari nomad tribes.  '
                                  'Perfect',
                       'timestamp': '2019-08-28T22:48:10Z',
                       'title': 'Issachari sun veil',
                       'wordcount': 22}],
           'searchinfo': {'totalhits': 4}}}

"""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'search',
                  'srnamespace': 0,
                  'srwhat': 'text',
                  'srlimit': self.limit,
                  'srsearch': 'intitle:' + ' '.join(args)}
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
        results = response['query']['search']
        if len(results) == 0:
            return await ctx.send('Sorry, that query didn\'t find any article titles.')
        urls = await self.pageids_to_urls([item['pageid'] for item in results])
        reply = ''
        for match, url in zip(results, urls):
            title = match['title']
            reply += f'\n[{title}]({url})'
        embed = discord.Embed(colour=discord.Colour(0xc3c9b1),
                              description=reply)
        await ctx.send(embed=embed)

    @commands.command()
    async def wikisearch(self, ctx, *args):
        """Perform a fulltext search for the given query, and embed a list of matches."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        params = {'format': 'json',
                  'action': 'query',
                  'list': 'search',
                  'srsearch': ' '.join(args),
                  'srnamespace': 0,
                  'srwhat': 'text',
                  'srlimit': self.limit,
                  'srprop': 'snippet'}
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
        embed = discord.Embed(colour=discord.Colour(0xc3c9b1),
                              description=reply)
        await ctx.send(embed=embed)
