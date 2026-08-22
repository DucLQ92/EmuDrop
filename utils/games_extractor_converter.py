import os
import subprocess
import zipfile
from utils.logger import logger
from utils.config import Config
import shutil
import re

class GamesExtractorConverter:
    def __init__(self, status, game_prop, download_path) -> None:
        self.platform_id = game_prop.platform_id
        self.download_path = download_path
        roms_base = os.environ.get('ROMS_DIR', '/mnt/SDCARD/Roms/')
        system_folder = Config.SYSTEMS_MAPPING.get(game_prop.platform_id, game_prop.platform_id)
        self.rom_path = os.path.join(roms_base, system_folder)
        self.isExtractable = game_prop.isExtractable
        self.canBeRenamed = game_prop.canBeRenamed
        self.game_name = game_prop.name
        self.process = None
        self.callback = None        # Callback function for progress updates
        self.status = status
        self.cancelled = False
    
    def _run_command(self, cmd, operation_name="", status_key=None):
        """Run a command and update progress information.
        
        Args:
            cmd: Command to execute as list of arguments
            operation_name: Name of the operation, used in logs and error text
            status_key: Translation key shown in the UI while the command runs
            
        Returns:
            tuple: (success, error_message)
            
        Raises:
            RuntimeError: If the command fails to execute
        """
        if self.cancelled:
            raise RuntimeError("Operation cancelled")
            
        self.status['current_operation'] = status_key or operation_name
        try:
            shell = False
            # if windows remove ./ and set shell to True
            if os.name == 'nt':
                cmd[0] = cmd[0].replace('./', '')
                shell = True
                
            exec_dir = os.environ.get('EXECUTABLES_DIR', os.path.join(Config.BASE_DIR, 'assets', 'executables'))
            exec_bin = os.path.join(exec_dir, cmd[0].replace('./', ''))
            if os.path.exists(exec_bin) and not os.access(exec_bin, os.X_OK):
                try:
                    os.chmod(exec_bin, 0o755)
                except Exception:
                    pass
                    
            process = subprocess.Popen(
                cmd,
                cwd=exec_dir if os.path.exists(exec_dir) else None,
                start_new_session=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=shell
            )
            self.process = process
            
            stdout, stderr = process.communicate()
            
            if self.cancelled:
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                raise RuntimeError("Operation cancelled")
            
            if process.returncode != 0:
                error_msg = f"{operation_name}: Command failed with return code {process.returncode}"
                if stderr:
                    error_msg += f"\n{stderr}"
                if stdout:
                    error_msg += f"\n{stdout}"
                return False, error_msg
                
            return True, stdout
            
        except Exception as e:
            if self.cancelled:
                raise RuntimeError("Operation cancelled")
            return False, str(e)
        finally:
            self.process = None
        
    def cancel(self):
        """Cancel the current operation"""
        self.cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
    
    def _trim_file_name(self, input_file):
        # This removes things like .img.iso.zip etc
        file_name = re.sub(r'(\.[a-zA-Z0-9]+)+$', '', input_file)
        return file_name
        
    def move_game(self):
        files_path, files = self.scan_folder(self.download_path)
        output_path = os.path.join(files_path, "output")
        os.makedirs(output_path, exist_ok=True)

        game_names_to_scrape = []
        valid_files = [f for f in files if not f.endswith(('.nfo', '.html', '.htm'))]
           
        def _normal_game_out():
            # Take what is on disk now, not the archive's original listing. The
            # conversion steps write their results into files_path, and moving
            # the original names instead shipped the raw .ecm to the ROM folder
            # while the decoded .bin sat next to it, unused.
            current = sorted(
                f for f in os.listdir(files_path)
                if os.path.isfile(os.path.join(files_path, f))
                and not f.endswith(('.nfo', '.html', '.htm'))
            )
            
            # An .ecm is an intermediate. Drop it once its decoded form exists;
            # no emulator reads .ecm, so shipping one is never the right answer.
            decoded = {
                self._trim_file_name(f) for f in current
                if not f.lower().endswith('.ecm')
            }
            out_files = [
                f for f in current
                if not (f.lower().endswith('.ecm') and self._trim_file_name(f) in decoded)
            ] or current
            
            for file in out_files:
                game_name = self._trim_file_name(file)
                
                # temp commented
                # if rename and self.canBeRenamed:
                #     game_name = os.path.splitext(self.game_name)[0]
                
                _, ext = os.path.splitext(file)
                dest_file = f"{game_name}{ext}"
                os.replace(os.path.join(files_path, file), os.path.join(output_path, dest_file))
                game_names_to_scrape.append(dest_file)

        def _convert_file(input_file, converter_type):
            game_name = self._trim_file_name(input_file)
            
            conversion_commands = {
                'chd': [
                    "./chdman",
                    "createcd",
                    "-i", os.path.join(files_path, input_file),
                    "-o", os.path.join(output_path, f"{game_name}.chd"),
                    "-c", "zlib"
                ],
                'cue': [
                    "./ccd2cue",
                    os.path.join(files_path, input_file),
                    "-o", os.path.join(files_path, f"{game_name}.cue")
                ],
                'bin': [
                    "./ecm2bin",
                    os.path.join(files_path, input_file),
                    os.path.join(files_path, f"{game_name}.bin")
                ]
            }
            
            if converter_type in conversion_commands:
                operation_name = f"Converting to {converter_type.upper()}"
                logger.info(f"{operation_name}: {input_file}")
                success, result = self._run_command(
                    conversion_commands[converter_type],
                    operation_name,
                    status_key=f"op_converting_{converter_type}"
                )
                
                if not success:
                    raise RuntimeError(result)
                    
                if converter_type == 'chd':
                    game_names_to_scrape.append(f"{game_name}.chd")
                    logger.info(f"File {input_file} has been converted to CHD successfully")

        # Platforms requiring CHD conversion
        to_chd_platforms = ['SEGACD', 'DC', 'PANASONIC', 'PS', 'NAOMI', 'PCFX', 'PCECD', 'SATURN']
        if self.platform_id in to_chd_platforms:
            # Group files by extension for batch processing
            file_groups = {
                'bin': [f for f in files if f.lower().endswith('.bin')],
                'img': [f for f in files if f.lower().endswith('.img')],
                'ecm': [f for f in files if f.lower().endswith('.ecm')],
                'ccd': [f for f in files if f.lower().endswith('.ccd')],
                'cue': [f for f in files if f.lower().endswith('.cue')],
            }
            
            # Process each group of files
            for ext, conv_files in file_groups.items():
                for file in conv_files:
                    if ext == 'ccd':
                        _convert_file(file, 'cue')
                    elif ext == 'ecm':
                        _convert_file(file, 'bin')
                    elif ext == 'cue':
                        input_file_path = os.path.join(files_path, file)
                        output_file_path = os.path.join(files_path, f"{self._trim_file_name(file)}.cue")
                        with open(input_file_path, 'r') as f:
                            content = f.readlines()
                        
                        bin_name_line = content[0].split('"')
                        bin_name_line[1] = f"{self._trim_file_name(file)}.bin"
                        content[0] = '"'.join(bin_name_line)
                        
                        os.remove(input_file_path)
                        with open(output_file_path, 'w') as f:
                            f.writelines(content)
                            
                    elif ext in ['bin', 'img']:
                        new_file_name = f"{self._trim_file_name(file)}.bin"
                        os.rename(os.path.join(files_path, file), os.path.join(files_path, 'temp.bin'))
                        os.rename(os.path.join(files_path, 'temp.bin'), os.path.join(files_path, new_file_name))
    
                        
            # Releases that ship a bare .ecm (or a bare .bin) carry no cue sheet,
            # and chdman cannot build a CHD without one. Write the standard
            # single-track PS1 sheet so the disc still converts instead of the
            # untouched intermediate being handed to the emulator.
            synthesized_cue = False
            if not any(f.lower().endswith(('.cue', '.gdi')) for f in os.listdir(files_path)):
                bins = sorted(f for f in os.listdir(files_path) if f.lower().endswith('.bin'))
                # Only for a single track: a multi-bin disc needs pregap and track
                # types we cannot infer.
                if len(bins) == 1:
                    cue_name = f"{self._trim_file_name(bins[0])}.cue"
                    with open(os.path.join(files_path, cue_name), 'w') as cue:
                        cue.write(f'FILE "{bins[0]}" BINARY\n')
                        cue.write('  TRACK 01 MODE2/2352\n')
                        cue.write('    INDEX 01 00:00:00\n')
                    synthesized_cue = True
                    logger.info(f"No cue sheet in the release; generated {cue_name}")
            
            # Convert all intermediate files to CHD
            intermediate_files = [f for f in os.listdir(files_path) 
                               if f.lower().endswith(('.cue', '.gdi'))]
            for file in intermediate_files:
                if synthesized_cue:
                    # The sheet is our guess, so a chdman failure is not fatal:
                    # fall through and ship the playable .cue/.bin pair instead.
                    try:
                        _convert_file(file, 'chd')
                    except Exception as e:
                        logger.warning(f"CHD conversion from the generated cue failed: {e}")
                else:
                    _convert_file(file, 'chd')
                
            # If no CHD files were created, fall back to normal processing
            if not any(f.lower().endswith('.chd') for f in os.listdir(output_path)):
                _normal_game_out()
        else:
            _normal_game_out()
            
        # Final move to ROM path
        self.status['current_operation'] = "op_moving_roms"
        output_files = os.listdir(output_path)
        if output_files:
            os.makedirs(self.rom_path, exist_ok=True)
            for file in output_files:
                os.replace(
                    os.path.join(output_path, file),
                    os.path.join(self.rom_path, file)
                )
            self._install_subchannel(output_files)
            group = self._group_discs(output_files)
            if group:
                # The folder is what the menu shows now, so the cover art has to
                # be fetched under its name instead of each disc's.
                game_names_to_scrape = [
                    n for n in game_names_to_scrape
                    if os.path.splitext(n)[1].lower() not in self.DISC_EXTENSIONS
                ]
                game_names_to_scrape.append(group)
        return list(set(game_names_to_scrape))

    # Disc images carry no subchannel data, and PAL PlayStation discs from the
    # LibCrypt era hide their anti-piracy key there. Without it the game loads,
    # runs, and then sits on a black screen. The missing bytes ship with the app
    # as .sbi files, which the emulator reads from beside the disc image.
    SUBCHANNEL_PLATFORMS = ('PS',)
    DISC_EXTENSIONS = ('.chd', '.cue', '.bin', '.img', '.iso', '.pbp')

    @staticmethod
    def _disc_serial(name):
        """The SLES-02965 style id printed on the disc, if the name carries one."""
        match = re.search(r'([A-Za-z]{4})[-_ ]?(\d{5})', name)
        return f"{match.group(1).upper()}-{match.group(2)}" if match else None

    # NextUI lists every file in a ROM folder, so a disc image plus its .sbi
    # shows up as two games. A folder holding an .m3u named after itself is
    # launched directly instead of being browsed into, which collapses a whole
    # multi-disc set - and anything sitting beside it - into one menu entry.
    DISC_GROUP_PLATFORMS = ('PS', 'SEGACD', 'SATURN', 'PCECD', 'DC', 'PANASONIC', 'PCFX', 'NAOMI')
    DISC_NUMBER_RE = re.compile(r'[\(\[][\s_]*(?:disc|disk|cd)[\s_]*(\d+)', re.I)

    @classmethod
    def _disc_group_name(cls, base):
        """Name shared by every disc of one game.

        'Final Fantasy IX (E) (Disc 1) [SLES-02965]' -> 'Final Fantasy IX (E)'
        """
        name = re.sub(r'[\(\[][\s_]*(?:disc|disk|cd)[\s_]*\d+(?:[\s_]*of[\s_]*\d+)?[\s_]*[\)\]]',
                      '', base, flags=re.I)
        name = re.sub(r'[\(\[][\s_]*[A-Za-z]{4}[-_ ]?\d{5}[\s_]*[\)\]]', '', name)
        name = re.sub(r'[\s_.\-]+$', '', name.replace('_', ' '))
        return re.sub(r'\s{2,}', ' ', name).strip() or base

    def _group_discs(self, rom_files):
        """Move disc images into a per-game folder with an .m3u. Returns its name."""
        if self.platform_id not in self.DISC_GROUP_PLATFORMS:
            return None

        discs = [f for f in rom_files
                 if os.path.splitext(f)[1].lower() in self.DISC_EXTENSIONS]
        if not discs:
            return None

        base = os.path.splitext(discs[0])[0]
        # Only worth a folder when there is something to collapse: a disc that is
        # part of a set, or one carrying a companion .sbi that would show up as a
        # second entry.
        has_sbi = any(
            os.path.exists(os.path.join(self.rom_path, f"{os.path.splitext(d)[0]}.sbi"))
            for d in discs
        )
        if not self.DISC_NUMBER_RE.search(base) and not has_sbi:
            return None

        group = self._disc_group_name(base)
        folder = os.path.join(self.rom_path, group)
        try:
            os.makedirs(folder, exist_ok=True)
            for disc in discs:
                stem = os.path.splitext(disc)[0]
                for name in (disc, f"{stem}.sbi"):
                    source = os.path.join(self.rom_path, name)
                    if os.path.exists(source):
                        os.replace(source, os.path.join(folder, name))

            # Rebuilt from the folder each time, so a disc downloaded later joins
            # the set that is already there.
            present = [f for f in os.listdir(folder)
                       if os.path.splitext(f)[1].lower() in self.DISC_EXTENSIONS]
            def disc_number(name):
                found = self.DISC_NUMBER_RE.search(name)
                return int(found.group(1)) if found else 0
            present.sort(key=lambda n: (disc_number(n), n.lower()))

            with open(os.path.join(folder, f"{group}.m3u"), 'w', encoding='utf-8') as playlist:
                playlist.write("\n".join(present) + "\n")

            logger.info(f"Grouped {len(present)} disc(s) under '{group}' with an m3u playlist")
            return group
        except Exception as e:
            logger.warning(f"Could not group discs for '{group}': {e}")
            return None

    def _install_subchannel(self, rom_files):
        """Place the matching .sbi next to any disc image that needs one."""
        if self.platform_id not in self.SUBCHANNEL_PLATFORMS:
            return

        sbi_dir = os.path.join(Config.ASSETS_DIR, 'sbi')
        if not os.path.isdir(sbi_dir):
            return

        # Match on the disc serial: it survives the naming differences between
        # sources, where the same disc may be "Final Fantasy IX (E) (Disc 1)"
        # or "Final Fantasy IX (E)_(Disc_1)".
        by_serial = {}
        for entry in os.listdir(sbi_dir):
            if not entry.lower().endswith('.sbi'):
                continue
            serial = self._disc_serial(entry)
            if serial:
                by_serial[serial] = entry

        for rom in rom_files:
            base, ext = os.path.splitext(rom)
            if ext.lower() not in self.DISC_EXTENSIONS:
                continue
            serial = self._disc_serial(base)
            source = by_serial.get(serial) if serial else None
            if not source:
                continue
            try:
                shutil.copyfile(
                    os.path.join(sbi_dir, source),
                    os.path.join(self.rom_path, f"{base}.sbi")
                )
                logger.info(f"Installed subchannel data {source} for {rom}")
            except Exception as e:
                logger.warning(f"Could not install subchannel data for {rom}: {e}")
                
    def scan_folder(self, subfolder):
        # Handle nested folders
        files = os.listdir(subfolder)
        if files and os.path.isdir(os.path.join(subfolder, files[0])):
            subfolder = os.path.join(subfolder, files[0])
                
        # Check for archive files
        archive_files = [file for file in os.listdir(subfolder) if any(ext in file.lower() for ext in ['.zip', '.rar', '.7z'])]
        if archive_files:
            if not self.isExtractable:
                return subfolder, archive_files
            
            else:
                tmp_path = os.path.join(subfolder, 'tmp')
                os.makedirs(tmp_path, exist_ok=True)
                self.extractor(os.path.join(subfolder, archive_files[0]), tmp_path)
                return self.scan_folder(tmp_path)
        else:
            return subfolder, os.listdir(subfolder)
    
    def extractor(self, file, extract_to):
        """Extract an archive file to the specified directory.
        
        Args:
            file: Path to the archive file
            extract_to: Directory to extract to
            
        Raises:
            FileNotFoundError: If the archive file doesn't exist
            RuntimeError: If extraction fails
        """
        if not os.path.exists(file):
            error_msg = f"Archive file not found: {file}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
            
        self.status['current_operation'] = "op_extracting"
        logger.info(f"Extracting {file}...")
        
        # Fast path: Native Python zipfile extraction for .zip files (fast & zero subprocess overhead)
        if file.lower().endswith('.zip'):
            try:
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                os.remove(file)
                logger.info(f"File {file} has been extracted successfully with zipfile")
                return
            except Exception as ze:
                logger.warning(f"Native zipfile extraction failed, falling back to 7z: {ze}")
                # Clear whatever the aborted run left behind. 7z would otherwise
                # hit an overwrite prompt on those files with no tty to answer it.
                try:
                    shutil.rmtree(extract_to)
                    os.makedirs(extract_to, exist_ok=True)
                except Exception as ce:
                    logger.warning(f"Could not clear partial extraction dir: {ce}")
        
        # -y assumes yes on every prompt: the process has no interactive stdin.
        success, result = self._run_command(
            ["./7z", "x", "-y", file, f'-o{str(extract_to)}'],
            "Extracting",
            status_key="op_extracting"
        )
        
        if not success:
            error_msg = f"Failed to extract {file}\n{result}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        os.remove(file)
        logger.info(f"File {file} has been extracted successfully")