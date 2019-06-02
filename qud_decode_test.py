"""Tests for qud_decode.py

Run qud_decode through a variety of character build codes to detect deadlocks,
exceptions, and other obvious regressions."""

from qud_decode import read_gamedata, decode

gamedata = read_gamedata()

build_codes = ('AAPMNNJL16',
               'BARFIGHTBABE',
               'BJQMMOEIBNBOBPBRDPED',
               'BAIIMLLRB5CHDADCDDDX',
               'BCCGDEHEBKB2CDDB',
               )

all_mods = ('BAEEEEEGAAABBABBBCB6BDBEBFBGBHBIBJBKBLBMBNBOBPBQBRBSBTBUBVBWBXBYBZB1B2B3B4B5CACBC'
            'CCDCECFCGCHCICJCLDADBDCDDDEDFDGDHDIDJDKDLDMDNDODPDQDRDSDTDUDVDWDXDYDZD1EAEBECEDEE'
            'EFEG0001040506070809111213141516U1U2U3U4',
            )


def test_qud_decode():
    for code in build_codes:
        assert len(decode(code, gamedata)) > 200
    for code in all_mods:
        assert len(decode(code, gamedata)) > 600
