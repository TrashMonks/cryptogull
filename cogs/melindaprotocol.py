"""One-time command to download all attachments from a channel into a directory."""
from pathlib import Path

from discord import TextChannel
from discord.ext.commands import Cog, Context, command

from shared import http_session


class MelindaProtocol(Cog):
    """Functionality for mass downloading attachments."""
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def melindaprotocol(self, ctx: Context, channel: int):
        """Internal command to download all attachments from the specified channel."""
        cwd = Path.cwd()
        melinda_path = cwd / 'melindaprotocol'
        if not melinda_path.exists():
            melinda_path.mkdir()
        textchannel: TextChannel = self.bot.get_channel(channel)
        await ctx.send(f'Melinda Protocol activated on channel {textchannel}.')
        async for message in textchannel.history():
            msgctx: Context = await self.bot.get_context(message)
            if len(message.attachments) > 0:
                for attachment in message.attachments:
                    await attachment.save(melinda_path / attachment.filename)
                    with open(melinda_path / 'credits.txt', 'a') as f:
                        f.write(f'{attachment.filename}: https://discordapp.com/channels/'
                                f'{msgctx.guild.id}/{msgctx.channel.id}/{msgctx.message.id}')

    @command()
    async def ivyprotocol(self, ctx: Context, channel: int):
        """Internal command to download all embedded images from the specified channel."""
        cwd = Path.cwd()
        ivy_path = cwd / 'ivyprotocol'
        if not ivy_path.exists():
            ivy_path.mkdir()
        textchannel: TextChannel = self.bot.get_channel(channel)
        await ctx.send(f'Ivy Protocol activated on channel {textchannel}.')
        async for message in textchannel.history():
            msgctx: Context = await self.bot.get_context(message)
            if len(message.embeds) > 0:
                for embed in message.embeds:
                    try:
                        filename = embed.image.url.split('/')[-1]
                        async with http_session.get(embed.image.url) as resp:
                            with open(ivy_path / filename, 'wb') as f:
                                f.write(await resp.read())
                        with open(ivy_path / 'credits.txt', 'a') as f:
                            f.write(f'{filename}: https://discordapp.com/channels/'
                                    f'{msgctx.guild.id}/{msgctx.channel.id}/{msgctx.message.id}')
                    except Exception as e:
                        print(e)
