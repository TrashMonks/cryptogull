import json
import random
from shared import config


class Corpus:
    """
    Uses the game's corpus in order to
    procedurally generate sentences using a markov chain.
    Has a chance of generating a "secret", just like in game.
    """

    def __init__(self):
        self.chain = {}
        self.order = 2
        self.openingwords = {}

        # Load corpus from game files
        self.load_json(config['Qud install folder'] +
                       "/CoQ_Data/StreamingAssets/Base/QudCorpus.txt")

    def generate_sentence(self, seed="") -> str:
        # Generate a single sentence. First two words are seeded/randomly picked.
        if len(seed) == 0 or seed.isspace():
            seed = self.openingwords[random.randint(
                0, len(self.openingwords))]
        list = []

        for i in range(0, self.order):
            list.append(seed.split(' ')[i])
        for i in range(0, 100):
            text = list[i]
            for j in range(1, self.order):
                text = f"{text} {list[i+j]}"
                text2 = self.chain[text][random.randint(
                    0, len(self.chain[text])-1)]

                # Inserts a randomly generated location hint for Isner.
                if text2 == "#MAKESECRET#":
                    text2 = self.make_secret()
                list.append(text2)
                if '.' in text2:
                    return ' '.join(list)
        return text

    def append_secret(self):
        # Add additional keys to the corpus to add a chance for a secret
        # try "?sleeptalk isner test" to guarantee secret generation.
        keys = ["of the", "to the", "in the", "with the", "isner test"]

        for key in keys:
            if key in self.chain:
                self.chain[key].append("#MAKESECRET#")
            else:
                self.chain[key] = ["#MAKESECRET#"]

    def make_secret(self):
        possiblelocations = ["Golgotha", "Grit Gate",
                             "Joppa", "the ruins of Joppa",
                             "Ezra", "the Spindle", "Kyakukya",
                             "Omonporch", "Red Rock",
                             "the Six Day Stilt", "the Yd Freehold",
                             "the Tomb of the Eaters", "Bethesda Susa"]
        directions = ["north", "west", "east", "west"]
        secretpt1 = ["masterwork pistol ",
                     "famous revolver ",
                     "hiding place of the ",
                     "chest containing the ",
                     "chest holding the ", ""]
        secretpt2 = ["said to be", "rumored to be",
                     "located", "where I stored it", "stored somewhere"]
        location = possiblelocations[random.randint(
            0, len(possiblelocations)-1)]

        direction = directions[random.randint(0, 3)]
        # tried to do match/case but compiler complained

        switch = (random.randint(0, 1))
        if switch == 0:
            str1 = f"{secretpt1[random.randint(0, len(secretpt1)-1)]}Ruin of House Isner"
        else:
            str1 = "lost masterwork pistol"

        str2 = f"{secretpt2[random.randint(0, len(secretpt2)-1)]}"\
            f" {random.randint(1,20)} parasangs {direction} of {location}"

        return f"{str1}, {str2}."

    def load_json(self, path):
        with open(path) as json_file:
            data = json.load(json_file)

        self.chain = {}
        for i in range(0, len(data["keys"])):
            self.chain[data["keys"][i]
                       ] = data["values"][i].split('\u0001')
        self.order = data["order"]
        self.openingwords = data["OpeningWords"]
        self.append_secret()
        return data


corpus = Corpus()
