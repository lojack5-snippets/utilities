# BSD License and Copyright Notice ============================================
#  Copyright (c) 2014, Lojack
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
#  * Neither the name of the project_update nor the names of its
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
Recursively walks a directory, setting the HIDDEN, SYSTEM, and READONLY 
attributes on any files named 'folder.jpg' found.  Just a quick script to help
when managing media libraries.
"""
import ctypes
import os
import sys
from enum import IntFlag


class AttribFlags(IntFlag):
    READONLY            = 0x0001
    HIDDEN              = 0x0002
    SYSTEM              = 0x0004
    ARCHIVE             = 0x0020
    NORMAL              = 0x0080
    TEMPORARY           = 0x0100
    OFFLINE             = 0x1000
    NOT_CONTENT_INDEXED = 0x2000

    FOLDER_JPG_FLAGS = READONLY | HIDDEN | SYSTEM


SetFileAttributes = ctypes.windll.kernel32.SetFileAttributesW
GetFileAttributes = ctypes.windll.kernel32.GetFileAttributesW


def set_attribs(filename, flags=AttribFlags.FOLDER_JPG_FLAGS):
    """Sets the specified file attributes if needed."""
    current_flags = AttribFlags(GetFileAttributes(filename))
    missing = flags & ~current_flags
    if missing:
        print(filename)
        flags = flags | current_flags
        SetFileAttributes(filename, flags)


def walk_and_set(directory, flags=AttribFlags.FOLDER_JPG_FLAGS):
    """Walk the specified directory, setting file attributes on any 'folder.jpg' files"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower() == 'folder.jpg':
                path = os.path.join(root, file)
                set_attribs(path, flags)


def main():
    if len(sys.argv) > 1:
        walk_and_set(sys.argv[1])
    else:
        walk_and_set(os.getcwd())


if __name__ == '__main__':
    main()
