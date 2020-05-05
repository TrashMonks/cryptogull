import logging
import time

import aiohttp
import discord
from discord.ext.commands import Cog, Bot, Context
from oauthlib.oauth2 import BackendApplicationClient

from shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Bugs(Cog):
    """Feature cog: cross-post issues to issue tracker upon a certain Discord reaction."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Bugs']
        self.processed_messages = set()
        self.oauthclient = BackendApplicationClient(self.config['oauth2 key'])

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Process all incoming reacts and filter out the uninteresting ones."""
        if payload.channel_id not in self.config['channels'] or \
                payload.emoji.name != self.config['trigger'] or \
                payload.message_id in self.processed_messages:
            return
        self.processed_messages.add(payload.message_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        ctx: Context = await self.bot.get_context(message)
        reacter = ctx.guild.get_member(payload.user_id)
        log.info(f'Issue requested by {reacter} ({payload.user_id})'
                 f' by reacting to the following message by {message.author} ({message.author.id}:')
        log.info(f'({message.channel}) <{message.author}> {message.content}')
        if not any(role.name in self.config['allowed roles'] for role in reacter.roles):
            log.info('Not allowed due to lacking roles.')
            log.info(f'Allowed roles: {", ".join(self.config["allowed roles"])}; user roles:'
                     f' {", ".join([role.name for role in reacter.roles])}')
            need_roles_md = [f'`{role}`' for role in reacter.roles]
            await ctx.send(f'<@{payload.user_id}>, 🐛 requires one of the following roles:'
                           f' {", ".join(need_roles_md)}')
            return
        await self.check_bitbucket_token()
        try:
            response = await self.create_bitbucket_issue(ctx, reacter)
        except Exception as e:
            log.exception(e)
            await ctx.message.add_reaction(self.config['fail reaction'])
        else:
            log.info(f'Successfully created issue #{response["id"]}.')
            await ctx.message.add_reaction(self.config['success reaction'])

    async def check_bitbucket_token(self):
        """Create or refresh our Bitbucket OAuth2 token."""
        # is our token nonexistent, expired, or expiring in the next 5 seconds?
        # TODO: Use refresh token instead of creating it each time.
        if self.oauthclient.expires_in is None or \
                self.oauthclient.expires_in < time.time() + 5:
            auth = aiohttp.BasicAuth(self.config['oauth2 key'],
                                     self.config['oauth2 secret'])
            data = {'grant_type': 'client_credentials'}
            async with http_session.post(url="https://bitbucket.org/site/oauth2/access_token",
                                         data=data,
                                         auth=auth) as response:
                text = await response.text()
                self.oauthclient.parse_request_body_response(text)

    async def create_bitbucket_issue(self, ctx: Context, requester: discord.User):
        """Create a Bitbucket issue regarding the given Discord Context.

        Return the Bitbucket API response."""
        title = ctx.message.clean_content[:self.config['title max length']]
        if ctx.message.clean_content > title:
            title = title[:len(title) - 3] + "..."
        content = f"""Issue requested by: {requester.display_name}

Message ([jump](https://discordapp.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id})):

```
<{ctx.author.display_name}> {ctx.message.clean_content}
```"""
        params = {
            'state': 'new',
            'kind': 'bug',
            'priority': 'trivial',
            'title': f'[Discord: #{ctx.channel}] {title}',
            'content': {
                'raw': content
            }
        }
        headers = {'Authorization': f'Bearer {self.oauthclient.token["access_token"]}'}
        async with http_session.post(url=self.config['endpoint'],
                                     headers=headers,
                                     json=params) as request:
            response = await request.json()
        return response
