"""
Functions for parsing a Caves of Qud build code into character attributes,
and for building a printable character sheet based on the attributes.
"""

import pprint
import logging
from typing import Union
from operator import add as add

from gamedata import read_gamedata

log = logging.getLogger(__name__)


def decode(charcode: str, gamecodes: dict) -> Union[str, None]:
    """
    Take a Qud character build code of at least 8 characters and return a text description.
    """
    # 1st character: A for true kin, B for mutated human
    genotype = gamecodes['genotype_codes'][charcode[0]]

    # 2nd character is class selection from list (A-L)
    subtypecode = charcode[1]
    if genotype == "True Kin":
        class_ = gamecodes['caste_codes'][subtypecode]
        class_called = "Caste:"
    elif genotype == "Mutated Human":
        class_ = gamecodes['calling_codes'][subtypecode]
        class_called = "Calling:"
    else:
        raise ValueError("Unexpected genotype code")
    bonuses = gamecodes['class_bonuses'][class_]

    # 3rd-8th characters are STR AGI TOU INT WIL EGO such that A=6, ..., Z=31
    attrs = []
    for _ in charcode[2:8]:
        attrs.append(ord(_) - 59)
    charcode = charcode[8:]

    # after 8th character, characters come in pairs to give either mutations or implants (if any)
    extensions = []
    if genotype == "True Kin":
        extname = "Implants:  "
    else:
        extname = "Mutations: "
    while len(charcode) > 0:
        if charcode[:2] == '16':  # the 16th implant changes depending on arcology of origin
            if subtypecode in 'ABCD':
                extensions.append(gamecodes['mod_codes']['16'][0])
            if subtypecode in 'EFGH':
                extensions.append(gamecodes['mod_codes']['16'][1])
            if subtypecode in 'IJKL':
                extensions.append(gamecodes['mod_codes']['16'][2])
        else:
            extensions.append(gamecodes['mod_codes'][charcode[:2]])
            if charcode[:2] in gamecodes['mod_bonuses']:
                bonuses = list(map(add, bonuses, gamecodes['mod_bonuses'][charcode[:2]]))
        charcode = charcode[2:]

    # skills are not in the build code, they're determined solely by class
    skills = [skill for skill in gamecodes['class_skills'][class_]]

    return make_sheet(attrs, bonuses, class_, class_called, extensions, extname, genotype,
                      skills)


def make_sheet(attrs, bonuses, class_, class_called, extensions, extname, genotype, skills):
    """Build a printable character sheet given the parsed attributes."""
    charsheet = f"""Genotype:  {genotype}
{class_called:11}{class_}"""
    attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
    attr_strings = []
    for attr_text, attr, bonus in zip(attributes, attrs, bonuses):
        if bonus == 0:
            attr_strings.append(f'{attr_text:14}{attr:2}')
        elif bonus > 0:
            attr_strings.append(f'{attr_text:14}{attr - bonus:2}+{bonus}')
        elif bonus < 0:
            attr_strings.append(f'{attr_text:14}{attr - bonus:2}{bonus}')
    charsheet += f"""
{attr_strings[0]:21}    {attr_strings[3]}
{attr_strings[1]:21}    {attr_strings[4]}
{attr_strings[2]:21}    {attr_strings[5]}"""
    charsheet += f"\n{extname}{', '.join(extensions)}"
    charsheet += f"\nSkills:    {', '.join(skills)}"
    return charsheet


# optional interactive mode for testing:
if __name__ == '__main__':
    gamedata = read_gamedata()
    pprint.pprint(gamedata)
    while True:
        code = input("Enter code: ")
        print(decode(code, gamedata))
