"""Commands for operating on the wiki API at https://wiki.cavesofqud.com/api.php

API request builder:
https://wiki.cavesofqud.com/Special:ApiSandbox#action=query&format=json&list=search&srsearch=intitle%3Amod&srwhat=title
API help:
https://wiki.cavesofqud.com/api.php?action=help&modules=query%2Bsearch
"""

import logging
from typing import Optional

from discord import Message
from discord.ext.commands import Bot, Cog, Context, command

from bot.helpers.wiki_page import send_single_wiki_page, send_wiki_page_list,\
    send_wiki_error_message, get_wiki_namespaces, api_opensearch, api_query_list_search,\
    merge_wikipage_results
from bot.shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Wiki(Cog):
    """Search the official Caves of Qud wiki."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Wiki']
        self.basic_limit = self.config['basic search limit']
        self.fulltext_limit = self.config['fulltext search limit']
        self.url = self.make_wiki_url('api.php')

    @command()
    async def wiki(self, ctx: Context, *args):
        """Gets up to 10 matching wiki pages.

        Supported command formats:
          ?wiki <search query>
        """
        async with ctx.typing():
            await self.wiki_helper(None, ctx, *args)

    @command()
    async def wikipage(self, ctx: Context, *args):
        """Gets a full summary and image for the closest wiki page match.

        Supported command formats:
          ?wikipage <title or search query>
        """
        async with ctx.typing():
            await self.wiki_helper(1, ctx, *args)

    @command(aliases=['randomwiki'])
    async def wikirandom(self, ctx: Context, *args):
        """Gets a random wiki page.

        Supported command formats:
          ?wikirandom
          ?wikirandom <namespace>

        Supported namespaces include: main, modding, category, data, talk, file, template, module
        """
        async with ctx.typing():
            await self.random_wikipage(ctx, *args)

    @command()
    async def wikisearch(self, ctx: Context, *args):
        """Gets up to 5 matching wiki pages, with summaries if available.

        Supported command formats:
          ?wikisearch <search query>
        """
        async with ctx.typing():
            await self.wikisearch_helper(ctx, *args)

    def make_wiki_url(self, sub_path: str) -> str:
        """Forms a Qud Wiki URL with the provided subpath. For example, when one passes 'Waterskin'
        to this method, the following url is returned: 'https://wiki.cavesofqud.com/Waterskin'.

        Args:
            sub_path: The wiki page name or sub-path, not including an initial forward slash.
        """
        return f'https://{self.config["site"]}/{sub_path.replace(" ", "_")}'

    async def wiki_helper(self, limit: Optional[int], ctx: Context, *args):
        """Searches the official Caves of Qud wiki, and sends an embed to the channel that includes
        either a simple list of the top matching page results (if there are multiple results) or
        a single, full-featured embed for the single matching page result.

        Uses a combination of the 'opensearch' API and the 'query&list=search' API to try and get
        the best possible results that are likely to match the intent of the user.

        Args:
            limit: Maximum number of pages to return
            ctx: Discord messaging context
            *args: Additional query parameters
        """
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query):  # If no search term specified, return basic help
            return await ctx.send_help(ctx.command)

        query_namespaces = 'Main,Category,Modding'
        result_limit = self.basic_limit if limit is None else limit

        # opensearch (preserved due to better partial title matching - ex: yonder => yondercane)
        o_limit = str(max(1, int(result_limit) // 4))  # one-fourth of result limit, rounded down
        o_err, o_titles, o_urls = await api_opensearch(self.url, query, o_limit,
                                                       query_namespaces)
        # query&list=search
        err, titles, urls, _, _ = await api_query_list_search(self.url, query, result_limit,
                                                              query_namespaces,
                                                              retrieve_snippets=False)
        if err is not None:
            try:
                info = ''.join(err['info'])
                return await ctx.send(f'Sorry, that query caused a search error: "{info}"')
            except ValueError as e:
                log.exception(e)
                return await ctx.send('Sorry, that query caused a search error with no'
                                      ' error message. Exception logged.')

        elif o_err is None:
            titles, urls = merge_wikipage_results((o_titles, o_urls), (titles, urls), result_limit)

        if len(titles) == 1:
            return await send_single_wiki_page(ctx, self.url, titles[0], urls[0],
                                               intro_only=True, max_len=620, max_paragraphs=2)
        elif len(titles) > 1:
            return await send_wiki_page_list(ctx, titles, urls)
        return await send_wiki_error_message(ctx, f'*No results found for "{query}"*')

    async def wikisearch_helper(self, ctx: Context, *args):
        """Searches the official Caves of Qud wiki, and sends an embed to the channel that includes
        a list of matching wiki pages, along with a short page summary for each result.

        Args:
            ctx: Discord messaging context
            *args: Additional query parameters
        """
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query):  # no search term specified, return basic help
            return await ctx.send_help(ctx.command)

        query_namespaces = 'Main,Modding'
        result_limit = self.fulltext_limit
        err, titles, urls, snips, alt_query = await api_query_list_search(self.url, query,
                                                                          result_limit,
                                                                          query_namespaces)
        if err is not None:
            try:
                info = ''.join(err['info'])
                return await ctx.send(f'Sorry, that query resulted in a search error: {info}')
            except ValueError as e:
                log.exception(e)
                return await ctx.send('Sorry, that query resulted in a search error with no'
                                      ' error message. Exception logged.')
        if len(titles) == 0:
            return await ctx.send('Sorry, no matches were found for that query.')
        intro = None if alt_query is None else f'*Showing results for "{alt_query}":*'
        return await send_wiki_page_list(ctx, titles=titles, urls=urls, snippets=snips, intro=intro)

    async def random_wikipage(self, ctx: Context, *args) -> Message:
        """Sends a random wiki page to the channel.

        Args:
            ctx: Discord messaging context
            *args: Additional query parameters
        """
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if len(query) > 0 and not str.isspace(query):
            namespaces = get_wiki_namespaces(query)
            if namespaces == '':
                return await ctx.send(f'I don\'t recognize "{query}" as a wiki namespace. Try'
                                      ' another namespace or use the `?wikirandom` command by'
                                      ' itself with no arguments.')
        else:
            namespaces = get_wiki_namespaces('Main,Category,Modding')
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'random',
            'rnnamespace': namespaces,
            'rnfilterredir': 'nonredirects',
            'rnlimit': 1
        }
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
        elif len(response['query']['random']) < 1:
            return await ctx.send('Sorry, that random page query unexpectedly failed to return'
                                  ' any result.')
        page_name = response['query']['random'][0]['title']
        log.info(f'Selected page "{page_name}" for ?wikirandom command')
        return await send_single_wiki_page(ctx, self.url, page_name, self.make_wiki_url(page_name),
                                           intro_only=True, max_len=620, max_paragraphs=2)
