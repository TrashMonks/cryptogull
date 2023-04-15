"""Tests for the random tile generation used in the horoscope cog."""
import os
import pytest

from bot.helpers.tiles import get_tile_data, get_random_tile_name

# is this test running in a CI environment? (GitHub Workflows)
CI = os.environ.get('CI') in ('True', 'true')


@pytest.mark.skipif(CI, reason="Skipping due to no textures")
@pytest.mark.asyncio
async def test_random_tile():
    """Exercise the random tile selection.

    Skipped in integration tests due to textures not being present."""
    for i in range(100):
        name, args = get_random_tile_name()
        msg, filedata, filename = await get_tile_data(name, *args)
