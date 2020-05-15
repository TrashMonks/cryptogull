"""
Pytest tests for qud_decode.py

Run qud_decode through a variety of character build codes to detect deadlocks,
exceptions, and other obvious regressions.
"""

from helpers.qud_decode import Character

# Test a variety of codes for crashes:
build_codes = ('AAPMNNJL16',
               'BARFIGHTBABE',
               'BJQMMOEIBNBOBPBRDPED',
               'BAIIMLLRB5CHDADCDDDX',
               'BCCGDEHEBKB2CDDB',
               'BAMMMMLLU5EB',
               'BINKMMKKBPBSB1B2CADP',
               )

# Stress test with every mutation and implant:
all_mods = 'BAEEEEEGAAABBABBBCB6BDBEBFBGBHBIBJBKBLBMBNBOBPBQBRBSBTBUBVBWBXBYBZB1B2B3B4B5CACBC'\
           'CCDCECFCGCHCICJCLDADBDCDDDEDFDGDHDIDJDKDLDMDNDODPDQDRDSDTDUDVDWDXDYDZD1EAEBECEDEE'\
           'EFEG0001040506070809111213141516U1U2U3U4'


def test_qud_decode():
    for code in build_codes:
        char = Character.from_charcode(code)
        assert len(char.make_sheet()) > 200
    char = Character.from_charcode(all_mods)
    assert len(char.make_sheet()) > 600
