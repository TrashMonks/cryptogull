# cryptogull
A Discord bot for the [Caves of Qud
discord](https://discordapp.com/invite/cavesofqud) (invite link).

Features:
 * Decode Caves of Qud character build codes into formatted character sheets
 * Perform title and fulltext searches on the [official Caves of Qud
   wiki](https://wiki.cavesofqud.com/)
 * Render tiles from the game and send them to Discord as attachments, with
   optional recoloring previews for modders

Cryptogull depends on another Trash Monks project, the
[hagadias](https://github.com/TrashMonks/hagadias) library, to read the game
files.

Contributions from the community in the form of issues or pull requests are
welcome. This project uses the Code of Conduct available from that Discord
server, in the `#code-of-conduct` channel.

## How to use
1. Clone this repository. You need Docker installed.
2. Create a `config.yml` in your project directory from the provided
   `config.example.yml`.
   2a. The Qud install folder is the location of the install in the docker
       container, not your actual game file.
3. Log in to the [Discord Developer
   Portal](https://discordapp.com/developers/applications/) and create a new
   application. The name of the application is not your bot's username.
4. Skip directly to the "Bot" tab of the application you created. Set the icon
   and username here. These can be changed later. Click the button to reveal the
   bot token. Copy this token into the `Discord token:` field in `config.yml`.
5. Turn on the "Server Members Intent" slider in the Bot tab.
6. If you don't have a private Discord server to test in, make one.
7. Grab the 'Application ID' from the 'General Information' tab of the Discord
   application you created (different from your bot token!)
8. Grab the permissions number you need from the 'Bot' tab of the Discord
   application you created. This should be 100352, which is the number created
   by checking the 'Send Messages', 'Attach Files', and 'Read Message History'
   checkboxes. If you're developing features that use higher permissions, check
   those permission boxes as well and use the permissions number created by
   doing that.
9. Craft a URL to join your bot to your server. The format is
   `https://discordapp.com/api/oauth2/authorize?client_id=xxxxxxxxxxxxxxxxxx&scope=bot&permissions=y`
   where the `x`s are the number from **step 7**, and `y` is the number from
   **step 8**.
10. Go to the URL and accept any prompts.
11. Run the bot through Docker using the commands below.

### Issue tracker configuration
Cryptogull uses an app password to authenticate with the Bitbucket issue tracker.

More info can be found at https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/.

## Example docker commands
If on Linux, and the docker daemon is not running already:

```bash
sudo dockerd
```

To build and run the bot:

```bash
docker build . -t cryptogull:latest
docker run -it --rm -v ./config.yml:/home/cryptogull/config.yml -v "C:\Steam\steamapps\common\Caves of Qud":"/home/cryptogull/Caves of Qud" -v ./Textures:/home/cryptogull/Textures --name cryptogull cryptogull:latest
```
Replace "C:\Steam\.." with your own game installation location.

This attaches the config file, game data folder, and tile art folder as volumes
inside the running container.

## Tile support
Tile support requires a full extract of the game Textures directory. To get an
up-to-date copy of the game textures, install the
[brinedump](https://github.com/TrashMonks/brinedump) mod and use the
`brinedump:textures` wish.
