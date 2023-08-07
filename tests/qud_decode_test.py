"""Tests for the newstyle character code decoder."""
import base64
import gzip
import json

import pytest

from bot.helpers.qud_decode import Character

# Test cases are lists in this format:
# [
#     build code,
#     [expected attributes in game order],
#     [expected bonuses in game order]
# ]

# game order is Strength, Agility, Toughness, Intelligence, Willpower, Ego

CASES = [
    [
        "H4sIAAAAAAAAA81WXW/aMBR9r9T/YEV7DIgiNnWVeGDpNra1EmtoO2nqg5PcJV4d2/LHKob477MNhSSsg05qBBIKvud+HO49ufL8+AihIMcl/AKpCGfBGQr63V633xt0X58GoccTQ2hWcTixDr0VVvLMUFDW/N2dEZovH2toOhPggr5dXXSjAkucapDvXEbV/Woy9/0IjGvrdukDQjRSCsqEzjpRbANEiG6WtYcbZiGKDNVGwpCB0RLTEE1MQkn6BWZTfg9syAylS46eTIY1tjTW7KzplX4utXObZIvepojN+ejv0l4ajTVkaGxKzGpeW718xBbLH4vwv3sZm+RAW1ljtruTK3eXNE4LTrFsq4V+bja3OsAmNrjtbmMpbMZe1aKAQupzbF7a5WdePaCVgFdNjgpSgsTV3N4n4oZp63DSBG6wJNhDvSqyCPetOOb8XqEfXKIPALrFwtMH3hkDziBrs6gkgkLnJydMt1r4nFudQqc0KqWtFr5mSmNbGrmdWcKTlfv7Vt4c7lraFCOtJUmMhkNcFU1yu3fFxIlPTYxMC6ysFs7q8wtGOaFEz6z9bW0mwfucW+ObuvGTFTKlJAeWOqqndTTWEliui+24KTd5wUCp7aBbQqngDyBd1Aapai7AIhbg1dEZDOrAFZSYMMLy5kpM7N8duUVZj3hB5URGaV6S37DGD1BBT5HcrSRmb5R+h2OWzVBMTV6DBbj5OJJVq1VK5kfbBITkzC6D+K9RLzmkgnMFscZSW9Fc8NTvrkMc1D+I7nHTasS5Yp+5EPh5Fy73uDs+WvwB4vrnYFQMAAA=",  # noqa E501
        [16, 19, 18, 18, 16, 16],  # attributes
        [2, 2, 0, 2, 0, 0],        # bonuses
    ],
    [
        "H4sIAAAAAAAAA81W22rbQBB9D+QfFtFHxTjBbdOAHxQl9JIE3MikhZKHlTSVl6x2xV5SVON/76zk2JKc1ElLhA1G1pyZM8dzWXa+v0eIl9Ec7kFpJoV3QryjwXBwNBwN3h57foXHlvG04XCIDsMllsvUctBo/uHeCZnXjxU0LQtwQd+vLwfhjCqaGFCnjlEPvtrUfT+CkAbdrqoAnwRaQx7z8iCMMKDwyU2de7xW5pPQcmMVjAVYoyj3ycTGnCUXUE7lHYixsJzXGisxKTUUZazUoemNeam0MyTZkLdOgpwP/o72yhpqICWfbE5Fy2ujlg/Yov6x8P+5lpGNd7SULWXbK7l0d6QTxjPF8r5KWPUNufUOFrGjbXsZ8wIZh02LBg5JxbFe2vozb76Q5QAvi3zughRLKCc446BqwO9EhNIKg+6HXeCGKkYraNhEFv5z859ChoVgIusx51QKlpCAc1BZ2WPeM5kz0XeBQ06ZupclFQn8f9r1y21PWxsYHM/YGtjFte2K2763E8mE0ROrkhnVkLZzIh5kuA2mRPv7Vk+880yi8UPb+FkY4Jxl4Jp7Qt610cgoEJmZbZJNpc1mArQ7Ko7b0DfGeSF/gXJ8a6Q5cB4togKq6TgYjdrANeSUCbfPneMpxr8buEOrHfGKkxNabXDjfsMK38EJekrk9kkSeLtz5Bf05x1tIQW41jh9TSsOSVp1tQsUSgo8B6JHo16zPzMpNUSGKoPzcimT6szaxR79RegzLjydOJfsiywK+rJ7j3vc7u8t/gCu1vr52wsAAA==",  # noqa E501
        [17, 17, 18, 16, 16, 19],  # attributes
        [0, 0, 0, 0, 2, 0],  # bonuses
    ],
]


@pytest.mark.parametrize("test_input,expected_attrs,_", CASES)
def test_decode_attributes(test_input, expected_attrs, _):
    """Check the decoded attributes against the expected attributes."""
    decode = base64.b64decode(test_input)
    unzip = gzip.decompress(decode).decode(encoding='utf-8')
    code = json.loads(unzip)
    char = Character(code)
    assert char.attributes == expected_attrs


@pytest.mark.parametrize("test_input,_,expected_bonuses", CASES)
def test_decode_bonuses(test_input, _, expected_bonuses):
    """Check the decoded bonuses against the expected bonuses."""
    decode = base64.b64decode(test_input)
    unzip = gzip.decompress(decode).decode(encoding='utf-8')
    code = json.loads(unzip)
    char = Character(code)
    assert char.bonuses == expected_bonuses


@pytest.mark.parametrize("test_input,_,__", CASES)
def test_decode_make_sheet(test_input, _, __):
    """Check that a text sheet can be rendered from each character code."""
    decode = base64.b64decode(test_input)
    unzip = gzip.decompress(decode).decode(encoding='utf-8')
    code = json.loads(unzip)
    char = Character(code)
    sheet = char.make_sheet()
    assert len(sheet) > 100
