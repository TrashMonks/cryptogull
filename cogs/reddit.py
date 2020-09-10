import asyncio
import logging

from discord import Embed
from discord.ext.commands import Cog, Bot
import asyncpraw

from shared import config

log = logging.getLogger('bot.' + __name__)


class Reddit(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Reddit']
        self.reddit = asyncpraw.Reddit(client_id=self.config['client ID'],
                                       client_secret=self.config['secret'],
                                       user_agent=self.config['user agent'])
        self.posts_channel = None
        self.comments_channel = None
        self.subreddit = None
        self.loop = None

        @self.bot.event
        async def on_ready():
            self.posts_channel = bot.get_channel(int(self.config['submissions channel']))
            self.comments_channel = bot.get_channel(int(self.config['comments channel']))
            self.subreddit = await self.reddit.subreddit(self.config['subreddit'])
            self.loop = asyncio.get_running_loop()
            self.loop.create_task(self.watch_for_submissions())
            self.loop.create_task(self.watch_for_comments())

    async def watch_for_submissions(self):
        """Watch for new submissions in the subreddit and relay them in embeds."""
        async for submission in self.subreddit.stream.submissions(skip_existing=True):
            await submission.load()
            embed = Embed(title=submission.title,
                          url=submission.url,
                          description=submission.selftext)
            # need to check 'vars' because submission cannot be directly queried, see:
            # https://asyncpraw.readthedocs.io/en/latest/getting_started/quick_start.html#determine-available-attributes-of-an-object
            if 'thumbnail' in vars(submission):
                embed.set_thumbnail(url=submission.thumbnail)
            author = submission.author
            await author.load()
            embed.set_author(name=author.name,
                             url=f'https://reddit.com/u/{author.name}',
                             icon_url=author.icon_img)
            await self.posts_channel.send(embed=embed)

    async def watch_for_comments(self):
        """Watch for new comments in the subreddit and relay them in embeds."""
        async for comment in self.subreddit.stream.comments(skip_existing=True):
            permalink = f'https://reddit.com{comment.permalink}'
            description = f'**[New reply]({permalink}) on ' \
                          f'[{comment.link_title}]({comment.link_permalink})**\n'
            description += comment.body[:1500]
            embed = Embed(description=description)
            author = comment.author
            await author.load()
            embed.set_author(name=author.name,
                             url=f'https://reddit.com/u/{author.name}',
                             icon_url=author.icon_img)
            await self.comments_channel.send(embed=embed)
