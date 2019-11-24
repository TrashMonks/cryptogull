"""Commands for preserving Discord messages in another channel."""
import logging
import re

from discord import Embed, TextChannel, Colour, Message
from discord.ext.commands import (Cog, CommandError, MessageConverter,
                                  TextChannelConverter, group, Context)

log = logging.getLogger('bot.' + __name__)


async def can_manage_messages(author, dest_channel) -> bool:
    if not dest_channel.permissions_for(author).manage_messages:
        return False
    else:
        return True


class Cryochamber(Cog):
    def __init__(self, _):
        self.ongoing_preservations = set()

    @group(invoke_without_command=True)
    async def preserve(self, context: Context, *, arg):
        """Main preserve function. Things in [] are optional arguments, stuff in () are variables.
            The user must be able to manage messages in order to invoke these functions. | means
            options.

               ?preserve (message link)|(message id) in (destination channel)
                   Message link can be gotten by enabling developer mode on Discord in Appearance
                   and selecting "Copy Link" or "Copy ID".

               ?preserve [future|no more] pins from (original channel) in (destination channel)
                   Embeds all messages pinned in the specified channel and reposts them in order or
                   pinned, earliest first.

                   future  | **NOT FULLY IMPLEMENTED**
                             any future pins in that channel will be immeadiately reposted to the
                             destination. All current channels tagged with this can be checked
                             using ?preserve what
                   no more | cancel a previous command that uses future.

               ?preserve what **NOT FULLY IMPLEMENTED**
                   Returns all original channel - destination channels tagged as future pins as a
                   set."""
        log.info(f'({context.message.channel})'
                 f' <{context.message.author}>'
                 f' {context.message.content}')
        get_channel = TextChannelConverter().convert
        get_message = MessageConverter().convert
        # regex test link: https://regex101.com/r/kb819e/1
        exp = r'(?P<source_specifier>.*?) in (?P<destination_channel_specifier>.*?)'
        command_match = re.fullmatch(exp, arg)

        if command_match is None:
            raise CommandError('wrong syntax: ' + arg)

        dest_channel = await get_channel(context,
                                         command_match.group('destination_channel_specifier'))
        # inline check to see if the author has the proper manage message permissions
        if can_manage_messages(context.message.author, dest_channel) is False:
            return await context.send('You do not have the proper permissions to use this command.')

        # regex test link: https://regex101.com/r/pMzemV/1/
        exp = r'(?:(?P<temporal_modifier>future|no more) )' \
              r'?pins from (?P<source_channel_specifier>.*?)'
        source_channel_match = re.fullmatch(exp,
                                            command_match.group('source_specifier'))

        if source_channel_match is None:
            source_message = await get_message(context, command_match.group('source_specifier'))
            await self._preserve_message(source_message, dest_channel)
        else:
            src_channel = await get_channel(context,
                                            source_channel_match.group('source_channel_specifier'))
            temporal_modifier = source_channel_match.group('temporal_modifier')

            if temporal_modifier is None:
                for pin in sorted(await src_channel.pins(), key=lambda message: message.created_at):
                    await self._preserve_message(pin, dest_channel)
            elif temporal_modifier == 'future':
                self.ongoing_preservations.add((src_channel.name, dest_channel.name))
            elif temporal_modifier == 'no more':
                self.ongoing_preservations.remove((src_channel.name, dest_channel.name))
            else:
                raise ValueError('unknown temporal modifier: ' + temporal_modifier)

    @preserve.command()
    async def what(self, context: Context):
        """Replies with which channels the bot is currently watching for future pins,
        and where it's reposting to."""
        await context.send(str(self.ongoing_preservations))

    async def _preserve_message(self, message: Message, channel: TextChannel):
        """Sends the preserved message. It formats an embed containing the original message with a
        link back to the original as well as denoting how many attachments there are. It will only
        embed the first image included."""
        attach_str = ""
        if len(message.attachments) > 0:
            attach_str = "" + str(len(message.attachments)) + " attachment" +\
                         ("s" if len(message.attachments) > 1 else "") + ""

        embedded_msg = Embed(colour=Colour(0xf403f),
                             description=message.content,
                             timestamp=message.created_at)
        embedded_msg.set_author(name=message.author.name + '#' + message.author.discriminator +
                                ", aka " + message.author.display_name,
                                icon_url=str(message.author.avatar_url))
        embedded_msg.add_field(name="__              __",
                               value=attach_str + " [(original)](" + message.jump_url + ")")
        embedded_msg.set_footer(text="in #" + message.channel.name)
        for attach in message.attachments:
            if attach.width is not None and attach.height is not None:
                embedded_msg.set_image(url=attach.url)
        await channel.send(embed=embedded_msg)
