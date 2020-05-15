"""
Functions for parsing a Caves of Qud build code into character attributes,
and for building a printable character sheet based on the attributes.
"""

from collections import namedtuple
from operator import add

from shared import gameroot
gamecodes = gameroot.get_character_codes()

Character = namedtuple('Character', ['attrs', 'bonuses', 'class_', 'class_called',
                                     'extensions', 'extname', 'genotype', 'skills'])


def decode(charcode: str) -> Character:
    """
    Take a Qud character build code of at least 8 characters and return a Character.
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

    return Character(attrs, bonuses, class_, class_called, extensions, extname, genotype, skills)


def make_sheet(charcode: str) -> str:
    """Build a printable character sheet given the parsed attributes."""
    char = decode(charcode)
    charsheet = f"""Genotype:  {char.genotype}
{char.class_called:11}{char.class_}"""
    attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
    attr_strings = []
    for attr_text, attr, bonus in zip(attributes, char.attrs, char.bonuses):
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
    charsheet += f"\n{char.extname}{', '.join(char.extensions)}"
    charsheet += f"\nSkills:    {', '.join(char.skills)}"
    return charsheet


def make_sheet_qud_beta(charcode: str) -> str:
    """Build a printable character sheet given the parsed attributes.

    Interprets character attributes differently on the Qud beta branch.
    """
    char = decode(charcode)
    attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
    attr_strings = []
    for attr_text, attr, bonus in zip(attributes, char.attrs, char.bonuses):
        if bonus == 0:
            attr_strings.append(f'{attr_text:14}{attr:2}')
        elif bonus > 0:
            attr_strings.append(f'{attr_text:14}{attr:2}+{bonus}')
        elif bonus < 0:
            attr_strings.append(f'{attr_text:14}{attr:2}{bonus}')
    charsheet = f"""
{attr_strings[0]:21}    {attr_strings[3]}
{attr_strings[1]:21}    {attr_strings[4]}
{attr_strings[2]:21}    {attr_strings[5]}"""
    return charsheet


def point_spend(attr: int, base: int) -> int:
    """Return the number of stat points required to raise a stat from base to given value."""
    spent = 0
    if attr > 18:
        spent += (attr - 18) * 2
        attr = 18
    spent += attr - base
    return spent


def charcode_origin(charcode: str) -> str:
    """Return 'beta' if this character code adds up to a max point spend from
    post-2.0.200.0 (the 'beta branch') of Caves of Qud, 'stable' if it is from
    before that, or 'unknown' if it is from neither (maybe altered)."""
    mutant_points = 44
    truekin_points = 38
    char = decode(charcode)
    points_spent = 0
    base = 12 if char.genotype == "True Kin" else 10
    origin = 'unknown'
    # check if this adds up to a beta character
    went_negative = False
    for attr in char.attrs:
        if attr < base:
            went_negative = True
        points_spent += point_spend(attr, base)
    if (char.genotype == "Mutated Human" and points_spent == mutant_points)\
            or (char.genotype == "True Kin" and points_spent == truekin_points)\
            and not went_negative:
        origin = 'beta'
    # check if this adds up to a stable character
    points_spent = 0
    went_negative = False
    for attr, bonus in zip(char.attrs, char.bonuses):
        attr -= bonus
        if attr < base:
            went_negative = True
        points_spent += point_spend(attr, base)
    if (char.genotype == "Mutated Human" and points_spent == mutant_points)\
            or (char.genotype == "True Kin" and points_spent == truekin_points)\
            and not went_negative:
        origin = 'stable'
    return origin
