"""One-off repair of wrong platform tags in the downloaded catalogue.

The catalogue is scraped from three ROM sites and shipped as a prebuilt SQLite
file, so a mis-filed game there sends the download into the wrong ROM folder
and the emulator will not touch it. Two wholesale mistakes are present:

  - every RomSpedia game tagged as NES is in fact a SNES game (that source has
    no SNES bucket at all, and 99% of its "NES" files are byte-identical
    filenames to SNES entries from the other two sources)
  - a few hundred HexRom rows contradict their own download URL, which names
    the system in its path

Both are repaired here rather than in the catalogue file itself, because
db_ota.sh replaces that file wholesale whenever upstream publishes a new one.
The work is guarded by PRAGMA user_version so it runs once per catalogue.
"""

import os
import re
import sqlite3
import urllib.parse
from collections import Counter, defaultdict

from utils.logger import logger

CATALOG_FIXUP_VERSION = 1

# Written from the platform names in the catalogue, deliberately not inferred
# from the rows being audited: a source that files every SNES game under NES
# looks perfectly self-consistent to a majority vote over its own data.
SLUG_TO_PLATFORM = {
    'nes': 'FC', 'nintendo-entertainment-system': 'FC', 'famicom': 'FC',
    'snes': 'SFC', 'super-nintendo': 'SFC', 'super-famicom': 'SFC',
    'super-nintendo-entertainment-system': 'SFC',
    'gb': 'GB', 'gameboy': 'GB', 'game-boy': 'GB',
    'gbc': 'GBC', 'game-boy-color': 'GBC', 'gameboy-color': 'GBC',
    'gba': 'GBA', 'game-boy-advance': 'GBA', 'gameboy-advance': 'GBA',
    'nds': 'NDS', 'nintendo-ds': 'NDS', 'n64': 'N64', 'nintendo-64': 'N64',
    'psp': 'PSP', 'playstation-portable': 'PSP',
    'ps1': 'PS', 'playstation': 'PS', 'psx': 'PS',
    'genesis': 'MD', 'sega-genesis': 'MD', 'mega-drive': 'MD', 'megadrive': 'MD',
    'master-system': 'MS', 'sega-master-system': 'MS',
    'game-gear': 'GG', 'sega-game-gear': 'GG',
    'dreamcast': 'DC', 'sega-dreamcast': 'DC',
    'saturn': 'SATURN', 'sega-saturn': 'SATURN',
    'sega-cd': 'SEGACD', '32x': 'SEGA32X', 'sega-32x': 'SEGA32X',
    'atari-2600': 'ATARI2600', 'atari-5200': 'ATARI5200', 'atari-7800': 'ATARI7800',
    'atari-st': 'ATARIST', 'lynx': 'LYNX', 'atari-lynx': 'LYNX',
    'wonderswan': 'WS', 'virtual-boy': 'VB',
    'neo-geo': 'NEOGEO', 'neo-geo-pocket': 'NGP',
    'pc-engine': 'PCE', 'turbografx-16': 'PCE',
    'commodore-64': 'C64', 'amstrad-cpc': 'CPC', 'msx': 'MSX',
    'zx-spectrum': 'ZXS', 'amiga': 'AMIGA',
    'colecovision': 'COLECO', 'intellivision': 'INTELLIVISION',
    '3do': 'PANASONIC', 'dos': 'DOS',
}

# A whole (source, platform) bucket is only moved on overwhelming agreement.
BUCKET_MIN_MATCHES = 20
BUCKET_MIN_AGREEMENT = 0.9


def _url_slug(game_url):
    """Platform named in a download URL, e.g. /rom/snes/ or _super-nintendo_he."""
    match = re.search(r'/rom/([a-z0-9\-]+)/', game_url or '')
    if match:
        return match.group(1)
    match = re.search(r'_([a-z0-9\-]+)_he', game_url or '')
    return match.group(1) if match else None


def _image_slug(image_url):
    """Platform named in a thumbnail, e.g. mario-world-snes-thumb.jpg."""
    match = re.search(r'/thumbs/(.+?)-thumb\.jpg', image_url or '')
    if not match:
        return None
    parts = match.group(1).split('-')
    for length in (4, 3, 2, 1):
        candidate = '-'.join(parts[-length:])
        if candidate in SLUG_TO_PLATFORM:
            return candidate
    return None


def _rom_filename(game_url):
    """Filename the URL points at, comparable across sources."""
    name = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(game_url or '').path))
    return re.sub(r'\[hexrom\.com\]', '', name, flags=re.I).strip().lower()


def _platform_from_evidence(row):
    """Platform the row's own URLs claim, or None when they say nothing."""
    for slug in (_url_slug(row['game_url']), _image_slug(row['image_url'])):
        if slug and slug in SLUG_TO_PLATFORM:
            return SLUG_TO_PLATFORM[slug]
    return None


def repair(db_path):
    """Fix platform tags in place. Returns the number of rows changed."""
    try:
        if not os.path.exists(db_path):
            return 0

        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        try:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if version >= CATALOG_FIXUP_VERSION:
                return 0

            rows = connection.execute(
                """SELECT g.id, g.platform_id, g.image_url, g.game_url, s.source_name
                   FROM games g JOIN sources s ON s.id = g.source_id"""
            ).fetchall()

            corrections = {}

            # 1. Rows whose own URL contradicts their tag.
            by_filename = defaultdict(list)
            for row in rows:
                claimed = _platform_from_evidence(row)
                if claimed and claimed != row['platform_id']:
                    corrections[row['id']] = claimed
                by_filename[_rom_filename(row['game_url'])].append(row)

            # 2. Buckets with no per-row evidence, judged against the same ROM
            #    file listed by another source.
            #
            #    Only rows whose own URL names a system may vote. Letting an
            #    untagged row vote its bare platform_id lets a mis-filed source
            #    outvote a correct one: an earlier version of this pass moved
            #    every ConsoleRoms SNES game into NES on the strength of the
            #    RomSpedia rows that are themselves the bug being fixed.
            votes = defaultdict(Counter)
            for row in rows:
                if _platform_from_evidence(row):
                    continue
                same_file = by_filename.get(_rom_filename(row['game_url']), ())
                for other in same_file:
                    if other['source_name'] == row['source_name']:
                        continue
                    other_platform = _platform_from_evidence(other)
                    if other_platform:
                        votes[(row['source_name'], row['platform_id'])][other_platform] += 1

            moved_buckets = {}
            for bucket, counter in votes.items():
                total = sum(counter.values())
                winner, count = counter.most_common(1)[0]
                if (winner != bucket[1] and total >= BUCKET_MIN_MATCHES
                        and count / total >= BUCKET_MIN_AGREEMENT):
                    moved_buckets[bucket] = winner

            for row in rows:
                target = moved_buckets.get((row['source_name'], row['platform_id']))
                if target and row['id'] not in corrections:
                    corrections[row['id']] = target

            if not corrections:
                connection.execute(f'PRAGMA user_version = {CATALOG_FIXUP_VERSION}')
                connection.commit()
                return 0

            connection.executemany(
                'UPDATE games SET platform_id = ? WHERE id = ?',
                [(platform, game_id) for game_id, platform in corrections.items()]
            )
            connection.execute(f'PRAGMA user_version = {CATALOG_FIXUP_VERSION}')
            connection.commit()

            for bucket, target in sorted(moved_buckets.items()):
                logger.info(f"Catalogue repair: all {bucket[0]} '{bucket[1]}' games re-tagged as '{target}'")
            logger.info(f"Catalogue repair: corrected the platform of {len(corrections)} games")
            return len(corrections)
        finally:
            connection.close()
    except Exception as e:
        # A read-only card or a locked file must not stop the app starting.
        logger.warning(f"Catalogue repair skipped: {e}")
        return 0
