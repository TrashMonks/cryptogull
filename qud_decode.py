import xml.etree.ElementTree as et
import pprint
import logging
from typing import Union
from operator import add as add

log = logging.getLogger(__name__)

# These files need to be copied in from, e.g.,
# SteamLibrary\SteamApps\common\Caves of Qud\CoQ_Data\StreamingAssets\Base
GENO = et.parse('xml/Genotypes.xml').getroot()
SKILLS = et.parse('xml/Skills.xml').getroot()
SUBTYPES = et.parse('xml/Subtypes.xml').getroot()
MUTATIONS = et.parse('xml/Mutations.xml').getroot()

STAT_NAMES = ('Strength', 'Agility', 'Toughness', 'Intelligence', 'Willpower', 'Ego')
# these are not available from XML
IMPLANT_CODES = {'00': 'none',
                 '01': 'dermal insulation',
                 '04': 'optical bioscanner',
                 '05': 'optical technoscanner',
                 '06': 'night vision',
                 '07': 'hyper-elastic ankle tendons',
                 '08': 'parabolic muscular subroutine',
                 '09': 'translucent skin',
                 '11': 'stabilizer arm locks',
                 '12': 'rapid release finger flexors',
                 '13': 'carbide hand bones',
                 '14': 'pentaceps',
                 '15': 'inflatable axons',
                 # subtypes A-D, E-H, I-L
                 '16': ('nocturnal apex', 'cherubic visage', 'air current microsensor'),
                 }
# these are not available from XML
MOD_BONUSES = {'BE': [2, 0, 0, 0, 0, 0],  # Double-muscled
               'BK': [0, 0, -1, 0, 0, 0],  # Heightened Quickness
               'B2': [-1, 2, 0, 0, 0, 0],  # Triple-jointed
               'B4': [0, 0, 2, 0, 0, 0],  # Two-hearted
               'CD': [0, 0, 0, 0, 0, -1],  # Beak (D)
               '00': [0, 0, 1, 0, 0, 0],  # True Kin but no implant
               }


def read_gamedata() -> dict:
    """
    Read character code snippets and assorted data from Qud XML files. Implant codes not in XML.
    """
    # Read genotypes: currently, only two (mutated human and true kin)
    genotype_codes = {}
    for genotype in GENO:
        genotype_codes[genotype.attrib['Code'].upper()] = genotype.attrib['Name']

    # Read skill class names and real names
    # These are not returned, but used to parse the powers of subtypes, below.
    skill_names = {}
    for skill_cat in SKILLS:
        skill_names[skill_cat.attrib['Class']] = '(' + skill_cat.attrib['Name'] + ")"
        for power in skill_cat:
            skill_names[power.attrib['Class']] = power.attrib['Name']
    print(skill_names)

    class_bonuses = {}
    class_skills = {}
    caste_codes = {}

    # read True Kin Castes
    arcologies = SUBTYPES[0]
    for arcology in arcologies:
        for caste in arcology:
            caste_codes[caste.attrib['Code'].upper()] = caste.attrib['Name']
            stat_bonuses = [0, 0, 0, 0, 0, 0]
            for element in caste:
                if element.tag == 'stat' and (element.attrib['Name'] in STAT_NAMES):
                    bonus = int(element.attrib['Bonus'])
                    stat_bonuses[STAT_NAMES.index(element.attrib['Name'])] = bonus
            class_bonuses[caste.attrib['Name']] = stat_bonuses
            skills_raw = caste.find('skills')
            skills = []
            for skill in skills_raw:
                skills.append(skill_names[skill.attrib['Name']])
            class_skills[caste.attrib['Name']] = skills

    # read mutant Callings
    calling_codes = {}
    for calling in SUBTYPES[1]:
        calling_codes[calling.attrib['Code'].upper()] = calling.attrib['Name']
        stat_bonuses = [0, 0, 0, 0, 0, 0]
        for element in calling:
            if element.tag == 'stat' and (element.attrib['Name'] in STAT_NAMES):
                bonus = int(element.attrib['Bonus'])
                stat_bonuses[STAT_NAMES.index(element.attrib['Name'])] = bonus
        class_bonuses[calling.attrib['Name']] = stat_bonuses
        skills_raw = calling.find('skills')
        skills = []
        for skill in skills_raw:
            skills.append(skill_names[skill.attrib['Name']])
        class_skills[calling.attrib['Name']] = skills

    # read mutations
    mod_codes = {}
    for arcology in MUTATIONS:
        for mutation in arcology:
            mod_codes[mutation.attrib['Code'].upper()] = mutation.attrib['Name']
            # mark defects with '(D)' as in game
            if arcology.attrib['Name'] in ('PhysicalDefects', 'MentalDefects'):
                mod_codes[mutation.attrib['Code'].upper()] += ' (D)'
    # add implants to mutations
    mod_codes.update(IMPLANT_CODES)  # not in XML

    # some manual fixups
    mod_codes.pop('UU')
    for i in range(1, 5):
        mod_codes[f'U{i}'] = f'Unstable Genome ({i})'

    log.debug("Completed computing gamecodes.")
    return {'genotype_codes': genotype_codes,
            'caste_codes': caste_codes,
            'calling_codes': calling_codes,
            'mod_codes': mod_codes,
            'class_bonuses': class_bonuses,
            'class_skills': class_skills,
            'mod_bonuses': MOD_BONUSES,
            }


def decode(charcode: str, gamecodes: dict) -> Union[str, None]:
    """
    Take a Qud character build code of at least 8 characters and return a text description.
    """

    assert(len(charcode) >= 8)  # in Discord bot, this is caught by the regex
    try:
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

        # 3rd-8th characters are STR AGI TOU INT WIL EGO
        # such that A=6, ..., Z=31
        attrs = []
        for _ in charcode[2:8]:
            attrs.append(ord(_) - 59)
        charcode = charcode[8:]  # anything after this is mutations/implants, two chars each

        # after 8th character, characters come in pairs to give mutations or implants
        # for mutations, first character is category (A-E), second character is mutation from that
        # category (A-?)
        # AA for first mutation, AB for second; last mutation (Socially Repugnant) is EF
        # Exception: UU: unstable genotype - character can be U2 or U3 for multiple levels of UU!
        # these are chained together, e.g. BJQMMOEIBNBOBPBRDPED is mutations BN, BO, BP, BR, DP, ED
        # If the build is implant-capable instead of mutated, the character pairs are 00 for no
        # implants or 01-16 otherwise; implant 16 is determined by caste (true kin class).

        extensions = []  # implants or mutations
        if genotype == "True Kin":
            extname = "Implants:  "  # what we will call them
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

        # now we build the printable character sheet
        charsheet = f"""Genotype:  {genotype}
{class_called:11}{class_}"""
        attributes = ['Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:']
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
    except:  # something went wrong, most likely an invalid character code # noqa: E722
        log.exception(f"Exception while decoding character code {charcode}.")
        return None


if __name__ == '__main__':
    gamedata = read_gamedata()
    pprint.pprint(gamedata)
    while True:
        code = input("Enter code: ")
        print(decode(code, gamedata))
