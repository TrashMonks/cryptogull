"""
Functionality for parsing a Caves of Qud build code into character attributes,
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
                        mod = selection[self.selection_noun]
                        if selection['Count'] > 1:
                            # Unstable Genome stack
                            self.selections.append(mod + f' x{selection["Count"]}')
                            continue
                        if self.selection_noun == "Cybernetic" and mod is None:
                            # True Kin with no implant - +1 toughness
                            self.bonuses[2] += 1
                            self.selections.append("None")
                            continue
                        self.selections.append(mod)  # regular mutation or cybernetic
                        if mod in gamecodes["mod_bonuses"]:
                            # some mutations or implants confer stat bonuses
                            self.bonuses = list(
                                map(add, self.bonuses, gamecodes["mod_bonuses"][mod])
                            )
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
        self.tile = QudTile(filename=gamecodes['class_tiles'][self.subtype][0],
                            colorstring=get_character_primary_color(self.selections),
                            raw_tilecolor=get_character_primary_color(self.selections),
                            raw_detailcolor=gamecodes['class_tiles'][self.subtype][1],
                            qudname=self.subtype)

    def make_sheet(self) -> str:
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


def get_character_primary_color(extensions: List[str]) -> str:
    """Obtains a character's primary color.

    Args:
        extensions: List of character's mutations and cybernetics
    """
    return 'y' if 'Photosynthetic Skin' not in extensions else 'g'
