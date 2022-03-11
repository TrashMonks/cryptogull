import json
import random
import logging

from discord.ext.commands import CommandError
from discord.ext.commands import Cog, Context, command
log = logging.getLogger('bot.' + __name__)


class Markov(Cog):
    chain = {}
    order = 2
    data = None

    def __init__():
        load_json("LibraryCorpus.json")

    @command()
    async def sleeptalk(self, ctx: Context, *args):
        """Generate a markov sentence using the Qud corpus."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')

        # TODO: let ppl specify their own seeds. however it will throw
        # a key error if it's not already in there, it's not obvious.
        seed = ' '.join(args)
        msg = generate_sentence()
        await ctx.send(msg)

    def generate_sentence(seed=""):
        if len(seed) == 0 or seed.isspace():
            seed = data["OpeningWords"][random.randint(
                0, len(data["OpeningWords"]))]
        list = []

        for i in range(0, order):
            list.append(seed.split(' ')[i])
        for i in range(0, 100):
            text = list[i]
            for j in range(1, order):
                text = f"{text} {list[i+j]}"
                text2 = chain[text][random.randint(0, len(chain[text])-1)]
                if text2 == "#MAKESECRET#":
                    text2 = make_secret()
                list.append(text2)
                if '.' in text2:
                    return ' '.join(list)
        return text

    def append_secret():
        keys = ["of the", "to the", "in the", "with the", "beep beep"]

        for key in keys:
            if key in chain:
                chain[key].append("#MAKESECRET#")
            else:
                chain[key] = ["#MAKESECRET#"]

    def make_secret():
        possiblelocations = ["Golgotha", "Grit Gate",
                             "Joppa", "the ruins of Joppa", "Ezra", "the Spindle"]
        directions = ["north", "west", "east", "west", "weast"]
        secretpt1 = ["masterwork pistol ",
                     "famous revolver ", "hiding place of the ", "chest containing the ", "chest holding the ", ""]
        secretpt2 = ["said to be", "rumored to be", "located", "where I stored it"]
        location = possiblelocations[random.randint(0, len(possiblelocations)-1)]

        direction = directions[random.randint(0, 4)]
        # tried to do match/case but compiler complained

        switch = (random.randint(0, 1))
        if switch == 0:
            str1 = f"{secretpt1[random.randint(0, len(secretpt1)-1)]}Ruin of House Isner"
        else:
            str1 = "lost masterwork pistol"

        str2 = f"{secretpt2[random.randint(0, len(secretpt2)-1)]} stored somewhere {random.randint(1,20)} parasangs {direction} of {location}"

        return f"{str1}, {str2}."

    def load_json(path):
        with open(path) as json_file:
            data = json.load(json_file)

        for i in range(0, len(data["keys"])):
            chain[data["keys"][i]] = data["values"][i].split('\u0001')
        order = data["order"]
        append_secret()
