"""Works out where a platform's ROMs belong on the device actually in use.

MinUI and its forks (NextUI) pick the emulator from the tag in parentheses at
the end of a ROM folder's name - "Sega 32X (32X)" is run by 32X.pak - and a
folder whose tag matches no installed emulator is hidden outright, games and
all. Which tags exist is a property of the device, not of this app: one card
calls its arcade emulator FBN, another may have MAME installed instead, and
EmuDrop was never written for this frontend in the first place.

A table baked into the app cannot know any of that, so the layout is read off
the device instead: which emulators are installed, and which ROM folders are
already there. The bundled systems mapping stays as the fallback for devices
where none of this applies (CrossMix, Stock, Knulli).
"""

import os
import re

from utils.logger import logger

# Tags to try for a platform, best first. Only aliases for the same hardware,
# plus a fallback to an emulator that genuinely covers the system: FinalBurn
# Neo runs Neo Geo, CPS and a large part of the classic arcade catalogue, so
# it is worth falling back to. It does not run NAOMI or Atomiswave, so those
# are left alone rather than sent somewhere that cannot load them.
PLATFORM_TAGS = {
    'SEGA32X': ('32X',),
    'MS': ('SMS',),
    'ATARI2600': ('A2600',),
    'ATARI5200': ('A5200',),
    'ATARI7800': ('A7800',),
    'AMIGA': ('PUAE',),
    'AMIGACD': ('PUAE',),
    'AMIGACDTV': ('PUAE',),
    'CPET': ('PET',),
    'CPLUS4': ('PLUS4',),
    'VIC20': ('VIC',),
    'POKEMINI': ('PKM',),
    'FBNEO': ('FBN',),
    'MSX2': ('MSX',),
    'COLSGM': ('COLECO',),
    'PCECD': ('PCE',),
    'GBA': ('GBA', 'MGBA'),
    'SFC': ('SFC', 'SUPA'),
    'SATELLAVIEW': ('SFC', 'SUPA'),
    'SUFAMI': ('SFC', 'SUPA'),
    # Deliberately absent: SuperGrafx, MSU-MD and the 64DD need core support
    # the usual paks do not have, so sending them to the neighbouring folder
    # would only turn 'invisible' into 'fails to launch'.
    # Arcade: prefer a dedicated pak, fall back to FinalBurn Neo.
    'MAME': ('MAME', 'MAME2003PLUS', 'MAME2010', 'FBN'),
    'MAME2003PLUS': ('MAME2003PLUS', 'MAME', 'MAME2010', 'FBN'),
    'MAME2010': ('MAME2010', 'MAME', 'MAME2003PLUS', 'FBN'),
    'NEOGEO': ('NEOGEO', 'FBN'),
    'NEOCD': ('NEOCD', 'FBN'),
    'CPS1': ('CPS1', 'FBN'),
    'CPS2': ('CPS2', 'FBN'),
    'CPS3': ('CPS3', 'FBN'),
    'PGM': ('PGM', 'FBN'),
}


def _tag_of(folder_name):
    """The (TAG) at the end of a MinUI style folder name."""
    match = re.search(r'\(([^)]+)\)\s*$', folder_name or '')
    return match.group(1) if match else None


class SystemLayout:
    """Reads the emulators and ROM folders present on the device."""

    def __init__(self):
        self._scanned = False
        self.root = None
        self.installed_tags = set()
        self.folders_by_tag = {}
        self._resolved = {}

    def _scan(self):
        if self._scanned:
            return
        self._scanned = True
        try:
            roms_dir = os.environ.get('ROMS_DIR', '')
            if not roms_dir or not os.path.isdir(roms_dir):
                return
            # ROMS_DIR points at <root>/Roms, so the card root is one level up.
            self.root = os.path.dirname(os.path.normpath(roms_dir))

            # Emulators: user installed under Emus/<device>/, shipped ones under
            # .system/<device>/paks/Emus/.
            for base in (os.path.join(self.root, 'Emus'),
                         os.path.join(self.root, '.system')):
                for pak in self._find_paks(base):
                    self.installed_tags.add(pak)

            # Existing ROM folders, so downloads join what is already there
            # instead of creating a second folder for the same system.
            for entry in sorted(os.listdir(roms_dir)):
                if not os.path.isdir(os.path.join(roms_dir, entry)):
                    continue
                tag = _tag_of(entry)
                if not tag:
                    continue
                current = self.folders_by_tag.get(tag)
                # Two folders can share a tag. Keep whichever already holds games.
                if current and self._has_files(os.path.join(roms_dir, current)):
                    continue
                self.folders_by_tag[tag] = entry

            if self.installed_tags:
                logger.info(f"Device layout: {len(self.installed_tags)} emulators installed, "
                            f"{len(self.folders_by_tag)} ROM folders present")
        except Exception as e:
            logger.warning(f"Could not read the device layout: {e}")

    @staticmethod
    def _find_paks(base):
        """Every <TAG>.pak under base, at any depth up to the Emus folders."""
        found = []
        if not os.path.isdir(base):
            return found
        for current, dirs, _ in os.walk(base):
            # Deep enough to reach .system/<device>/paks/Emus, no deeper.
            if current[len(base):].count(os.sep) >= 4:
                dirs[:] = []
                continue
            for name in dirs:
                if name.endswith('.pak'):
                    found.append(name[:-4])
        return found

    @staticmethod
    def _has_files(path):
        try:
            return any(not f.startswith('.') for f in os.listdir(path))
        except Exception:
            return False

    def folder_for(self, platform_id, default_folder):
        """ROM folder for a platform, as the device wants it named."""
        if platform_id in self._resolved:
            return self._resolved[platform_id]

        self._scan()
        result = default_folder
        try:
            if self.installed_tags:
                default_tag = _tag_of(default_folder)
                # Aliases first, the bundled tag last as the fallback.
                candidates = list(PLATFORM_TAGS.get(platform_id, ()))
                if default_tag and default_tag not in candidates:
                    candidates.append(default_tag)

                for tag in candidates:
                    if tag not in self.installed_tags:
                        continue
                    existing = self.folders_by_tag.get(tag)
                    if existing:
                        result = existing
                    elif tag == default_tag:
                        result = default_folder
                    else:
                        # No folder yet: keep the bundled display name, fix the tag.
                        display = re.sub(r'\s*\([^)]*\)\s*$', '', default_folder).strip()
                        result = f"{display} ({tag})" if display else f"{platform_id} ({tag})"
                    break

            if result != default_folder:
                logger.info(f"Platform {platform_id}: using '{result}' instead of '{default_folder}'")
        except Exception as e:
            logger.warning(f"Could not resolve the folder for {platform_id}: {e}")

        self._resolved[platform_id] = result
        return result


layout = SystemLayout()
