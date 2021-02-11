import re
from typing import Optional, List, Tuple
from urllib.parse import urlencode
from urllib.request import pathname2url

from discord import Message, Embed, Colour
from discord.ext.commands import Context
from yarl import URL

from shared import http_session

WIKI_FAVICON = 'https://static.wikia.nocookie.net/cavesofqud_gamepedia_en/images/0/05/Wiki-icon-used-by-CoQ-Discord-bot.png'  # noqa E501
WIKI_SINGLE_PAGE_EMBED_COLOR = Colour(0xc3c9b1)
WIKI_PAGE_LIST_EMBED_COLOR = Colour(0xc3c9b1)
WIKI_PAGE_ERROR_EMBED_COLOR = Colour(0xc3c9b1)
WIKI_NAMESPACES = {
    'main': '0',
    'talk': '1',
    'file': '6',
    'template': '10',
    'category': '14',
    'module': '828',
    'modding': '10000',
    'data': '10002'
}
IGNORED_WIKI_IMAGES = [  # images to always ignore and not display in wikipage embeds
    'Hp_symbol.png',
    'Av_symbol.png',
    'Dv_symbol.png',
    'AmboxAlchTable.png',
    'AmboxBaetyl.png',
    'AmboxCleanup.svg',
    'AmboxCrow.png',
    'AmboxDaughter.png',
    'AmboxFarmer.png',
    'AmboxMerchant.png',
    'AmboxRadio.png',
    'AmboxRejuvTank.png',
    'AmboxScroll.png',
    'AmboxStatue.png',
    'AmboxStela.png',
    'AmboxVisage.png',
    'Water.png',  # Intentional, otherwise liquids show up on every faction page because they're
    'Blood.png',  # listed as water ritual liquids. Liquid wiki pages continue to work fine despite
    'Oil.png',    # these exlusions due to the presense of alternate tiles, so this is okay.
]


class WikiPageSummary:
    def __init__(self, api_url: str, page_name: str, intro_only: bool, max_len: int = 1200):
        """Creates a new WikiPageSummary object. WikiPageSummary.load() should be called
        immediatley after instantiating a new WikiPageSummary object.

        Args:
            api_url: The wiki API endpoint URL
            page_name: The wiki page name for which we are retrieving a summary (ex: 'Glowfish')
            intro_only: True to return only the content before the first section header on the page.
            max_len: The maximum number of characters to return in the page extract; capped at 1200
        """
        self.url: str = api_url
        self.intro_only: bool = intro_only
        self.max_len: int = max_len if 1200 >= max_len > 0 else 1200
        self.pagename: str = page_name
        self.error: Optional[str] = None
        self._look_description: Optional[str] = None
        self._wiki_description: Optional[str] = None
        self._wiki_image: Optional[str] = None
        self._wiki_image_url: Optional[str] = None

    async def load(self):
        """Loads data into this WikiPageSummary. This method should be called after creating a new
        WikiPageSummary instance, and before accessing any other properties or methods."""
        if self.pagename is None or self.pagename == '':
            self.error = {'code': 'pageunknown', 'info': 'No wiki page was specified.'}
            return

        # The 'parse' API pulls the wikitext/images/etc from the page. This allows us to get more
        # info from our QBE template and also to determine which image(s) are on the page.
        #
        #   API docs: https://www.mediawiki.org/wiki/API:Parsing_wikitext
        #   Qud wiki API sandbox: https://bit.ly/3cU9uKf
        #
        parse_params = {
            'action': 'parse',
            'format': 'json',
            'page': self.pagename,
            'redirects': 1,
            'prop': 'images|wikitext',
        }
        async with http_session.get(url=self.url, params=parse_params) as reply:
            response = await reply.json()
        if 'error' in response:
            self.error = response['error']  # error object includes 'code' and 'info' sub-elements
            return
        # first grab the image from the full list of page images (less reliable - see below)
        self._wiki_image = next((im for im in response['parse']['images']
                                 if im not in IGNORED_WIKI_IMAGES), None)
        wiki_text = response['parse']['wikitext']['*']
        if any(tocright in wiki_text for tocright in ['{{tocright}}', '{{Tocright}}']):
            # workaround when {{tocright}} is present - if we try to retrieve only the intro when
            # this is the case, we get nothing (because TOC counts as a heading before the intro
            self.intro_only = False

        self._look_description = self._parse_look_description_from_templates(wiki_text)
        self._look_description = await self._parse_grammar(self._look_description, wiki_text)
        template_image = self._parse_image_from_templates(wiki_text, response['parse']['images'])
        self._wiki_image = template_image if template_image is not None else self._wiki_image

        # We follow up our 'parse' API call with a 'query' call to obtain these additional details:
        #
        #   Image URL
        #     AllImages API allows us to pull the image details, including direct URL to an image
        #     API docs: https://www.mediawiki.org/wiki/API:Allimages
        #
        #   Human-readable text page summary
        #     TextExtracts API allows us to get a human-readable text translation of the wikitext on
        #     the page, without trying to parse it ourselves. This ignores templates, such as our
        #     infobox template, and also ignores images, tables, and links. It will include headers
        #     with our current configuration (ex: "\n\n== Tips ==\nSome tip text"), but can be
        #     reconfigured to return only the intro text before the first section header if needed.
        #     API docs: https://www.mediawiki.org/wiki/Extension:TextExtracts
        #
        #   Qud wiki API sandbox: https://bit.ly/3pZKs02
        #
        extract_params = {
            'action': 'query',
            'format': 'json',
            # TextExtracts API params:
            'prop': 'extracts',
            'titles': self.pagename,
            'exchars': self.max_len,
            'exlimit': 1,
            'explaintext': 1
        }
        if self.intro_only:
            extract_params['exintro'] = 1
        if self._wiki_image is not None:
            # merge allimages params into query call
            allimages_params = {
                'list': 'allimages',
                'aifrom': self._wiki_image,
                'aito': self._wiki_image,
            }
            extract_params = {**extract_params, **allimages_params}

        # for some reason, question marks get malformed in the request URL (converted to %3E) if
        # we use the following call. This seems to affect only the TextExtracts API:
        #     async with http_session.get(url=self.url, params=extract_params) as reply
        # To fix it, we have to encode the URL ourselves for this particular API request. I took the
        # workaround instructions from here: https://github.com/aio-libs/aiohttp/issues/3424
        encoded_url = self.url + '?' + urlencode(extract_params)
        async with http_session.get(url=URL(encoded_url, encoded=True)) as reply:
            response = await reply.json()
        if 'error' in response:
            self.error = response['error']  # error object includes 'code' and 'info' sub-elements
            return
        elif '-1' in response['query']['pages']:  # alternate error indicator for TextExtracts API
            self.error = {'code': 'notfound', 'info': 'No page matches the API query.'}
            return
        page_id = list(response['query']['pages'])[0]
        extract_text = response['query']['pages'][page_id]['extract']
        if extract_text is not None and extract_text != '' and extract_text != '...':
            self._wiki_description = self.cleanup_extract_formatting(extract_text)
        if 'allimages' in response['query'] and len(response['query']['allimages']) > 0:
            uri = response['query']['allimages'][0]['url']
            encoded_wiki_image_url = pathname2url(self._wiki_image)
            # Trim excess from image path (ex: <imageurl>.png/revision/latest?cb=20201231000000)
            if encoded_wiki_image_url in uri:
                self._wiki_image_url = uri.split(encoded_wiki_image_url)[0] + encoded_wiki_image_url

    @staticmethod
    def _parse_look_description_from_templates(page_wikitext: str) -> Optional[str]:
        """Parses the 'desc' parameter of various wiki templates that appear in wikitext markup.
        This includes both QBE-generated templates as well as some manually-maintained templates
        with a 'desc' parameter

        Args:
            page_wikitext: The full wikitext of the wiki page
        """
        desc_pattern = (r'^{{(?:Item|Character|Food|Corpse|[Aa]bility|[Ss]kill|[Mm]od|[Ll]ocation'
                        r'|[Mm]utation) *\n(?:(?!^}}).).*^\| *desc *= *((?:(?!^(?:\||}})).)+)')
        desc_match = re.search(desc_pattern, page_wikitext, re.MULTILINE | re.DOTALL)
        if desc_match is not None:
            look_desc: str = desc_match.group(1)
            look_desc = look_desc.replace('*', '\\*')  # escape asterisks for Discord markdown
            look_desc = look_desc.replace('\\n', '\n')  # fix raw '\n' in some mutation descriptions
            look_desc = WikiPageSummary.strip_templates(look_desc)  # remove templates
            for common_color_str in ['&amp;C', '&C', '&y', '&W', '&w']:  # remove color prefixes
                look_desc = look_desc.replace(common_color_str, '')
            look_desc_lines = [
                f'> *{li.strip()}*' if len(li.strip()) > 0 else '> '
                for li in look_desc.splitlines()
            ]
            return '\n'.join(look_desc_lines)

    @staticmethod
    def _parse_image_from_templates(page_wikitext: str, page_images: List[str]) -> Optional[str]:
        """Parses the 'overrideimages' parameter of a page's wikitext, if present. Falls back to
        parsing the 'image' parameter if 'overrideimages' is not found. Designed to parse both
        QBE-generated templates and some manually-maintained templates with these parameters

        Args:
            page_wikitext: The full wikitext of the wiki page
            page_images: API-retrieved list of page images with proper capitalization/underscoring
        """
        image_pattern = (r'^{{(?:Item|Character|Food|Corpse|[Ll]ocation|[Mm]utation) *\n'
                         r'(?:(?!^}}).).*^\| *image *= *((?:(?!^(?:\||}})).)+)'
                         r'(?:\| *overrideimages *= *.*?\{\{altimage *\| *([^\|]+\S) *\|)?')
        image_match = re.search(image_pattern, page_wikitext, re.MULTILINE | re.DOTALL)
        if image_match is not None:
            img = image_match.group(1) if image_match.group(2) is None else image_match.group(2)
            img = img.strip()
            # find the correct caps/format from the page's image list, if we can
            if len(page_images) > 0:
                val = img.lower().replace('  ', ' ').replace(' ', '_')
                for page_image in page_images:
                    if page_image.lower() == val:
                        img = page_image
                        break
            return img

    async def _parse_grammar(self, text_to_parse: str, full_wikitext: str) -> Optional[str]:
        """Parses grammar and pronouns in a 'look' description by using the expandtemplates API.
        If we eventually move the logic for handling grammar into hagadias (instead of the wiki's
        Module:Grammar), we can remove this function and the single call to it."""
        if text_to_parse is None or '=' not in text_to_parse:
            return text_to_parse
        gender_pronouns_pattern = (r'^{{(?:Character) *\n'
                                   r'(?:(?:(?!^}}).)*^\| *gender *= *([^\n]+))?'
                                   r'(?:(?:(?!^}}).)*^\| *pronouns *= *([^\n]+))?')
        gp_match = re.search(gender_pronouns_pattern, full_wikitext, re.MULTILINE | re.DOTALL)
        gender = 'nonspecific' if (gp_match is None or gp_match.group(1) is None) \
            else gp_match.group(1)
        pronouns = '' if (gp_match is None or gp_match.group(2) is None) else gp_match.group(2)
        grammar_template = ('{{grammar'
                            f'|text={text_to_parse}|gender={gender}|pronouns={pronouns}'
                            '}}')
        params = {
            'action': 'expandtemplates',
            'format': 'json',
            'text': grammar_template,
            'prop': 'wikitext'
        }
        async with http_session.get(url=self.url, params=params) as reply:
            response = await reply.json()
        if 'error' in response:
            return text_to_parse  # errors ignored; issues will be obvious in any non-parsed output
        return response['expandtemplates']['wikitext']

    @staticmethod
    def strip_templates(text: str) -> str:
        """Strip wiki {{templates}} from string, including nested templates."""
        i = 0
        ret = ''
        template_level = 0
        while i < len(text):
            if text[i] == '{' and text[i + 1] == '{':
                template_level += 1
                i += 1
            elif text[i] == '}' and text[i + 1] == '}':
                if template_level > 0:
                    template_level -= 1
                i += 1
            elif template_level == 0:
                ret += text[i]
            i += 1
        return ret.strip()

    @staticmethod
    def cleanup_extract_formatting(text: str) -> str:
        """Cleans up the format of the wiki text extract, making it suitable for a Discord embed.
        Makes the following changes:
          - If a "References" section exists, removes that section and all subsequent content.
          - Reformats page headers (ex: ==Header Two==) to use Discord markdown (ex: **Title**).
          - Standardizes newline spacing
        """
        if '=' in text:
            # strip ==References== section and anything subsequent from end of extract, if present:
            references_patt = r'\n*^ *=+ *References *(?:\.\.\.)? *=+.*'
            text = re.sub(references_patt, '', text, flags=re.MULTILINE | re.DOTALL)

            # convert all headers from wikitext to Discord markdown
            patterns = [
                r'^ *= *([^=\n]+\S) *= *$\n*',  # h1
                r'^ *== *([^=\n]+\S) *== *$\n*',  # h2
                r'^ *=== *([^=\n]+\S) *=== *$\n*',  # h3
                r'^ *====+ *([^=\n]+\S) *====+ *$\n*'  # h4 or beyond
            ]
            replacements = [
                r'__**\1**__\n',  # h1
                r'**\1**\n',  # h2
                r'__*\1*__\n',  # h3
                r'*\1*\n'  # h4 or beyond
            ]
            for patt, repl in zip(patterns, replacements):
                text = re.sub(patt, repl, text, flags=re.MULTILINE)

        # when ascending heading levels (ex: h3 -> h2), add an extra linebreak between.
        ascending_h_patts = [
            r'^(\*[^\*\n]+\*)\n(__\*[^\*\n]+\*__)$',
            r'^(__\*[^\*\n]+\*__)\n(\*\*[^\*\n]+\*\*)$',
            r'^(\*\*[^\*\n]+\*\*)\n(__\*\*[^\*\n]+\*\*__)$'
        ]
        for patt in ascending_h_patts:
            text = re.sub(patt, r'\1\n\n\2', text, flags=re.MULTILINE)

        # clean up any excessive (3+) linebreaks on the page:
        linebreaks_patt = r'\n *\n *(?:\n *)+'
        text = re.sub(linebreaks_patt, '\n\n', text, flags=re.MULTILINE)
        return text

    @property
    def look_description(self) -> Optional[str]:
        if self.error is not None:
            raise RuntimeError('Attempted to access unresolved property of WikiPageSummary after '
                               'WikiPageSummary.load() encountered an API error.')
        return self._look_description

    @property
    def wiki_description(self) -> Optional[str]:
        if self.error is not None:
            raise RuntimeError('Attempted to access unresolved property of WikiPageSummary after '
                               'WikiPageSummary.load() encountered an API error.')
        return self._wiki_description

    @property
    def wiki_image_url(self) -> Optional[str]:
        if self.error is not None:
            raise RuntimeError('Attempted to access unresolved property of WikiPageSummary after '
                               'WikiPageSummary.load() encountered an API error.')
        return self._wiki_image_url


def get_wiki_namespaces(namespaces: str) -> str:
    """Returns a pipe-delimited string of wiki namespace IDs, or an empty string if no matching
    namespace was found.

    Args:
        namespaces: Comma-delimited list of namespaces to include in the return value.
    """
    ids = []
    for namespace in namespaces.lower().split(','):
        n = namespace.strip()
        if n in WIKI_NAMESPACES:
            ids.append(WIKI_NAMESPACES[n])
    return '|'.join(ids)


async def get_wiki_page_summary(api_url: str, page_name: str,
                                intro_only: bool = True, max_len: int = 1200) -> WikiPageSummary:
    """Asynchronously creates and returns a WikiPageSummary object for the specified page, ensuring
    that the WikiPageSummary object is properly initialized.

    Args:
        api_url: The wiki's API endpoint
        page_name: The name of the wiki page, such as "Barathrumite token"
        intro_only: True if the WikiPageSummary should include -only- the introductory section of
                    the wiki page up until the first section header, ignoring everything after that
        max_len: The maximum number of characters to allow in the page extract; capped at 1200
    """
    wikipage_summary = WikiPageSummary(api_url, page_name, intro_only, max_len)
    await wikipage_summary.load()
    return wikipage_summary


async def send_single_wiki_page(ctx: Context, api_url: str, page_name: str, page_url: str,
                                intro_only: bool = True, max_len: int = 1200) -> Message:
    """Sends a single wiki page to the Discord client as a full-featured embed.

    Args:
        ctx: Discord messaging context
        api_url: The wiki's API endpoint
        page_name: The name of the wiki page, such as "Barathrumite token"
        page_url: The full URL to the wiki page
        intro_only: True if this method should embed -only- the introductory section of the
                    wiki page up until the first section header, ignoring everything after that
        max_len: The maximum number of characters to return in the page extract; capped at 1200
    """
    reply = ''
    page_info: WikiPageSummary = await get_wiki_page_summary(api_url, page_name,
                                                             intro_only, max_len)
    if page_info.look_description:
        reply += f'{page_info.look_description}\n'
    if page_info.wiki_description:
        reply += ('\n' if len(reply) > 0 else '') + page_info.wiki_description
    embed = Embed(colour=WIKI_SINGLE_PAGE_EMBED_COLOR, description=reply)
    if page_info.wiki_image_url:
        embed.set_thumbnail(url=page_info.wiki_image_url)
    embed.title = page_name
    embed.url = page_url
    embed.set_footer(text='Official Caves of Qud Wiki', icon_url=WIKI_FAVICON)
    return await ctx.send(embed=embed)


async def send_wiki_page_list(ctx: Context, titles: List[str],
                              urls: List[str], snippets: Optional[List[str]] = None) -> Message:
    """Sends a list of wiki pages to the Discord client as a simple embed.

    Args:
        ctx: Discord messaging context
        titles: The list of wiki page titles
        urls: The corresponding list of wiki page URLs
        snippets: (Optional) short description snippets to include with each link
    """
    reply = ''
    snippets = snippets if snippets is not None else [None] * len(titles)
    for title, url, snip in zip(titles, urls, snippets):
        reply += f'\n[{title}]({encode_wiki_url_parens(url)})'
        if snip is not None and snip != '' and snip != '...':
            reply += f': {snip}'
    embed = Embed(colour=WIKI_PAGE_LIST_EMBED_COLOR, description=reply)
    return await ctx.send(embed=embed)


async def send_wiki_error_message(ctx: Context, message: str) -> Message:
    """Sends an error message to the Discord client as a simple embed."""
    return await ctx.send(embed=Embed(colour=WIKI_PAGE_ERROR_EMBED_COLOR, description=message))


async def pageids_to_urls_and_snippets(api_url: str, pageids: list) -> Tuple[list, list]:
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
    async with http_session.get(url=api_url, params=params) as reply:
        response = await reply.json()
    urls = [response['query']['pages'][str(pageid)]['fullurl'] for pageid in pageids]
    summaries = [response['query']['pages'][str(pageid)]['extract'] for pageid in pageids]
    summaries = list(map(lambda s: s.replace('\n', ' '), summaries))
    return urls, summaries


def encode_wiki_url_parens(wiki_url: str) -> str:
    """Wiki pages that end in a parenthesis aren't rendered correctly in Discord mobile. This fixes
    that issue by encoding parentheses and braces in the final part of the url path."""
    paren_chars = {'(': '%28', ')': '%29', '[': '%5B', ']': '%5D'}
    if any(paren in wiki_url for paren in paren_chars.keys()) and '/' in wiki_url:
        url_parts = wiki_url.rsplit('/', 1)
        for paren, repl in paren_chars.items():
            url_parts[1] = url_parts[1].replace(paren, repl)
        wiki_url = url_parts[0] + '/' + url_parts[1]
    return wiki_url
