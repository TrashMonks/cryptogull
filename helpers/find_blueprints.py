"""Helper functions to find blueprints by name or display name."""
import asyncio
import concurrent.futures

from fuzzywuzzy import process
from hagadias.qudobject_props import QudObjectProps


def find_name_or_displayname(query: str, qindex: dict) -> QudObjectProps:
    """Try to return an exact match on an Object name or Object display name."""
    obj = None
    # check names
    for key, val in qindex.items():
        if query.lower() == key.lower():
            obj = val
            break
    if obj is None:
        # check display names
        for blueprint, qobject in qindex.items():
            if qobject.displayname.lower() == query.lower():
                obj = qobject
                break
    if obj is None:
        raise LookupError
    else:
        return obj


async def fuzzy_find_nearest(query: str, qindex: dict) -> QudObjectProps:
    """Try to return the nearest single match on any Object name or Object display name.

    Try using this if find_name_or_displayname fails.

    Doing a fuzzy match on qindex keys or display names can take about 2 seconds each, so
    run async in an executor so we can keep processing other bot commands in the meantime."""
    loop = asyncio.get_running_loop()
    # find nearest name
    names = [key for key, val in qindex.items()]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        search = loop.run_in_executor(pool, process.extractOne, query, names)
        nearest_name = await search
    # find nearest display name
    displayname_map = {}
    for qudobject in qindex.values():
        displayname_map[qudobject.displayname] = qudobject
    displaynames = [key for key, val in displayname_map.items()]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        search = loop.run_in_executor(pool, process.extractOne, query, displaynames)
        nearest_displayname = await search
    if nearest_name[1] > nearest_displayname[1]:  # compare by fuzzywuzzy's match score
        obj = qindex[nearest_name[0]]
    else:
        obj = displayname_map[nearest_displayname[0]]
    return obj
