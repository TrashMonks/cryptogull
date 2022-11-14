"""Cog for posting Reddit events to Discord."""
import asyncio
import logging

import asyncpraw
from discord import Embed
from discord.ext.commands import Cog, Bot

from bot.shared import config

log = logging.getLogger('bot.' + __name__)


class Reddit(Cog):
    """Functionality for streaming Reddit posts and comments from one or more
    subreddits to one or more channels."""
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Reddit']
        self.reddit = asyncpraw.Reddit(client_id=self.config['client ID'],
                                       client_secret=self.config['secret'],
                                       user_agent=self.config['user agent'])
        self.loop = None
        self.tasks_created = False

        @self.bot.event
        async def on_ready():
            """Register all requested subreddit+channel combos as tasks."""
            # guard against creating tasks more than once - on_ready fires when reconnecting.
            if self.tasks_created:
                return
            self.loop = asyncio.get_running_loop()
            for subreddit_name, channels in self.config['subreddits'].items():
                subreddit = await self.reddit.subreddit(subreddit_name)
                if 'submissions channel' in channels:
                    posts_channel = bot.get_channel(int(channels['submissions channel']))
                    self.loop.create_task(watch_submissions(subreddit, posts_channel))
                if 'comments channel' in channels:
                    comments_channel = bot.get_channel(int(channels['comments channel']))
                    self.loop.create_task(watch_comments(subreddit, comments_channel))
            self.tasks_created = True


async def watch_submissions(subreddit, channel):
    """Watch for new submissions in the subreddit and relay them to a processor."""
    while True:
        try:
            async for submission in subreddit.stream.submissions(skip_existing=True):
                await process_submission(channel, submission)
        except Exception as e:
            log.exception(e)
            log.warning('Caught exception in relay_submissions, continuing in 10 seconds.')
            await asyncio.sleep(10)


async def process_submission(channel, submission):
    """Handle a submission to a subreddit and post it as an embed."""
    await submission.load()
    embed = Embed(title=submission.title[:200],
                  url=submission.url,
                  description=submission.selftext[:1000])
    # need to check 'vars' because submission cannot be directly queried, see:
    # https://asyncpraw.readthedocs.io/en/latest/getting_started/quick_start.html#determine-available-attributes-of-an-object
    if 'thumbnail' in vars(submission) and submission.thumbnail != 'self':
        # self-posts (text) have the text string 'self' instead of a thumbnail
        embed.set_thumbnail(url=submission.thumbnail)
    author = submission.author
    await author.load()
    embed.set_author(name=author.name,
                     url=f'https://reddit.com/u/{author.name}',
                     icon_url=author.icon_img)
    await channel.send(embed=embed)


async def watch_comments(subreddit, channel):
    """Watch for new comments in the subreddit and relay them to a processor."""
    while True:
        try:
            async for comment in subreddit.stream.comments(skip_existing=True):
                await process_comment(channel, comment)
        except Exception as e:
            log.exception(e)
            log.warning('Caught exception in relay_comments, continuing in 10 seconds.')
            await asyncio.sleep(10)


async def process_comment(channel, comment):
    """Handle a new comment in the subreddit and post it as an embed."""
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
    await channel.send(embed=embed)
