"""
Functions for parsing a Caves of Qud build code into character attributes,
and for building a printable character sheet based on the attributes.
"""

from operator import add
from typing import List

from shared import gameroot
gamecodes = gameroot.get_character_codes()


def point_spend(attr: int, base: int) -> int:
    """Return the number of stat points required to raise a stat from base to given value."""
    spent = 0
    if attr > 18:
        spent += (attr - 18) * 2
        attr = 18
    spent += attr - base
    return spent


class Character:
    """Represents a Caves of Qud game character."""

    def __init__(self,
                 attrs: List[int],       # one integer per stat, in game order
                 bonuses: List[int],     # one integer per stat, 0 if no bonus from class
                 class_name: str,        # i.e. "Apostle"
                 class_called: str,      # "Calling:" or "Caste:"
                 extensions: List[str],  # the list of mutations or implants as strings
                 extname: str,           # "mutations" or "implants"
                 genotype: str,          # "Mutated Human" or "True Kin"
                 skills: List[str]       # the list of skills as strings
                 ):

        self.attrs = attrs
        self.bonuses = bonuses
        self.class_name = class_name
        self.class_called = class_called
        self.extensions = extensions
        self.extname = extname
        self.genotype = genotype
        self.skills = skills

    @classmethod
    def from_charcode(cls, charcode: str):
        """
        Take a Qud character build code of at least 8 characters and return a Character.
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

        # after 8th character, characters come in pairs to give mutations or implants (if any)
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
        skills = [skill for skill in gamecodes['class_skills'][class_name]]

        return Character(attrs, bonuses, class_name, class_called,
                         extensions, extname, genotype, skills)

    def make_sheet(self) -> str:
        """Build a printable character sheet for the Character."""
        charsheet = f"""Genotype:  {self.genotype}
{self.class_called:11}{self.class_name}"""
        attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
        attr_strings = []
        for attr_text, attr, bonus in zip(attributes, self.attrs, self.bonuses):
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
        charsheet += f"\n{self.extname}{', '.join(self.extensions)}"
        charsheet += f"\nSkills:    {', '.join(self.skills)}"
        return charsheet

    def make_sheet_qud_beta(self) -> str:
        """Build a printable character sheet for the Character.

        Interprets character attributes differently on the Qud beta branch.
        """
        attributes = ('Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:')
        attr_strings = []
        for attr_text, attr, bonus in zip(attributes, self.attrs, self.bonuses):
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

    @property
    def origin(self) -> str:
        """Return 'beta' if this character code adds up to a max point spend from
        post-2.0.200.0 (the 'beta branch') of Caves of Qud, 'stable' if it is from
        before that, or 'unknown' if it is from neither (maybe altered)."""
        mutant_points = 44
        truekin_points = 38
        points_spent = 0
        base = 12 if self.genotype == "True Kin" else 10
        origin = 'unknown'
        # check if this adds up to a beta character
        went_negative = False
        for attr in self.attrs:
            if attr < base:
                went_negative = True
            points_spent += point_spend(attr, base)
        if (self.genotype == "Mutated Human" and points_spent == mutant_points)\
                or (self.genotype == "True Kin" and points_spent == truekin_points)\
                and not went_negative:
            origin = 'beta'
        # check if this adds up to a stable character
        points_spent = 0
        went_negative = False
        for attr, bonus in zip(self.attrs, self.bonuses):
            attr -= bonus
            if attr < base:
                went_negative = True
            points_spent += point_spend(attr, base)
        if (self.genotype == "Mutated Human" and points_spent == mutant_points)\
                or (self.genotype == "True Kin" and points_spent == truekin_points)\
                and not went_negative:
            origin = 'stable'
        return origin
