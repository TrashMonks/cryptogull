import discord
import logging
import re
import qud_decode
import time


logging.basicConfig(filename='bot.log', level=logging.INFO)

client = discord.Client()

gamecodes = qud_decode.read_gamedata()
valid_charcode = re.compile(r"[AB][A-L][A-Z]{6}(?:[01ABCDEU][0-9A-Z])*")


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')


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

if __name__ == '__main__':
    with open('discordtoken.sec') as f:
        token = f.read()
        client.run(token)
