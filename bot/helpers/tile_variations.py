import random
from typing import Tuple


def parse_variation_parameters(query: str) -> Tuple[str, str]:
    """Parses 'variation' and parameters from a query string. Returns the remaining query string
    as well as the variation value.

    Args:
        query: The query string to parse.
    """
    # main 'variation' use case (ex: ?tile flowers variation 3)
    if 'variation' in query:
        query, variation = [q.strip() for q in query.split('variation', maxsplit=1)]
        if variation == '':
            variation = 'random'
    # support a simplified 'unidentified' query (ex: ?tile hypertractor unidentified)
    elif query.endswith(' unidentified'):
        query = query[:-13]
        variation = 'unidentified'
    else:
        variation = ''
    return query, variation


def get_tile_variation_details(obj, variation: str) -> dict:
    """Attempts to retrieve an alternate tile for the QudObject, or returns an error message.

    Args:
        obj: QudObject for which to attempt to get the tile variation
        variation: variation string parameter. Empty string or 'random' for a random variation.
                   Number to get the variation with that numeric index. Other word to try and
                   search for a variation by its variation name.

    Returns: A dictionary with the following keys:
       err: None, or an error message to show in the client if the variation could not be retrieved
       tile: the variation QudTile, if one was successfully retrieved
       idx: the variation tile index, if one was successfully retrieved
       name: the variation name, if one was successfully retrieved
    """
    err = None
    tile = None
    idx = None
    name = None
    num_tiles = obj.number_of_tiles()
    if num_tiles > 1:
        obj_tiles, obj_tiles_metadata = obj.tiles_and_metadata()

        if variation[0] == '#' and variation[1:].isdigit():
            variation = variation[1:]
        elif variation.lower() == 'random':
            variation = str(random.randrange(num_tiles) + 1)

        if variation.isdigit():
            i = int(variation)
            if i == 0:
                err = 'You must specify a variation number greater than 0.'
            elif i <= len(obj_tiles):
                tile = obj_tiles[i - 1]
                idx = i
                name = obj_tiles_metadata[i - 1].type
            else:
                err = f'Sorry, `{obj.name}` doesn\'t have {variation} alternate tiles.'
        elif any(variation.lower() in m.type.lower() for m in obj_tiles_metadata):
            i = 0
            for t, m in zip(obj_tiles, obj_tiles_metadata):
                i += 1
                if variation.lower() in m.type.lower():
                    tile = t
                    idx = i
                    name = m.type
                    break
        else:
            err = f'Sorry, `{obj.name}` has no alternate tile called "{variation}".'
    else:
        err = f'Sorry, `{obj.name}` does not have any alternate tiles.'
    return {'err': err, 'tile': tile, 'idx': idx, 'name': name}
