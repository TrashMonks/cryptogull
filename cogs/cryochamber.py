import re

<<<<<<< HEAD
from discord import Embed, Attachment, Colour
from discord.ext.commands import Cog, CommandError, MessageConverter, TextChannelConverter, command
=======
from discord import Embed, Attachment, Colour
from discord.ext.commands import Cog, CommandError, MessageConverter, TextChannelConverter, command
>>>>>>> 9e08f303e6257922aa511fee9e09d187d4f3ddec

class Cryochamber(Cog):
    @command()
    async def preserve(self, context, *, arg):
        get_channel = TextChannelConverter().convert
        get_message = MessageConverter().convert
        command_match = re.fullmatch(r'(?P<source_specifier>.*?) in (?P<destination_channel_specifier>.*?)', arg)

        if command_match is None:
            raise CommandError('wrong syntax: ' + arg)

        destination_channel = await get_channel(context, command_match.group('destination_channel_specifier'))

        if not destination_channel.permissions_for(context.author).manage_messages:
            raise MissingPermissions(['manage_messages'])

        source_channel_specifier_match = re.fullmatch(r'pins from (?P<source_channel_specifier>.*?)', command_match.group('source_specifier'))

        if source_channel_specifier_match is None:
            source_message = await get_message(context, command_match.group('source_specifier'))
            await self._preserve_message(source_message, destination_channel)
        else:
            source_channel = await get_channel(context, source_channel_specifier_match.group('source_channel_specifier'))

            for pin in sorted(await source_channel.pins(), key=lambda message: message.created_at):
                await self._preserve_message(pin, destination_channel)

    async def _preserve_message(self, message, channel):
        embedded_msg = Embed(colour=Colour(0xf403f), description=message.content + " [(original message)](" + message.jump_url + ")", timestamp=message.created_at)
        embedded_msg.set_author(name=message.author.name, icon_url= str(message.author.avatar_url))
        embedded_msg.set_footer(text="in #" + message.channel.name)
        for attach in message.attachments:
            embedded_msg.set_image(url = attach.url)
        await channel.send(embed=embedded_msg)
        