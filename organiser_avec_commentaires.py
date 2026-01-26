#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour organiser la playlist M3U par catégories
avec des commentaires de section pour séparer les catégories
et un espacement correct entre les chaînes
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Fix encoding pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Trouver le fichier principal
playlist_file = None
for f in Path('.').glob('*.m3u'):
    if 'old' not in f.name.lower() and 'fusion' not in f.name.lower() and not f.name.endswith('.py'):
        playlist_file = f
        break

if not playlist_file:
    print("Erreur: Aucun fichier M3U principal trouvé!")
    exit(1)

print(f"Fichier principal: {playlist_file.name}")
print()

# Créer une sauvegarde
backup_file = f"{playlist_file.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(playlist_file, 'r', encoding='utf-8') as f:
    content = f.read()
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Sauvegarde créée: {backup_file}")
print()

# Fonction pour extraire les infos d'une ligne EXTINF
def parse_extinf(line):
    tvg_id = re.search(r'tvg-id="([^"]+)"', line)
    tvg_name = re.search(r'tvg-name="([^"]+)"', line)
    tvg_logo = re.search(r'tvg-logo="([^"]+)"', line)
    group_title = re.search(r'group-title="([^"]+)"', line)
    channel_name = line.split(',')[-1].strip() if ',' in line else ""
    
    return {
        'tvg_id': tvg_id.group(1) if tvg_id else "EPG N/A",
        'tvg_name': tvg_name.group(1) if tvg_name else "",
        'tvg_logo': tvg_logo.group(1) if tvg_logo else "",
        'group_title': group_title.group(1) if group_title else "",
        'channel_name': channel_name,
        'extinf_line': line
    }

# Lire le fichier
with open(playlist_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Parser toutes les chaînes
channels_by_category = defaultdict(list)
i = 0

while i < len(lines):
    line = lines[i].strip()
    
    # Ignorer les commentaires existants
    if line.startswith('# ') and not line.startswith('#EXT'):
        i += 1
        continue
    
    if line.startswith('#EXTINF'):
        extinf_info = parse_extinf(line)
        url = ""
        
        # Chercher l'URL sur la ligne suivante
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('#'):
                url = next_line
                i += 2
            else:
                i += 1
        else:
            i += 1
        
        if url:
            group_title = extinf_info['group_title']
            if group_title:
                channels_by_category[group_title].append({
                    'extinf': extinf_info['extinf_line'],
                    'url': url,
                    'channel_name': extinf_info['channel_name'] or extinf_info['tvg_name'] or ""
                })
    else:
        i += 1

print(f"Nombre de catégories trouvées: {len(channels_by_category)}")
print(f"Nombre total de chaînes: {sum(len(chs) for chs in channels_by_category.values())}")
print()

# Fonction pour obtenir le nom de section à partir du group-title
def get_section_name(group_title):
    # Extraire le code pays/région
    match = re.match(r'^([A-Z]{2,3})\s*\|\s*(.+)$', group_title)
    if match:
        code = match.group(1)
        name = match.group(2).strip()
        
        # Mapping des codes vers les noms complets
        code_map = {
            'CA': 'CANADA',
            'AF': 'AFRIQUE',
            'AR': 'MAGHREB',
            'FR': 'FRANCE',
            'US': 'ÉTATS-UNIS',
            'USA': 'ÉTATS-UNIS'
        }
        
        country_name = code_map.get(code, code)
        return f"{country_name} - {group_title}"
    
    # Si pas de format standard, utiliser le group-title tel quel
    return group_title

# Fonction pour trier les chaînes par nom
def sort_key(channel):
    name = channel['channel_name'].upper()
    # Enlever les accents et caractères spéciaux pour le tri
    name = name.replace('É', 'E').replace('È', 'E').replace('Ê', 'E')
    name = name.replace('À', 'A').replace('Â', 'A')
    name = name.replace('Î', 'I').replace('Ï', 'I')
    name = name.replace('Ô', 'O')
    name = name.replace('Ù', 'U').replace('Û', 'U')
    return name

# Trier les catégories (ordre de priorité)
category_order = [
    'CA| CANADA',
    'AF| AFRIQUE',
    'AF| DSTV AFRIQUE',
    'AR| ALGERIE',
    'AR| MAROC',
    'AR| TUNISIE',
    'FR| ACTUALITES',
    'FR| CANAL+ AFRIQUE',
    'FR| CINEMA',
    'FR| DOCUMENTAIRE',
    'FR| FRANCE',
    'FR| JEUNESSE',
    'FR| MUSIQUE',
    'FR| SPORTS',
    'US| SPORTS',
    'US| USA',
    'USA| NBA NFL NHL MLB'
]

# Créer la nouvelle playlist
new_playlist = ['#EXTM3U', '']

# Traiter les catégories dans l'ordre
processed_categories = set()
for cat in category_order:
    if cat in channels_by_category:
        processed_categories.add(cat)
        channels = sorted(channels_by_category[cat], key=sort_key)
        section_name = get_section_name(cat)
        
        new_playlist.append('# ============================================')
        new_playlist.append(f'# {section_name}')
        new_playlist.append('# ============================================')
        new_playlist.append('')
        
        for channel in channels:
            new_playlist.append(channel['extinf'])
            new_playlist.append(channel['url'])
            new_playlist.append('')  # Ligne vide après chaque chaîne

# Ajouter les catégories restantes (non listées dans category_order)
remaining_categories = sorted([cat for cat in channels_by_category.keys() if cat not in processed_categories])

for cat in remaining_categories:
    channels = sorted(channels_by_category[cat], key=sort_key)
    section_name = get_section_name(cat)
    
    new_playlist.append('# ============================================')
    new_playlist.append(f'# {section_name}')
    new_playlist.append('# ============================================')
    new_playlist.append('')
    
    for channel in channels:
        new_playlist.append(channel['extinf'])
        new_playlist.append(channel['url'])
        new_playlist.append('')  # Ligne vide après chaque chaîne

# Écrire le nouveau fichier
with open(playlist_file, 'w', encoding='utf-8', newline='\n') as f:
    content = '\n'.join(new_playlist)
    if not content.endswith('\n'):
        content += '\n'
    f.write(content)

print("Organisation terminée avec commentaires de section et espacement correct!")
print()
print("Résumé par catégorie:")
for cat in sorted(channels_by_category.keys()):
    count = len(channels_by_category[cat])
    print(f"  {cat}: {count} chaînes")
