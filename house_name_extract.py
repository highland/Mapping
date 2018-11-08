# -*- coding: utf-8 -*-
"""Functions to extract data from the OSM database.

Author: Mark Thomas
"""
from pprint import pprint

from typing import Sequence, List, Tuple, Dict

import requests
from bs4 import BeautifulSoup
from OSGridConverter import latlong2grid
from shapely.geometry.polygon import Polygon

# Type aliases
XML = str
Tags = str
Keys = List[Tags]
HouseInfo = List[Tuple[str]]
Eastings = int
Northings = int
Coords = Tuple[Eastings, Northings]


def _get_raw_data() -> XML:
    newtonmore = {'bbox': '-4.1516,57.0421,-4.0918,57.0772'}
    osm = 'https://api.openstreetmap.org/api/0.6/map'
    return requests.get(osm, newtonmore).text


soup: BeautifulSoup = BeautifulSoup(_get_raw_data(), 'xml')

all_corners: Dict[str, Coords] = {}


def _get_corners():
    """
    Populate the Global Dictionary, all_corners, with the coordinates
    of all the nodes in the data set.
    """
    if not all_corners:
        for tag in soup.find_all('node'):
            ref = tag.get('id')
            lat = float(tag.get('lat'))
            lon = float(tag.get('lon'))
            grid = latlong2grid(lat, lon)
            all_corners[ref] = grid.E, grid.N


def _clean(seq: Sequence) -> List:
    """
    Remove duplicates and sort
    """
    alist = list(set(seq))
    alist.sort()
    return alist


def extract_house_info(keys: Keys) -> HouseInfo:
    """
    Get House names plus additional data.

    Args:
        keys: The required extra tags (k = ... in OSM XML)

    Returns:
        The requested data
    """
    _get_corners()
    house_list: HouseInfo = []
    for tag in soup.find_all('tag'):
        if tag.get('k') == 'addr:housename':
            info = []
            info.append(tag.get('v'))
            house = tag.parent
            for data in house.find_all('tag'):
                key = data.get('k')
                if key in keys:
                    info.append(data.get('v'))
            corners: List[Coords] = []
            for place in house.find_all('nd'):
                ref = place.get('ref')
                corners.append(all_corners.get(ref))
            if len(corners) >= 3:
                point = Polygon(corners).centroid
                info.append(int(point.x))
                info.append(int(point.y))
            house_list.append(tuple(info))
    return _clean(house_list)


# def meters_distance(house1: Point, house2: Point) -> int:
#    return int(sqrt((house1.E - house2.E)**2 + (house1.N - house2.N)**2))
# now just 'house1.distance(house2)'

def get_house_names() -> List[str]:
    """Get house names.

    Returns:
        All the house names in the bounding block.
    """
    return _clean([tag.get('v')
                   for tag in soup.find_all('tag')
                   if tag.get('k') == 'addr:housename'])


def get_previous_names() -> List[Tuple[str, str]]:
    """Get old house names.

    Returns:
        Tuples of (new name, old name).
    """
    replacement_list = []
    for tag in soup.find_all('tag'):
        if tag.get('k') == 'old_name':
            old_name = tag.get('v')
            house = tag.parent
            data = house.tag
            for data in house.find_all('tag'):
                key = data.get('k')
                if key == 'addr:housename':
                    new_name = data.get('v')
                    replacement_list.append((old_name, new_name))
                    break
    return _clean(replacement_list)


def _main():
    print('First 10 house names:')
    pprint(get_house_names()[:10])

    houses = extract_house_info(['addr:street', 'addr:postcode'])
    print('Name, Postcode, Street, Eastings, Northings for first 10 houses:')
    pprint(houses[:10])
    count = 0
    with open('houses.csv', 'w') as outfile:
        outfile.write('Name,Postcode,Road,OSE,OSN\n')   # csv header
        for house in houses:
            if len(house) == 5:
                name, postcode, road, os_eastings, os_northings = house
                outfile.write(
                    f'{name},{postcode},{road},{os_eastings},{os_northings}\n')
                count += 1
    print(f'{count} houses found')

    print('House names that have changed:')
    pprint(get_previous_names())


def _main1():
    from collections import Counter
    tags = Counter()
    for tag in soup.find_all('tag'):
        tags[tag.get('k')] += 1
    pprint(tags.most_common())


if __name__ == '__main__':
    _main()
