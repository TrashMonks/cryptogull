"""
Functions for parsing a Caves of Qud build code into character attributes,
and for building a printable character sheet based on the attributes.
"""

from operator import add
from typing import List

from hagadias.qudtile import QudTile

from bot.shared import gameroot
gamecodes = gameroot.get_character_codes()


class Character:
    """Represents a Caves of Qud player character. This class is intended for modern build codes
    post 2.0.202 which are JSON strings, gzipped and base64-encoded.
    """

    def __init__(self, code: dict):
        """Create a new character from a fully decoded build code."""
        self.code = code
        for module in code['modules']:
            match module['moduleType'].split(', '):
                case ['XRL.CharacterBuilds.Qud.QudGenotypeModule', *_]:
                    self.genotype = module['data']['Genotype']
                case ['XRL.CharacterBuilds.Qud.QudSubtypeModule', *_]:
                    self.subtype = module['data']['Subtype']
                    self.bonuses = gamecodes['class_bonuses'][self.subtype]
                case [('XRL.CharacterBuilds.Qud.QudMutationsModule' |
                       'XRL.CharacterBuilds.Qud.QudCyberneticsModule'), *_]:
                    self.selections = []
                    self.selection_noun = 'Mutation' if 'Mutation' in module['moduleType']\
                        else 'Cybernetic'
                    for selection in module['data']['selections']:
                        if selection['Count'] == 1:
                            self.selections.append(selection[self.selection_noun])
                        else:
                            self.selections.append(selection[self.selection_noun] +
                                                   f' x{selection["Count"]}')
                case ['XRL.CharacterBuilds.Qud.QudAttributesModule', *_]:
                    pointspurchased = module['data']['PointsPurchased']
                    base = 10 if self.genotype == 'Mutated Human' else 12
                    self.attributes = [base + attr for name, attr in pointspurchased.items()]
                case ['XRL.CharacterBuilds.Qud.QudCustomizeCharacterModule', *_]:
                    self.name = module['data']['name']
                    self.pet = module['data']['pet']
                    self.gender = module['data']['gender']
                    self.pronounSet = module['data']['pronounSet']
                case ['XRL.CharacterBuilds.Qud.QudChooseStartingLocationModule', *_]:
                    self.startinglocation = module['data']['StartingLocation']

    def make_sheet(self):
        """Build a printable character sheet for the Character."""
        attr_widths = (11, 11, 11, 14, 14, 14)
        attr_names = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
        attr_strings = []

        for width, attr_text, attr, bonus in zip(attr_widths,
                                                 attr_names,
                                                 self.attributes,
                                                 self.bonuses):
            # print a +/- in front of any existing bonus
            if bonus > 0:
                bonus_text = f'+{bonus}'
            elif bonus < 0:
                bonus_text = f'{bonus}'  # already has a minus sign
            else:
                bonus_text = ''
            attr_strings.append(f'{attr_text:{width}}{attr:2}{bonus_text}')
        if hasattr(self, 'name') and self.name is not None:
            title = f'{self.name} the {self.genotype} {self.subtype}'
        else:
            title = f'{self.genotype} {self.subtype}'
        charsheet = f"""{title}
{attr_strings[0]:18}{attr_strings[3]}
{attr_strings[1]:18}{attr_strings[4]}
{attr_strings[2]:18}{attr_strings[5]}"""
        charsheet += f"\n{self.selection_noun}s: {', '.join(self.selections)}\n"
        charsheet += f"Starting location: {self.startinglocation}"
        return charsheet


class Pre202Character:
    """Represents a Caves of Qud player character. This class was intended for build codes
    between 2.0.200 and 2.0.202 and is no longer supported.

    Will not work for old format build codes, such as build codes from pre-2.0.200.0 (which
    handle stats differently) or some build codes from before the mutation overhaul (which may
    contain deprecated mutations).

    TODO: This code should be removed after a long wait, since these codes will be seen for a while
    """
    def __init__(self,
                 attrs: List[int],       # one integer per stat, in game order
                 bonuses: List[int],     # one integer per stat, 0 if no bonus from class
                 class_name: str,        # i.e. "Apostle"
                 class_called: str,      # "Calling:" or "Caste:"
                 extensions: List[str],  # the list of mutations or implants as strings
                 extname: str,           # "mutations" or "implants"
                 genotype: str,          # "Mutated Human" or "True Kin"
                 skills: List[str],      # the list of skills as strings
                 qud_tile: QudTile       # sprite for this calling or caste
                 ):

        self.attrs = attrs
        self.bonuses = bonuses
        self.class_name = class_name
        self.class_called = class_called
        self.extensions = extensions
        self.extname = extname
        self.genotype = genotype
        self.skills = skills
        self.tile = qud_tile

        self.extensions_codes = ""

    @classmethod
    def from_charcode(cls, charcode: str):
        """
        Take a Qud character build code of at least 8 characters and return a Pre202Character.
        """
        # 1st character: A for true kin, B for mutated human
        genotype = gamecodes['genotype_codes'][charcode[0]]

        # 2nd character is class selection from list (A-L)
        subtypecode = charcode[1]
        if genotype == "True Kin":
            class_name = gamecodes['caste_codes'][subtypecode]
            class_called = "Caste:"
        elif genotype == "Mutated Human":
            class_name = gamecodes['calling_codes'][subtypecode]
            class_called = "Calling:"
        else:
            raise ValueError("Unexpected genotype code")
        bonuses = gamecodes['class_bonuses'][class_name]

        # 3rd-8th characters are STR AGI TOU INT WIL EGO such that A=6, ..., Z=31
        attrs = []
        for _ in charcode[2:8]:
            attrs.append(ord(_) - 59)
        charcode = charcode[8:]

        extensions_codes = charcode

        # after 8th character, characters come in pairs to give mutations or implants (if any)
        extensions = []
        previouscode = None
        if genotype == "True Kin":
            extname = "Implants:  "
        else:
            extname = "Mutations: "
        while len(charcode) > 0:
            if charcode[:2].startswith('#'):
                # Hash plus number indicates a variant of the previous mutation code
                if previouscode is None or previouscode not in gamecodes['mutation_variants']:
                    raise ValueError("Unexpected variant code")
                variant = gamecodes['mutation_variants'][previouscode][int(charcode[1])]
                extensions.pop()
                extensions.append(variant)
            elif charcode[:2] == '16':  # the 16th implant changes depending on arcology of origin
                if subtypecode in 'ABCD':
                    extensions.append(gamecodes['mod_codes']['16'][0])
                if subtypecode in 'EFGH':
                    extensions.append(gamecodes['mod_codes']['16'][1])
                if subtypecode in 'IJKL':
                    extensions.append(gamecodes['mod_codes']['16'][2])
            else:
                if charcode[:2] not in gamecodes['mod_codes']:
                    raise ValueError(f'Invalid mutation or cybernetics code: "{charcode[:2]}"')
                extensions.append(gamecodes['mod_codes'][charcode[:2]])
                if charcode[:2] in gamecodes['mod_bonuses']:
                    bonuses = list(map(add, bonuses, gamecodes['mod_bonuses'][charcode[:2]]))
            previouscode = charcode[:2]
            charcode = charcode[2:]

        # skills are not in the build code, they're determined solely by class
        skills = [skill for skill in gamecodes['class_skills'][class_name]]

        tile = QudTile(filename=gamecodes['class_tiles'][class_name][0],
                       colorstring=get_character_primary_color(extensions),
                       raw_tilecolor=get_character_primary_color(extensions),
                       raw_detailcolor=gamecodes['class_tiles'][class_name][1],
                       qudname=class_name)

        char = Pre202Character(attrs, bonuses, class_name, class_called,
                               extensions, extname, genotype, skills, tile)
        char.extensions_codes = extensions_codes
        return char

    def to_charcode(self) -> str:
        """Return a character build code for the Pre202Character.
        Assumes by default that all attributes are "correct". Cryptogull will accept more build
        codes than are technically valid/supported in game.
        """
        code = ''
        if self.genotype == 'True Kin':
            code = 'A'
        elif self.genotype == 'Mutated Human':
            code = 'B'
        class_codes_flip = {}
        if self.genotype == 'True Kin':
            class_codes_flip = {v: k for k, v in gamecodes['caste_codes'].items()}
        elif self.genotype == 'Mutated Human':
            class_codes_flip = {v: k for k, v in gamecodes['calling_codes'].items()}
        code += class_codes_flip[self.class_name]
        for attr in self.attrs:
            code += chr(attr + 59)
        code += self.extensions_codes
        return code

    def make_sheet(self) -> str:
        """Build a printable character sheet for the Pre202Character."""
        charsheet = f"""Genotype:  {self.genotype}
{self.class_called:11}{self.class_name}"""
        attr_widths = (11, 11, 11, 14, 14, 14)
        attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
        attr_strings = []
        for width, attr_text, attr, bonus in zip(attr_widths, attributes, self.attrs, self.bonuses):
            # print a +/- in front of any existing bonus
            if bonus > 0:
                bonus_text = f'+{bonus}'
            elif bonus < 0:
                bonus_text = f'{bonus}'  # already has a minus sign
            else:
                bonus_text = ''
            attr_strings.append(f'{attr_text:{width}}{attr:2}{bonus_text}')
        charsheet += f"""
{attr_strings[0]:18}{attr_strings[3]}
{attr_strings[1]:18}{attr_strings[4]}
{attr_strings[2]:18}{attr_strings[5]}"""
        charsheet += f"\n{self.extname}{', '.join(self.extensions)}"
        charsheet += f"\nSkills:    {', '.join(self.skills)}"
        return charsheet

    def __str__(self):
        """Return a string representation of the Character."""
        return f'Character {self.to_charcode()}'


def get_character_primary_color(extensions: List[str]) -> str:
    """Obtains a character's primary color.

    Args:
        extensions: List of character's mutations and cybernetics
    """
    return 'y' if 'Photosynthetic Skin' not in extensions else 'g'