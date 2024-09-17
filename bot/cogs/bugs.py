import io
import logging
import time

import aiohttp
import discord
from discord.ext.commands import Cog, Bot, Context
from oauthlib.oauth2 import BackendApplicationClient

from bot.shared import config, http_session

log = logging.getLogger('bot.' + __name__)


class Bugs(Cog):
    """Feature cog: cross-post issues to issue tracker upon a certain Discord reaction."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config['Bugs']
        self.oauthclient = BackendApplicationClient(self.config['oauth2 key'])

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Watch for reactions that might trigger an issue report."""
        # process all incoming reacts and filter out the uninteresting ones:
        if payload.channel_id not in self.config['channels'] or \
                payload.emoji.name != self.config['trigger']:
            return
        # bootstrap to a context from the raw reaction
        channel = self.bot.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        ctx: Context = await self.bot.get_context(message)
        reacter = ctx.guild.get_member(payload.user_id)
        log.info(f'Issue requested by {reacter} ({payload.user_id})'
                 f' by reacting to the following message by {message.author}'
                 f' ({message.author.id}):')
        log.info(f'({message.channel}) <{message.author}> {message.content}')
        # have we already reacted to this message with a checkmark?
        reactions = message.reactions
        for reaction in reactions:
            if reaction.emoji == self.config['success reaction'] and reaction.me:
                log.info('Found an existing checkmark on this message, so not reporting.')
                return
        # role check: can the person who added the reaction open an issue from Discord?
        if not any(role.id in self.config['allowed roles'] for role in reacter.roles):
            log.info('Not allowed due to lacking roles.')
            return
        try:
            response = await self.create_bitbucket_issue(ctx, reacter)
            assert response["type"] != "error", "Received error response: " + str(response)
        except Exception as e:
            log.exception(e)
            return await ctx.message.add_reaction(self.config['fail reaction'])
        # success emoji
        reactions = message.reactions
        for reaction in reactions:
            if reaction.emoji == self.config['fail reaction'] and reaction.me:
                await message.remove_reaction(self.config['fail reaction'], self.bot.user)
        await ctx.message.add_reaction(self.config['success reaction'])
        log.info(f'Successfully created issue #{response["id"]}.')
        # attachments
        try:
            await self.upload_issue_attachments(ctx, response['id'])
        except Exception as e:
            log.exception(e)

    async def check_oauth_token(self):
        """Create or refresh our Bitbucket OAuth2 token."""
        # is our token nonexistent, expired, or expiring in the next 30 seconds?
        if self.oauthclient.expires_in is None or \
                self.oauthclient.expires_in < time.time() + 30:
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
        await self.check_oauth_token()
        title = ctx.message.clean_content
        if len(title) > self.config['title max length']:
            title = title[:self.config['title max length']] + "..."
        message = '  \n> '.join(ctx.message.clean_content.split('\n'))
        content = f"""Marked for crossposting by: {requester.display_name}

Message ([jump](https://discordapp.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id})):

> <{ctx.author.display_name}> {message}
"""
        params = {
            'state': 'new',
            'kind': 'bug',
            'priority': 'trivial',
            'title': f'[#{ctx.channel}] {title}',
            'content': {
                'raw': content
            }
        }
        headers = {'Authorization': f'Bearer {self.oauthclient.token["access_token"]}'}
        async with http_session.post(self.config['endpoint'],
                                     headers=headers,
                                     json=params) as request:
            response = await request.json()
        return response

    async def upload_issue_attachments(self, ctx: Context, issue_id: int):
        """Upload any attachments from the given Discord Context to the issue ID."""
        for num, attachment in enumerate(ctx.message.attachments):
            log.info(f'Uploading attachment {num}: {attachment.filename} ({attachment.size} bytes)')
            headers = {'Authorization': f'Bearer {self.oauthclient.token["access_token"]}'}
            stream = io.BytesIO()
            await attachment.save(stream, seek_begin=True)
            data = aiohttp.FormData()
            data.add_field('file', stream, filename=attachment.filename)
            url = f'{self.config["endpoint"]}/{issue_id}/attachments'
            await http_session.post(url, headers=headers, data=data)
