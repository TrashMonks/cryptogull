import xml.etree.ElementTree as et
import pprint
import logging
from typing import Union

logging.basicConfig(filename='bot.log', level=logging.INFO)


def read_gamedata() -> dict:
    """
    Read valid character code snippets and assorted data from Qud XML files. Implant codes not available from XML.
    """

    # These files need to be copied in from, e.g.,
    # SteamLibrary\SteamApps\common\Caves of Qud\CoQ_Data\StreamingAssets\Base
    xmlgeno = 'xml/Genotypes.xml'
    xmlskills = 'xml/Skills.xml'
    xmlsubtypes = 'xml/Subtypes.xml'
    xmlmutations = 'xml/Mutations.xml'

    genotypes = et.parse(xmlgeno).getroot()
    genotype_codes = {}
    for genotype in genotypes:
        genotype_codes[genotype.attrib['Code'].upper()] = genotype.attrib['Name']

    skills = et.parse(xmlskills).getroot()
    skill_names = {}  # read these before subtypes because subtypes reference skills
    for skill in skills:
        skill_names[skill.attrib['Class']] = '(' + skill.attrib['Name'] + ")"
        for power in skill:
            skill_names[power.attrib['Class']] = power.attrib['Name']

    stat_names = ('Strength', 'Agility', 'Toughness', 'Intelligence', 'Willpower', 'Ego')
    class_bonuses = {}
    class_skills = {}
    caste_codes = {}
    subtypes = et.parse(xmlsubtypes).getroot()
    categories = subtypes[0]
    for category in categories:
        for caste in category:
            caste_codes[caste.attrib['Code'].upper()] = caste.attrib['Name']
            stat_bonuses = [0, 0, 0, 0, 0, 0]
            for element in caste:
                if element.tag == 'stat' and (element.attrib['Name'] in stat_names):
                    stat_bonuses[stat_names.index(element.attrib['Name'])] = int(element.attrib['Bonus'])
            class_bonuses[caste.attrib['Name']] = stat_bonuses
            if 'Skills' in caste.attrib:
                skills = []
                rawskills = caste.attrib['Skills']
                for rawskill in rawskills.split(','):
                    skills.append(skill_names[rawskill])
                class_skills[caste.attrib['Name']] = skills

    calling_codes = {}
    for calling in subtypes[1]:
        calling_codes[calling.attrib['Code'].upper()] = calling.attrib['Name']
        stat_bonuses = [0, 0, 0, 0, 0, 0]
        for element in calling:
            if element.tag == 'stat' and (element.attrib['Name'] in stat_names):
                stat_bonuses[stat_names.index(element.attrib['Name'])] = int(element.attrib['Bonus'])
        class_bonuses[calling.attrib['Name']] = stat_bonuses
        if 'Skills' in calling.attrib:
            skills = []
            rawskills = calling.attrib['Skills']
            for rawskill in rawskills.split(','):
                skills.append(skill_names[rawskill])
            class_skills[calling.attrib['Name']] = skills

    mutations = et.parse(xmlmutations).getroot()
    mutation_codes = {}
    for category in mutations:
            for mutation in category:
                mutation_codes[mutation.attrib['Code'].upper()] = mutation.attrib['Name']
                # mark defects with '(D)' as in game
                if category.attrib['Name'] in ('PhysicalDefects', 'MentalDefects'):
                    mutation_codes[mutation.attrib['Code'].upper()] += ' (D)'
    # some manual fixups
    mutation_codes.pop('UU')
    for i in range(1, 5):
        mutation_codes[f'U{i}'] = f'Unstable Genome ({i})'

    # these are not available from XML
    implantcodes = {'01': 'dermal insulation',
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
                    '16': ('nocturnal apex', 'cherubic visage', 'air current microsensor')}  # subtypes A-D, E-H, I-L

    return {'genotype_codes': genotype_codes,
            'caste_codes': caste_codes,
            'calling_codes': calling_codes,
            'mutation_codes': mutation_codes,
            'implant_codes': implantcodes,
            'class_bonuses': class_bonuses,
            'class_skills': class_skills}


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

        # 3rd-8th characters are STR AGI TOU INT WIL EGO
        # such that A=6, ..., Z=31
        attrs = []
        for _ in charcode[2:8]:
            attrs.append(ord(_) - 59)
        class_attrs = gamecodes['class_bonuses'][class_]
        charcode = charcode[8:]  # anything after this is mutations/implants, two chars each

        # after 8th character, characters come in pairs to give mutations or implants
        # for mutations, first character is category (A-E), second character is mutation from that category (A-?)
        # AA for first mutation, AB for second; last mutation (Socially Repugnant) is EF
        # Exception: UU: unstable genotype - character can be U2 or U3 for multiple levels of UU!
        # these are chained together, e.g. BJQMMOEIBNBOBPBRDPED is mutations BN, BO, BP, BR, DP, ED
        # if the build is implant-capable instead of mutated, the character pairs are 00 for no implants
        # or 01-16 otherwise; implant 16 is determined by caste (true kin class).

        extensions = []  # implants or mutations
        if genotype == "True Kin":
            extname = "Implants:  "  # what we will call them
        else:
            extname = "Mutations: "
        while len(charcode) > 0:
            if genotype == "True Kin":
                if charcode[:2] == '16':  # the 16th implant changes depending on arcology of origin
                    if subtypecode in 'ABCD':
                        extensions.append(gamecodes['implant_codes']['16'][0])
                    if subtypecode in 'EFGH':
                        extensions.append(gamecodes['implant_codes']['16'][1])
                    if subtypecode in 'IJKL':
                        extensions.append(gamecodes['implant_codes']['16'][2])
                elif charcode[:2] == '00':  # player chose no implant
                    extensions.append('none')
                else:
                    extensions.append(gamecodes['implant_codes'][charcode[:2]])
            if genotype == "Mutated Human":
                extensions.append(gamecodes['mutation_codes'][charcode[:2]])
            charcode = charcode[2:]

        # skills are not in the build code, they're determined solely by class
        skills = [skill for skill in gamecodes['class_skills'][class_]]

        # now we build the printable character sheet
        charsheet = f"""Genotype:  {genotype}
{class_called:11}{class_}"""
        attributes = ['Strength:', 'Agility:', 'Toughness:', 'Intelligence:', 'Willpower:', 'Ego:']
        attr_strings = []
        for attr_text, attr, bonus in zip(attributes, attrs, class_attrs):
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
    except:  # something went wrong, most likely an invalid character code
        logging.exception(f"Exception while decoding character code {charcode}")
        return None


if __name__ == '__main__':
    gamedata = read_gamedata()
    pprint.pprint(gamedata)
    while True:
        code = input("Enter code: ")
        print(decode(code, gamedata))
