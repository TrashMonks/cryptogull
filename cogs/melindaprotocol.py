"""One-time command to download all attachments from a channel into a directory."""
from pathlib import Path

from discord import TextChannel
from discord.ext.commands import Cog, Context, command


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
        await ctx.send(f'Melinda protocol activated on channel {textchannel}.')
        async for message in textchannel.history():
            print(message)
            if len(message.attachments) > 0:
                for attachment in message.attachments:
                    await attachment.save(melinda_path / attachment.filename)
                    with open(melinda_path / 'credits.txt', 'a') as f:
                        f.write(f'{attachment.filename}: https://discordapp.com/channels/'
                                f'{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}')
