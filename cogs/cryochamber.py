from discord.ext.commands import Cog, TextChannelConverter, command

class Cryochamber(Cog):
    @command()
    async def preserve_pins(self, context, from_channel_name, to_channel_name):
        convert = TextChannelConverter().convert
        from_channel = await convert(context, from_channel_name)
        to_channel = await convert(context, to_channel_name)

        for pin in sorted(await from_channel.pins(), key=lambda message: message.created_at):
            await to_channel.send(pin)
