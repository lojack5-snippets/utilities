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
Package for venvconfig that handles setting up virtual environments and
launching python scripts within them.

Copyright (c) 2017, Lojack.
"""

__all__ = ['Launcher', 'ensure_active']

__version__ = '0.0.1'
__author__ = "Lojack <lojo.jacob@gmail.com>"
__date__ = '09 July 2017'


import venv
import sys
import os
import subprocess
from pathlib import Path
import pip


from .config import Config, ConfigError


class Launcher:
    def __init__(self, config=None):
        """Venv(path [, config=None])
        
           Creates a venv management object, using the Config object specified,
           or if config is a path-like object, loads the  Config object from
           said path.
        """
        if isinstance(config, Config):
            self.config = config
        elif isinstance(config, (os.PathLike,str,bytes)):
            self.config = Config()
            self.config.read_config(config)
        else:
            self.config = Config()

    def active(self):
        """active()
        
           Return whether the configured venv is the active venv.
        """
        return Path(sys.prefix) == self.config.path.resolve()

    def ensure_active(self):
        """ensure_active()
        
           If the configured venv is not active, relaunches this script (as
           determined by sys.argv[0]) under the configured venv.  If the venv
           is not present or malformed, created the venv first.
           
           If the configured venv is active, checks for and installs missing
           packaged dependencies.
        """
        if not self.active():
            self.launch_script(sys.argv[0])
            sys.exit(0)
        self.install_requirements()

    def ensure_active_new_console(self):
        """ensure_active_new_console()
        
           Identical to ensure_active(), but the if this script needs to be
           relaunched, it is done so in a new console.
        """
        if not self.active():
            self.launch_script_new_console(sys.argv[0])
            sys.exit(0)
        self.install_requirements()

    def create(self):
        """create()
        
           Creates the configured venv, overriding any files present.
        """
        cmd = [str(self.config.path), '--clear']
        if self.config.name:
            cmd.extend(['--prompt', self.config.name])
        venv.main(cmd)

    def install_requirements(self):
        """install_requirements()
        
           If the configured venv is active, installs any missing requirements.
        """
        if self.active():
            missing = self.config.current_missing_requirements()
            for item in missing:
                cmd = f'{item}=={missing[item]}'
                pip.main(['install', cmd, '-q', '-q', '-q'])

    def launch_script(self, script_path, args=None):
        """launch_script(script_path [, args=None])
        
           Activates the configured venv, creating it if necessary, and
           launches the target script in a new process, optionally with args
           on the command line.
        """
        self._launch_script(script_path, args)


    def launch_script_new_console(self, script_path, args=None):
        """launch_script_new_console(script_path [,args=None])
        
           Like launch_script, but the new process is launched in a new console
           window.
        """
        self._launch_script(script_path, args, subprocess.CREATE_NEW_CONSOLE)


    def _launch_script(self, script_path, args=None, flags=0):
        if args is None:
            args = sys.argv
            args.pop(0) # Remove the first argument (script name)
        repair = '--repair-venv' in args
        if repair:
            args.remove('--repair-venv')
            # Will perform the actual repair below
        elif self.config.executable(self.config.path).is_file():
            self._launch(script_path, args, flags)
            return
        else:
            # Either the venv is missing its python instance, or
            # we specified to repair
            self.create()
            self._launch(script_path, args, flags)


    def _launch(self, script_path, args, flags=0):
        try:
            exe = self.config.executable(self.config.path)
            cmd = [str(exe), str(script_path)]
            cmd.extend(args)
            subprocess.Popen(cmd, creationflags=flags)
            return
        except Exception as e:
            print('Could not launch via venv:', e)
            raise


def ensure_active(config):
    """ensure_active(config)
    
       All-in-one function to relaunch the current script into a venv with
       requirements installed, with some stdout printing for feedback.
       (TODO: convert to logging)
    """
    v = Launcher(config)
    if not v.active():
        print('activating venv')
        v.ensure_active()
    elif v.config.current_missing_requirements():
        print('installing missing dependencies:',
              v.config.current_missing_requirements())
        v.install_requirements()
