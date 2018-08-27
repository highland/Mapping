# -*- coding: utf-8 -*-
"""Functions to extract data from the OSM database.

Author: Mark Thomas
"""
from pprint import pprint

from typing import Sequence, List, Tuple

import requests
from bs4 import BeautifulSoup

# Type aliases
XML = str
Tags = str
Keys = List[Tags]
House_info = List[Tuple[str]]

soup: BeautifulSoup = None

def _get_raw_data() -> XML:
    newtonmore = {'bbox': '-4.1386,57.0572,-4.0877,57.0729'}
    osm = 'https://api.openstreetmap.org/api/0.6/map'
    return requests.get(osm, newtonmore).text


def _clean(seq: Sequence) -> List:
    alist = list(set(seq))
    alist.sort()
    return alist


def extract_house_info(keys: Keys) -> House_info:
    """Get House names plus additional data.

    Args:
        keys: The required extra tags (k = ... in OSM XML)

    Returns:
        The requested data
    """
    global soup
    if not soup:
        data = _get_raw_data()
        soup = BeautifulSoup(data, 'xml')
    house_list = []
    for tag in soup.find_all('tag'):
        if tag.get('k') == 'addr:housename':
            info = []
            info.append(tag.get('v'))
            house = tag.parent
            for data in house.find_all('tag'):
                key = data.get('k')
                if key in keys:
                    info.append(data.get('v'))
            house_list.append(tuple(info))
    return _clean(house_list)


def get_house_names() -> List[str]:
    """Get house names.

    Returns:
        All the house names in the bounding block.
    """
    global soup
    if not soup:
        data = _get_raw_data()
        soup = BeautifulSoup(data, 'xml')
    return _clean([tag.get('v')
                   for tag in soup.find_all('tag')
                   if tag.get('k') == 'addr:housename'])


def get_previous_names() -> List[Tuple[str,str]]:
    """Get old house names.

    Returns:
        Tuples of (new name, old name).
    """
    global soup
    if not soup:
        data = _get_raw_data()
        soup = BeautifulSoup(data, 'xml')
    replacement_list = []
    for tag in soup.find_all('tag'):
        if tag.get('k') == 'addr:previousname':
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
    print('Name, Street, Postcode for first 10 houses:')
    pprint(houses[:10])
    
    print(f'{len(houses)} houses found' )

    print('House names that have changed:')
    pprint(get_previous_names())

if __name__ == '__main__':
    _main()
