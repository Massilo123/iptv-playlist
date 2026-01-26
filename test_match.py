#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

def normalize_name(name):
    if not name:
        return ""
    name = name.upper().strip()
    name = name.replace('É', 'E').replace('È', 'E').replace('Ê', 'E').replace('Ë', 'E')
    name = name.replace('À', 'A').replace('Â', 'A').replace('Ä', 'A')
    name = name.replace('Î', 'I').replace('Ï', 'I')
    name = name.replace('Ô', 'O').replace('Ö', 'O')
    name = name.replace('Ù', 'U').replace('Û', 'U').replace('Ü', 'U')
    name = name.replace('Ç', 'C')
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def get_base_key(name):
    if not name:
        return ""
    normalized = normalize_name(name)
    normalized = normalized.replace('_', ' ')
    normalized = re.sub(r'BEIN\s+SPORTS', 'BEIN SPORT', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'SPORTS\s+(\d)', r'SPORT \1', normalized)
    normalized = re.sub(r'SPORTS\s+MAX', 'SPORT MAX', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'SPORTS$', 'SPORT', normalized)
    normalized = re.sub(r'FULL\s*HD', 'FHD', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'0(\d)', r'\1', normalized)
    quality_patterns = [
        r'\s*HEVC\s*$',
        r'\s*FHD\s*$',
        r'\s*FULLHD\s*$',
        r'\s*HD\s*\+?\s*$',
        r'\s*SD\s*$',
    ]
    for pattern in quality_patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

# Test
name1 = "BEIN_SPORT_MAX_04"
name2 = "BeIN Sports Max 4 FHD"
name3 = "beIN Sports Max 4 HD"

key1 = get_base_key(name1)
key2 = get_base_key(name2)
key3 = get_base_key(name3)

print(f"'{name1}' -> '{key1}'")
print(f"'{name2}' -> '{key2}'")
print(f"'{name3}' -> '{key3}'")
print(f"Match 1-2: {key1 == key2}")
print(f"Match 1-3: {key1 == key3}")
