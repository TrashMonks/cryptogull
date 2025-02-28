import json
import random
import re
from bot.shared import config


class Corpus:
    """
    Uses the game's corpus in order to procedurally generate sentences using a Markov chain.
    Has a chance of generating a "secret", just like in game.
    """

    def __init__(self):
        self.chain: dict[str: list[str]] = {}
        self.order = 2
        self.openingwords = {}

        # Load corpus from game files
        self.load_json(config['Qud install folder'] +
                       "/CoQ_Data/StreamingAssets/Base/LibraryCorpus.json")

    def get_pair(self, seed):
        # Finds a pair, but only one. Returns None if no pairs were found at all.
        pair = self.get_pairs(seed)
        if len(pair) == 0:
            return None
        return pair[random.randint(0, len(pair)-1)]

    def get_pairs(self, seed, strictmatch=False):
        # Returns a proper pair for corpus matching. If seed is only one word,
        # returns a list of pairs starting with the word, case insensitive.

        text = ' '.join(seed)
        flags = 0
        regex = r""
        if len(seed) >= 2:
            if strictmatch:  # TODO: have strictmatch actually togglable
                if text in self.chain:
                    return text
                return []
            else:
                possiblepairs = []
                # remove punctuation from seed
                cleanedseed = re.search(r"\b(\w+)\b.+\b(\w+)\b", text).groups()
                flags = re.IGNORECASE
                regex = fr"\b{cleanedseed[0]}\b.+\b{cleanedseed[1]}\b"
            for pair in self.chain:
                if re.search(regex, pair, flags=flags) is not None:
                    possiblepairs.append(pair)
            return possiblepairs
        else:
            possiblepairs = []
            if not strictmatch:
                flags = re.IGNORECASE
            regex = fr"^\W*\b{text}\b"
            for pair in self.chain:
                if re.search(regex, pair, flags=flags) is not None:
                    possiblepairs.append(pair)
            return possiblepairs

    def generate_sentence(self, seed="") -> str:
        """Generate a single sentence. First two words are seeded/randomly picked."""
        if len(seed) == 0 or seed.isspace():
            seed = self.openingwords[random.randint(0, len(self.openingwords))]
        words = []

        # manual seeding: allow number of words up to self.order
        words.extend(seed.split(' ')[:self.order])
        for i in range(0, 100):
            text = words[i]
            for j in range(1, self.order):
                text = f"{text} {words[i+j]}"
                text2 = self.chain[text][random.randint(0, len(self.chain[text])-1)]
                # Inserts a randomly generated location hint for Isner.
                if text2 == "#MAKESECRET#":
                    text2 = self._make_secret()
                words.append(text2)
                if '.' in text2:
                    return ' '.join(words)
        return text

    def _append_secret(self):
        # Add additional keys to the corpus to add a chance for a secret
        # try "?sleeptalk isner test" to guarantee secret generation.
        keys = ["of the", "to the", "in the", "with the", "isner test"]

        for key in keys:
            if key in self.chain:
                self.chain[key].append("#MAKESECRET#")
            else:
                self.chain[key] = ["#MAKESECRET#"]

    def _make_secret(self) -> str:
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

        switch = (random.randint(0, 1))
        if switch == 0:
            str1 = f"{secretpt1[random.randint(0, len(secretpt1)-1)]}Ruin of House Isner"
        else:
            str1 = "lost masterwork pistol"

        str2 = f"{secretpt2[random.randint(0, len(secretpt2)-1)]}"\
            f" {random.randint(1,20)} parasangs {direction} of {location}"

        return f"{str1}, {str2}."

    def load_json(self, path):
        with open(path, encoding='utf-8') as json_file:
            data = json.load(json_file)
        for key, values in zip(data["keys"], data["values"]):
            if len(values):  # guard against buggy key:value pairs with "" as the value
                splitvalues = values.split('\u0001')
                if key in self.chain:
                    for value in splitvalues:
                        if value not in self.chain[key]:
                            self.chain[key].append(value)
                else:
                    self.chain[key] = splitvalues
        self.order = data["order"]
        self.openingwords = data["OpeningWords"]
        self._append_secret()
        return data


# Single instance for export
corpus = Corpus()
