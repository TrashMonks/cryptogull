import discord
import logging
import re
import qud_decode
import asyncio
import time


logging.basicConfig(filename='bot.log', level=logging.INFO)

gamecodes = qud_decode.read_gamedata()
with open('discordtoken.sec') as f:
    token = f.read()
client = discord.Client()
valid_charcode = re.compile(r"[AB][A-L][A-Z]{6}(?:[01ABCDEU][0-9A-Z])*")


def handle_exit():
    logging.info("Attempting to shutdown gracefully...")
    client.loop.run_until_complete(client.logout())
    for t in asyncio.Task.all_tasks(loop=client.loop):
        if t.done():
            t.exception()
            continue
        t.cancel()
        try:
            client.loop.run_until_complete(asyncio.wait_for(t, 5, loop=client.loop))
            t.exception()
        except asyncio.InvalidStateError:
            pass
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            pass


while True:
    @client.event
    async def on_ready():
        logging.info(f'Logged in as {client.user}.')


    @client.event
    async def on_message(message):
        if message.channel.name not in ('character-builds', 'huff'):  # huff is my testing channel
            return

        if message.author == client.user:
            return

        match = valid_charcode.search(message.content)
        if match:
            code = match[0]
            logging.info(f'Received a message with matching character build code:')
            logging.info(f'<{message.author}> {message.content}')
            decode = qud_decode.decode(code, gamecodes)
            if decode:
                response = "```\n" + decode + "\n```"
                await client.send_message(message.channel, response)
                logging.info(f'Replied with {response}')
            else:
                logging.error(f"Character code {code} did not decode successfully.")

    try:
        client.loop.run_until_complete(client.start(token))
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        handle_exit()
        client.loop.close()
        logging.info("Shut down.")
        break
    except Exception as e:
        logging.exception("Caught unexpected error, will try to restart in 60 seconds.", exc_info=True)
        handle_exit()
        time.sleep(60)
    logging.info("Restarting...")
    client = discord.Client(loop=client.loop)
