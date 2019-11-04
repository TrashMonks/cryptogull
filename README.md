# cryptogull
A Discord bot for the [Caves of Qud discord](https://discordapp.com/invite/cavesofqud) (invite link).

Features:
 * Decode Caves of Qud character build codes into formatted character sheets
 * Perform title and fulltext searches on the [official Caves of Qud wiki](https://cavesofqud.gamepedia.com/)
 * Render tiles from the game and send them to Discord as attachments, with optional recoloring previews for modders

Cryptogull depends on another Trash Monks project, the [hagadias](https://github.com/TrashMonks/hagadias) library, to
read and interpret the game files.

## Contributing
Pull requests are welcome, and the Trash Monks channel on Discord can also be joined on request. In order to send changes
to the bot, it's best if you test them first. Here's a guide on how to do that.

### Steps to test
1. Log in to the [Discord Developer Portal](https://discordapp.com/developers/applications/) and create a new
application. Call it something memorable, but this will not be the final name that the bot appears by in Discord.
2. Skip directly to the "Bot" tab of the application you created. Set the icon and username here. These can be changed
later. Click the button to reveal the bot token. Copy this token into `discordtoken.sec` in the Cryptogull source
directory. This file is listed in `.gitignore`, so you don't have to worry about accidentally sharing it through git.
3. Create a private Discord server for yourself through the Discord client. The button is on the left under the list of
servers you're in.
4. Grab the 'Client ID' from the 'General Information' tab of the Discord application you created (different from your
bot token!)
5. Grab the permissions number you need from the 'Bot' tab of the Discord application you created. This should be 100352,
which is the number created by checking the 'Send Messages', 'Attach Files', and 'Read Message History' checkboxes. If
you're developing features that use higher permissions, check those permission boxes as well and use the permissions number
created by doing that.
6. Craft a URL to join the bot the the server. The format is
`https://discordapp.com/api/oauth2/authorize?client_id=xxxxxxxxxxxxxxxxxx&scope=bot&permissions=y`
where the `x`s are the number from **step 4**, and `y` is the number from **step 5**.
7. Go to the URL to join your bot user to the new server. Accept any prompts.
8. Run `bot.py`. It will load the bot token from `discordtoken.sec` and connect to Discord, appearing in the server you
added it to.

If you want to test character code decoding, there's a whitelist of channels in `config.yml`. Add yours there. The bot
shouldn't listen to itself, but just in case, add the bot user ID to the 'Users to ignore' list. To get these IDs, just
turn on 'developer mode' in the Discord client, under User Settings->Appearance. Then right click on anything to get its
ID.
