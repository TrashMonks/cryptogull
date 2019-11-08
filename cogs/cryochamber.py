import re

from discord import Embed, Attachment, Colour
from discord.ext.commands import Cog, CommandError, MessageConverter, TextChannelConverter, group

class Cryochamber(Cog):
    def __init__(self, _):
        self.ongoing_preservations = set()

    @group(invoke_without_command=True)
    async def preserve(self, context, *, arg):
        get_channel = TextChannelConverter().convert
        get_message = MessageConverter().convert
        command_match = re.fullmatch(r'(?P<source_specifier>.*?) in (?P<destination_channel_specifier>.*?)', arg)

        if command_match is None:
            raise CommandError('wrong syntax: ' + arg)

        destination_channel = await get_channel(context, command_match.group('destination_channel_specifier'))

        if not destination_channel.permissions_for(context.author).manage_messages:
            raise MissingPermissions(['manage_messages'])

        source_channel_specifier_match = re.fullmatch(r'(?:(?P<temporal_modifier>future|no more) )?pins from (?P<source_channel_specifier>.*?)', command_match.group('source_specifier'))

        if source_channel_specifier_match is None:
            source_message = await get_message(context, command_match.group('source_specifier'))
            await self._preserve_message(source_message, destination_channel)
        else:
            source_channel = await get_channel(context, source_channel_specifier_match.group('source_channel_specifier'))
            temporal_modifier = source_channel_specifier_match.group('temporal_modifier')

            if temporal_modifier is None:
                for pin in sorted(await source_channel.pins(), key=lambda message: message.created_at):
                    await self._preserve_message(pin, destination_channel)
            elif temporal_modifier == 'future':
                self.ongoing_preservations.add((source_channel.name, destination_channel.name))
            elif temporal_modifier == 'no more':
                self.ongoing_preservations.remove((source_channel.name, destination_channel.name))
            else:
                raise ValueError('unknown temporal modifier: ' + temporal_modifier)

    @preserve.command()
    async def what(self, context):
        await context.send(self.ongoing_preservations)

    async def _preserve_message(self, message, channel):
        attach_str = ""
        if len(message.attachments) > 0:
            attach_str = "" + str(len(message.attachments)) + " attachment" + ("s" if len(message.attachments) > 1 else "") + ""

        embedded_msg = Embed(colour=Colour(0xf403f), description=message.content, timestamp=message.created_at)
        embedded_msg.set_author(name=message.author.name + '#' + message.author.discriminator + ", aka " + message.author.display_name, icon_url= str(message.author.avatar_url))
        embedded_msg.add_field(name="__              __", value=attach_str + " [(original)](" + message.jump_url + ")")
        embedded_msg.set_footer(text="in #" + message.channel.name)
        for attach in message.attachments:
            if attach.width is not None and attach.height is not None:
                embedded_msg.set_image(url = attach.url)
        await channel.send(embed=embedded_msg)
