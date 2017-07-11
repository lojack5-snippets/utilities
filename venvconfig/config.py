#!/usr/bin/env python3

# BSD License and Copyright Notice ============================================
#  Copyright (c) 2017, Lojack (https://github.com/lojack5)
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither the name of venvconfig nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
# =============================================================================

"""
Configuration package for venvconfig.  Provides a class for holding information
pertaining to a virtual environments location, name, and package requirements.

Copyright (c) 2017, Lojack.
"""

__all__ = ['Config', 'ConfigError']


__version__ = '0.0.1'
__author__ = "Lojack <lojo.jacob@gmail.com>"
__date__ = '09 July 2017'


import configparser
import contextlib
import io
from pathlib import Path
import pip
import re
import subprocess
import sys


class ConfigError(Exception):
    """ConfigError

       Thrown when a Config operation cannot be performed
       due to a problem with the current configuration.
    """
    pass


class Config:
    def __init__(self, path=None, name=None, requirements={}):
        """Config([path=None][, name=None][, requirements={}])

           Creates a venv configuration object.
           path - Filesystem path where the venv is/will be located.
           name - A name to be giving to the venv
           requirements - A dictionary of (package, version) strings
                          listing the packages needed for this venv.
        """
        self.path = path
        self.name = name
        self.requirements = requirements

    def __str__(self):
        name = self.name if self.name else self.path
        return f'{self.__class__.__name__}({name})'

    def save_config(self, path):
        """save_config(path)
        
           Saves the currently loaded venv configuration to file.
           
           Throws ConfigError if the configured venv path does not
           refer to an actual path (non-existing paths are OK).
        """
        if not self.path:
            raise ConfigError(f'Invalid venv path: {self.path}')
        config = configparser.ConfigParser()
        config['venv'] = {}
        config['venv']['path'] = str(self.path)
        if self.venv_name:
            config['venv']['name'] = self.name
        config['pip'] = self.requirements
        with open(path, 'w') as out:
            config.write(out)

    def read_config(self, path):
        """read_config(path)
        
           Reads the venv configuration data from a config file.
        """
        config = configparser.ConfigParser()
        config.read(path)
        vpath = Path(config['venv']['path'])
        name = config['venv'].get('name', None)
        requirements = config['pip']
        # Commit changes
        self.path = vpath
        self.name = name
        self.requirements = requirements

    def read_target(self, path):
        """read_target(path)
        
           Reads the venv path, name, and requirements from the
           venv located at path.
        """
        vpath, name = self._read_target_venv(venv_path)
        requirements = self._read_target_pip(venv_path)
        # Commit changes
        self.path = vpath
        self.name = name
        self.requirements = requirements

    def read_requirements(self, path):
        """read_requirements(path)
        
           Reads package dependencies from a requirements.txt file
           specified by path.
        """
        requirements = {}
        with open(path, 'r') as ins:
            self.requirements = self._parse_requirements(ins)

    def read_current_pip(self):
        """read_current_pip()
        
           Reads package depenencies for the current Python
           environment via pip.
        """
        self.requirements = self._read_current_pip()

    def _read_current_pip(self):
        f = io.StringIO(newline=None)
        with contextlib.redirect_stdout(f):
            pip.main(['freeze'])
        return self._parse_requirements(f.getvalue())

    def read_target_pip(self, path):
        """read_target_pip(path)
        
           Reads package dependencies for the venv located at
           path, using pip.
        """
        self.requirements = self._read_target_pip(path)
        
    def current_missing_requirements(self):
        """current_missing_requirements()
        
           Returns a dictionary of (package, version) pairs detailing any
           configured requirements which are not installed to the current
           Python environment, as reported by pip.
        """
        have = self._read_current_pip()
        return {key:value
                for (key,value) in self.requirements.items()
                if key.lower() not in have
                   or self._version(value) > self._version(have[key.lower()])
                }

    def target_missing_requirements(self, path):
        """target_missing_requirements(path)
        
           Returns a dictionary of (package, version) pairs detailing any
           configured requirements which are not installed to the target venv,
           as reported by pip.
        """
        have = self._read_target_pip(path)
        return {key:value
                for (key,value) in self.requirements.items()
                if key.lower() not in have
                }

    def executable(self, path):
        """executable(path)
        
           Returns the path to the python executable in the venv located at
           path.
        """
        bin = 'Scripts' if sys.platform == 'win32' else 'bin'
        return Path(path) / bin / Path(sys.executable).name

    def _read_target_pip(self, path):
        cmd = [self.executable(path), '-m', 'pip', 'freeze']
        ins, err = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
        return self._parse_requirements(ins)

    def _parse_requirements(self, data):
        if isinstance(data, bytes):
            data = data.decode()
        if isinstance(data, str):
            lines = data.splitlines()
        elif isinstance(data, io.TextIOWrapper):
            lines = (x for x in data)
        return dict(((x.strip().lower() for x in line.split('=='))
                    for line in lines))

    def _version(self, version):
        version = version.strip().strip('()').lower().split('.')
        version = tuple(int(x) if x.isdigit() else x for x in version)
        return version

    def read_current_venv(self):
        """read_current_venv()
        
           If run from within a venv, reads the venv's name and path.
           No-op if run outside of a venv.
        """
        if sys.prefix != sys.base_prefix:
            try:
                path = Path(sys.prefix).relative_to(Path.cwd())
            except ValueError:
                path = Path(sys.prefix)
            name = self._read_venv_name(path)
            # Commit changes
            self.path = path
            self.name = name

    def read_target_venv(self, path):
        """read_target_venv(path)
        
           Reads the venv path and name from the venv located at
           path.
           
           Throws ConfigError if no venv exists at path.
        """
        self.path, self.name = self._read_target_venv(path)

    def _read_target_venv(self, path):
        path = Path(path)
        cfg = path / 'pyvenv.cfg'
        if not cfg.is_file():
            raise ConfigError(f'No venv exists at {path}.')
        name = self._read_venv_name(path)
        return path, name

    def _read_venv_name(self, path):
        if sys.platform == 'win32':
            activate = path / 'Scripts' / 'activate.bat'
            rePrompt = re.compile(r'set\s+\"PROMPT=\((.+?)\)\s\%PROMPT\%\"',
                                  re.I)
        else:
            activate = path / 'bin' / 'activate'
            rePrompt = re.compile(r'PS1\=\"\((.+?)\)\s+\$PS1\"', re.I)
        with open(activate, 'r') as ins:
            for line in ins:
                match = rePrompt.search(line)
                if match:
                    return match.group(1)
        return None
