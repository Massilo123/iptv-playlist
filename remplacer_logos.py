#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour remplacer les logos des chaînes de la playlist principale
par les logos des anciennes chaînes (old_channel.m3u) si elles correspondent
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Fix encoding pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Trouver les fichiers
old_channel_file = Path('old_channel.m3u')
playlist_file = None

for f in Path('.').glob('*.m3u'):
    if 'old' not in f.name.lower() and 'fusion' not in f.name.lower() and not f.name.endswith('.py'):
        playlist_file = f
        break

if not old_channel_file.exists():
    print("Erreur: Fichier old_channel.m3u non trouvé!")
    exit(1)

if not playlist_file:
    print("Erreur: Fichier playlist principal non trouvé!")
    exit(1)

print(f"Fichier old_channel: {old_channel_file.name}")
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
        'tvg_id': tvg_id.group(1) if tvg_id else "",
        'tvg_name': tvg_name.group(1) if tvg_name else "",
        'tvg_logo': tvg_logo.group(1) if tvg_logo else "",
        'group_title': group_title.group(1) if group_title else "",
        'channel_name': channel_name
    }

# Fonction pour normaliser les noms (pour la correspondance)
def normalize_name(name):
    if not name:
        return ""
    name = name.upper().strip()
    # Enlever les accents
    name = name.replace('É', 'E').replace('È', 'E').replace('Ê', 'E').replace('Ë', 'E')
    name = name.replace('À', 'A').replace('Â', 'A').replace('Ä', 'A')
    name = name.replace('Î', 'I').replace('Ï', 'I')
    name = name.replace('Ô', 'O').replace('Ö', 'O')
    name = name.replace('Ù', 'U').replace('Û', 'U').replace('Ü', 'U')
    name = name.replace('Ç', 'C')
    # Enlever les espaces multiples
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

# Fonction pour créer une clé de base (sans qualité mais avec numéros)
def get_base_key(name):
    """Extrait la clé de base d'une chaîne en enlevant les suffixes de qualité
    mais en gardant les numéros pour distinguer les chaînes numérotées"""
    if not name:
        return ""
    
    normalized = normalize_name(name)
    
    # Convertir les underscores en espaces
    normalized = normalized.replace('_', ' ')
    
    # Normaliser "SPORT" vs "SPORTS" 
    # "SPORTS" devient "SPORT" dans le contexte "BEIN SPORTS" (avec ou sans MAX après)
    # Mais on garde "SPORTS" dans d'autres contextes (ex: "SPORTS CENTER")
    normalized = re.sub(r'BEIN\s+SPORTS', 'BEIN SPORT', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'SPORTS\s+(\d)', r'SPORT \1', normalized)
    normalized = re.sub(r'SPORTS\s+MAX', 'SPORT MAX', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'SPORTS$', 'SPORT', normalized)
    
    # Normaliser "FullHD" et "FULLHD" en "FHD"
    normalized = re.sub(r'FULL\s*HD', 'FHD', normalized, flags=re.IGNORECASE)
    
    # Normaliser les numéros avec zéros (04 -> 4, mais garder 10, 20, etc.)
    # Gérer aussi les cas comme "MAX_04" ou "MAX 04"
    # Pattern pour trouver les numéros avec zéro initial (01-09)
    normalized = re.sub(r'0(\d)', r'\1', normalized)  # 01 -> 1, 02 -> 2, 04 -> 4, etc.
    # Mais ne pas transformer 10, 20, 30, etc. (déjà géré car pas de zéro initial)
    
    # Patterns de qualité à enlever (à la fin du nom)
    quality_patterns = [
        r'\s*HEVC\s*$',
        r'\s*FHD\s*$',
        r'\s*FULLHD\s*$',
        r'\s*HD\s*\+?\s*$',
        r'\s*SD\s*$',
        r'\s*UHD\s*$',
        r'\s*4K\s*$',
    ]
    
    base = normalized
    for pattern in quality_patterns:
        base = re.sub(pattern, '', base, flags=re.IGNORECASE)
    
    # Nettoyer les espaces multiples
    base = re.sub(r'\s+', ' ', base)
    base = base.strip()
    
    return base

# Fonction pour trouver une correspondance intelligente
def find_matching_channel(channel_name, old_channels_dict):
    """Trouve une correspondance dans old_channels en gérant les variations de qualité"""
    if not channel_name:
        return None
    
    # Essayer d'abord une correspondance exacte
    normalized = normalize_name(channel_name)
    if normalized in old_channels_dict:
        return old_channels_dict[normalized]
    
    # Essayer avec la clé de base (sans qualité)
    base_key = get_base_key(channel_name)
    if base_key in old_channels_dict:
        return old_channels_dict[base_key]
    
    # Chercher dans toutes les clés de old_channels
    # en comparant les clés de base
    for old_key, old_info in old_channels_dict.items():
        old_base = get_base_key(old_info['original_name'])
        if old_base == base_key and base_key:  # S'assurer que base_key n'est pas vide
            return old_info
    
    return None

# Lire old_channel.m3u et extraire les logos
print("Lecture de old_channel.m3u...")
old_channels = {}
with open(old_channel_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

i = 0
while i < len(lines):
    line = lines[i].strip()
    if line.startswith('#EXTINF'):
        info = parse_extinf(line)
        # Utiliser tvg-name ou channel_name comme clé
        key = info['tvg_name'] or info['channel_name']
        if key and info['tvg_logo']:
            # Stocker avec plusieurs clés pour faciliter la recherche
            normalized_key = normalize_name(key)
            base_key = get_base_key(key)
            
            # Stocker avec la clé normalisée
            old_channels[normalized_key] = {
                'logo': info['tvg_logo'],
                'original_name': key,
                'tvg_name': info['tvg_name'],
                'channel_name': info['channel_name']
            }
            
            # Stocker aussi avec la clé de base si différente
            if base_key and base_key != normalized_key:
                # Si la clé de base existe déjà, garder celle qui a le logo le plus spécifique
                if base_key not in old_channels or not old_channels[base_key].get('logo'):
                    old_channels[base_key] = {
                        'logo': info['tvg_logo'],
                        'original_name': key,
                        'tvg_name': info['tvg_name'],
                        'channel_name': info['channel_name']
                    }
    i += 1

print(f"  {len(old_channels)} chaînes trouvées dans old_channel.m3u")
print()

# Lire la playlist principale
print("Lecture de la playlist principale...")
with open(playlist_file, 'r', encoding='utf-8') as f:
    main_lines = f.readlines()

# Traiter la playlist principale
new_lines = []
replacements = 0
i = 0

while i < len(main_lines):
    line = main_lines[i]
    
    if line.strip().startswith('#EXTINF'):
        info = parse_extinf(line)
        key = info['tvg_name'] or info['channel_name']
        
        # Chercher une correspondance intelligente
        old_info = find_matching_channel(key, old_channels)
        
        if old_info:
            # Remplacer le logo dans la ligne EXTINF
            if info['tvg_logo']:
                # Remplacer l'ancien logo par le nouveau
                new_line = re.sub(
                    r'tvg-logo="[^"]*"',
                    f'tvg-logo="{old_info["logo"]}"',
                    line
                )
            else:
                # Ajouter le logo s'il n'existe pas
                # Trouver où insérer le logo (après tvg-name ou tvg-id)
                if 'tvg-name=' in line:
                    new_line = re.sub(
                        r'(tvg-name="[^"]*")',
                        f'\\1 tvg-logo="{old_info["logo"]}"',
                        line
                    )
                elif 'tvg-id=' in line:
                    new_line = re.sub(
                        r'(tvg-id="[^"]*")',
                        f'\\1 tvg-logo="{old_info["logo"]}"',
                        line
                    )
                else:
                    # Ajouter au début après #EXTINF
                    new_line = line.replace('#EXTINF:-1,', f'#EXTINF:-1, tvg-logo="{old_info["logo"]}"')
            
            new_lines.append(new_line)
            replacements += 1
            print(f"  [LOGO] {key} -> {old_info['logo']}")
        else:
            # Garder la ligne telle quelle
            new_lines.append(line)
    else:
        # Garder les autres lignes telles quelles
        new_lines.append(line)
    
    i += 1

# Écrire le nouveau fichier
with open(playlist_file, 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

print()
print("Remplacement terminé!")
print(f"  Logos remplacés: {replacements}")
