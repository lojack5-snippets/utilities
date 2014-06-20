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

"""Quick script for updating MSVC 2013 (MSVC-12.0) project and project filter
   files with all valid source files in the directory it resideds in
   (recursively).  Runs in either Python 2.7, or Python 3.3+.  See the command
   line help for options."""


# Imports
from __future__ import print_function
import sys
import os
import argparse
import re
import shutil


# Command line options
parser = argparse.ArgumentParser(
    description=u'''Script to automatically ensure all source files are
    included in your MSVC 2013 project files.  The scan will select .h, .hpp,
    .c, .cpp, and .rc files.'''
    )
parser.add_argument('--scan-only', '-s',
                    action='store_true',
                    default=False,
                    help=u'''Only scan the directory and report which
                    files are missing from your project files, but do not
                    update the project files.''')
parser.add_argument('--project', '-p',
                    help=u'''Manually specify your project file, for use
                    if this script cannot find it automatically.''')
parser.add_argument('--filter', '-f',
                    help=u'''Manually specify your project filter file,
                    for use if this script cannot find it automatically.''')
parser.add_argument('--no-filter', '-n',
                    action='store_true',
                    default=False,
                    help=u'''Do not create or update your project filter
                    file with new or missing source files.  This is usefull if
                    you do not like the default way this script organizes the
                    source files in the project.''')
parser.add_argument('--skip-top-dirs',
                    nargs='*',
                    default=[u'docs', u'debug', u'release'],
                    help=u'''Specifies which top-level directories should not
                    be scanned when searching for files to add to project the
                    project files.  By default 'Debug', 'Release', and 'docs'
                    are skipped.'''
                    )
parser.add_argument('--skip-all-dirs',
                    nargs='*',
                    default=[],
                    help=u'''Specifies which directories should not be scanned
                    when searching for files recursively.  By default, none are
                    skipped.'''
                    )
parser.add_argument('--remove-first-dir-name',
                    action='store_true',
                    default=False,
                    help=u'''When adding files to the project filter file, this
                    option lops off the first directory name from the filter
                    names.  This is useful for example if all of your source
                    files are in a single sub-folder, and you don't want.''')
parser.add_argument('--ignore', '-i',
                    nargs='*',
                    default=[],
                    help=u'''Specifies a list of specific files to ignore when
                    scanning for files recursively.  By default, no files with
                    the correct file extensions are skipped.'''
                    )


# Check python version
version = sys.version_info[0:2]
if version != (2,7) and version < (3,3):
    print(__file__, " needs either Python 2.7 or Python 3.3+ to run.")
    sys.exit(0)


# Handle differences in std library for Python veresions
if version == (2,7):
    import codecs
    getcwd = os.getcwdu
    open = codecs.open
else:
    getcwd = os.getcwd


# Regexes
reItemGroupBegin = re.compile(r'<ItemGroup>', re.I)
reItemGroupEnd = re.compile(r'^(\s*</ItemGroup>)', re.I|re.M)
reIndent = re.compile(r'^(\s*)')

# Single line version
reClCompile = re.compile('<ClCompile\s*Include=[\'\"](.+?)[\'\"]\s*/>', re.I)
reClInclude = re.compile('<ClInclude\s*Include=[\'\"](.+?)[\'\"]\s*/>', re.I)
reRcCompile = re.compile('<ResourceCompile\s*Include=[\'\"](.+?)[\'\"]\s*/>', re.I)

# Multi line versions
reClCompileMl = re.compile('^\s*<ClCompile\s*Include=[\'\"](.+?)[\'\"]\s*>\s*(.*?)\s*</ClCompile>', re.I|re.M)
reClIncludeMl = re.compile('^\s*<ClInclude\s*Include=[\'\"](.+?)[\'\"]\s*>\s*(.*?)\s*</ClInclude>', re.I|re.M)
reRcCompileMl = re.compile('^\s*<ResourceCompile\s*Include=[\'\"](.+?)[\'\"]\s*>\s*(.*?)\s*</ResourceCompile>', re.I|re.M)


def backupFile(path):
    '''Create a backup of path if necessary.'''
    if os.path.isfile(path):
        backup = path+u'.bak'
        if os.path.isfile(backup):
            os.remove(backup)
        shutil.copy(path, backup)


def plural(word, number):
    '''Quick 'n dirty function to pluralize *some* words.  It only has to
       handle about 3 words, so rather than using a library, just made a
       quick mapping.'''
    plurals = {
        'entry': 'entries',
        'file': 'files',
        'Header File': 'Header Files',
        'Source File': 'Source Files',
        'Resource File': 'Resource Files',
        'is': 'are',
        'does': 'do',
    }
    if number == 1:
        return word
    else:
        return plurals.get(word, word)


def scan_directory(path, opts):
    '''Scans the given path, building a list of files that need to be included
       in the project (valid source files)'''
    path = os.path.normcase(os.path.normpath(path))
    print(u'Scanning directory:', path)
    rootSkips = [x.lower() for x in opts.skip_top_dirs]
    allSkips = [x.lower() for x in opts.skip_all_dirs]
    fileSkips = [x.lower() for x in opts.ignore]
    headers = []
    sources = []
    resources = []
    for root, dirs, files in os.walk(path):
        isRoot = os.path.normcase(root) == path
        if isRoot:
            # Skip directories that will never have .h/.cpp files in them
            # (and shouldn't)
            dirs[:] = [x for x in dirs if x.lower() not in rootSkips]
        if allSkips:
            dirs[:] = [x for x in dirs if x.lower() not in allSkips]
        for file in files:
            if file.lower() in fileSkips:
                continue
            cext = os.path.splitext(file)[1].lower()
            if cext in {u'.h', u'.hpp'}:
                headers.append(os.path.relpath(os.path.join(root, file), path))
            elif cext in {u'.c', u'.cpp'}:
                sources.append(os.path.relpath(os.path.join(root, file), path))
            elif cext == u'.rc':
                resources.append(os.path.relpath(os.path.join(root, file), path))
    print(u'Found %i header %s,' % (len(headers), plural('file', len(headers))))
    print(u'      %i source %s,' % (len(sources), plural('file', len(sources))))
    print(u'      %i resource %s.' % (len(resources), plural('file', len(resources))))
    return headers, sources, resources


def readUTF8(path):
    '''Reads in a file encoded in UTF8, possibly with the BOM'''
    with open(path, 'rb') as ins:
        data = ins.read()
    # MSVC project/filter files look to be encoded with the BOM.
    # Also, they created with CRLF line endings so we'll stick with that
    # to be consistent.
    return data.decode('utf-8-sig')


def scan_project(path):
    '''Scan the .vcxproj file for files it includes'''
    print(u'Processing project file:', path)
    return scan_file(path)


def scan_filter(path):
    '''Scan the .vcxproj.filters file for files it includes'''
    if os.path.isfile(path):
        print(u'Processing project filter file:', path)
        return scan_file(path)
    else:
        print(u'No project filter file present.')
        return ([],[],[])


def scan_file(path):
    '''Scan a .vcxproj* file, checking for files it includes.  Returns
       a tuple of lists:
       (headers, sources, resources)'''
    data = readUTF8(path)

    groups = reItemGroupBegin.split(data)
    groups = [reItemGroupEnd.split(x)[0] for x in groups]
    includes = [x for x in groups if reClInclude.search(x) or reClIncludeMl.search(x)]
    compiles = [x for x in groups if reClCompile.search(x) or reClCompileMl.search(x)]
    resource = [x for x in groups if reRcCompile.search(x) or reRcCompileMl.search(x)]

    errMsg = u''
    if len(includes) > 1:
        errMsg += u'ERROR: Could not determine location of the Include ItemGroup.\n'
    if len(compiles) > 1:
        errMsg += u'ERROR: Could not determine location of the Compile ItemGroup.\n'
    if len(resource) > 1:
        errMsg += u'ERROR: Could not determine location of the Resource ItemGroup.\n'
    if errMsg:
        raise Exception(errMsg)

    if includes:
        includes = reClInclude.findall(includes[0]) + [x[0] for x in reClIncludeMl.findall(includes[0])]
        print(u' Includes section found, %i %s.'
              % (len(includes), plural('entry', len(includes))))
    else:
        includes = []
        print(u' No Includes section found.')
    if compiles:
        compiles = reClCompile.findall(compiles[0]) + [x[0] for x in reClCompileMl.findall(compiles[0])]
        print(u' Compiles section found, %i %s.'
              % (len(compiles), plural('entry', len(compiles))))
    else:
        compiles = []
        print(u' No Compiles section found.')
    if resource:
        resource = reRcCompile.findall(resource[0]) + [x[0] for x in reRcCompileMl.findall(resource[0])]
        print(u' Resources section found, %i %s.'
              % (len(resource), plural('entry', len(resource))))
    else:
        resource = []
        print(u' No Resources section found.')

    return includes, compiles, resource


def rebuild_group(group, files, kind, indent=None, end=None):
    '''Rebuild an <ItemGroup> entry for a type of include file'''
    if indent is None:
        indent = reIndent.search(group)
    if end is None:
        end = reItemGroupEnd.search(group)
    indent = indent.group(0) if indent else u''
    end = end.group(0).strip('\r\n') if end else u'</ItemGroup>'
    extra = reItemGroupEnd.split(group)
    extra.pop(0)
    extra = (x.strip('\r\n') for x in extra)
    extra = [x for x in extra if x.strip()]
    group = [(u'%s<%s Include="%s" />' % (indent, kind, x)) for x in files]
    group.extend(extra)
    group.append(u'')
    group = u'\r\n'.join(group)
    return group


def write_project(path, files):
    '''Writes the .vcxproj file with the given files'''
    print(u'Writing project file:', path)

    includes, compiles, resource = files

    data = readUTF8(path)

    groups = reItemGroupBegin.split(data)
    groups = [x.strip('\r\n') for x in groups]
    doneIncludes = False
    doneCompiles = False
    doneResource = False
    for i,group in enumerate(groups):
        if not doneIncludes and reClInclude.search(group) or reClIncludeMl.search(group):
            doneIncludes = True
            groups[i] = rebuild_group(group, includes, u'ClInclude')
        elif not doneCompiles and reClCompile.search(group) or reClCompileMl.search(group):
            doneCompiles = True
            groups[i] = rebuild_group(group, compiles, u'ClCompile')
        elif not doneResource and reRcCompile.search(group) or reRcCompileMl.search(group):
            doneResource = True
            groups[i] = rebuild_group(group, resource, u'ResourceCompile')
    # Determine indentation for <ItemGroup>
    lastAndExtra = groups[-1]
    end = reItemGroupEnd.search(lastAndExtra)
    if end:
        end = end.group(0)
    else:
        raise Exception(u'Error in formatting of original project file.')
    indentGroup = reIndent.search(end)
    if indentGroup:
        indentGroup = indentGroup.group(0).strip(u'\r\n')
    else:
        indentGroup = u''
    # Make sure all the sections were written
    if not doneIncludes or not doneCompiles or not doneResource:
        indent = reIndent.search(lastAndExtra)
        if indent:
            indent = indent.group(0)
        else:
            indent = u''
        lastAndExtra = reItemGroupEnd.split(lastAndExtra)
        if len(lastAndExtra) != 2:
            raise Exception(u'Error inserting missing item groups.')
        last = lastAndExtra[0]
        extra = lastAndExtra[1]
        groups[-1] = last

        if not doneIncludes:
            groups.append(rebuild_group(u'', includes, u'ClInclude', indent=indent, end=end))
        if not doneCompiles:
            groups.append(reguild_group(u'', compiles, u'ClCompile', indent=indent, end=end))
        if not doneResource:
            groups.append(rebuild_group(u'', resource, u'ResourceCompile', indent=indent, end=end))
        groups.append(extra)

    backupFile(path)
    with open(path, 'wb', encoding='utf-8-sig') as out:
        groups = (indentGroup+u'<ItemGroup>\r\n').join(groups)
        out.write(groups)


def write_filter(path, files, opts):
    '''Writes the .vcxproj.filters file with the given files'''
    print(u'Writing project filter file:', path)
    # Create list of filters
    headerFilters = set()
    sourceFilters = set()
    resourceFilters = set()
    ## Headers
    for header in files[0]:
        headerFilters.add(os.path.dirname(header))
    if u'' in headerFilters:
        headerFilters.remove(u'')
    ## Source files
    for source in files[1]:
        sourceFilters.add(os.path.dirname(source))
    if u'' in sourceFilters:
        sourceFilters.remove(u'')
    ## Resource files
    for rc in files[2]:
        resourceFilters.add(os.path.dirname(rc))
    if u'' in resourceFilters:
        resourceFilters.remove(u'')

    # Lop off the first part of the directory name if desired
    if opts.remove_first_dir_name:
        temp = set()
        for filter in headerFilters, sourceFilters, resourceFilters:
            for name in filter:
                split = name.split(os.path.sep, 1)
                if len(split) > 1:
                    name = split[1]
                    temp.add(name)
            filter.clear()
            filter |= temp
            temp.clear()

    # Sort the final results
    headerFilters = list(sorted(headerFilters))
    sourceFilters = list(sorted(sourceFilters))
    resourceFilters = list(sorted(resourceFilters))

    # Write new one
    backupFile(path)
    with open(path, 'wb', encoding='utf-8-sig') as out:
        # Write standard filters
        out.write(u'<?xml version="1.0" encoding="utf-8"?>\r\n')
        out.write(u'<Project ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\r\n')
        out.write(u'  <ItemGroup>\r\n')
        out.write(u'    <Filter Include="Source Files">\r\n')
        out.write(u'      <UniqueIdentifier>{4FC737F1-C7A5-4376-A066-2A32D752A2FF}</UniqueIdentifier>\r\n')
        out.write(u'      <Extensions>cpp;c;cc;cxx;def;odl;idl;hpj;bat;asm;asmx</Extensions>\r\n')
        out.write(u'    </Filter>\r\n')
        out.write(u'    <Filter Include="Header Files">\r\n')
        out.write(u'      <UniqueIdentifier>{93995380-89BD-4b04-88EB-625FBE52EBFB}</UniqueIdentifier>\r\n')
        out.write(u'      <Extensions>h;hh;hpp;hxx;hm;inl;inc;xsd</Extensions>\r\n')
        out.write(u'    </Filter>\r\n')
        out.write(u'    <Filter Include="Resource Files">\r\n')
        out.write(u'      <UniqueIdentifier>{67DA6AB6-F800-4c08-8B7A-83BB121AAD01}</UniqueIdentifier>\r\n')
        out.write(u'      <Extensions>rc;ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe;resx;tiff;tif;png;wav;mfcribbon-ms</Extensions>\r\n')
        out.write(u'    </Filter>\r\n')
        # Write extra header filters
        for filter in headerFilters:
            out.write(u'    <Filter Include="Header Files\\%s">\r\n' % filter)
            out.write(u'    </Filter>\r\n')
        for filter in resourceFilters:
            out.write(u'    <Filter Include="Resource Files\\%s">\r\n' % filter)
            out.write(u'    </Filter>\r\n')
        for filter in sourceFilters:
            out.write(u'    <Filter Include="Source Files\\%s">\r\n' % filter)
            out.write(u'    </Filter>\r\n')
        out.write(u'  </ItemGroup>\r\n')
        write_group(out, files[0], u'Header Files', u'ClInclude', opts)
        write_group(out, files[2], u'Resource Files', u'ResourceCompile', opts)
        write_group(out, files[1], u'Source Files', u'ClCompile', opts)
        # Write extra stuff after
        out.write(u'</Project>\r\n')


def write_group(out, files, filterBase, itemKind, opts):
    '''Writes an <ItemGroup> for the .filters file'''
    out.write(u'  <ItemGroup>\r\n')
    for file in files:
        filter_file = file
        if opts.remove_first_dir_name:
            split = file.split(os.path.sep, 1)
            if len(split) > 1:
                filter_file = split[1]
        filter = os.path.join(filterBase, os.path.dirname(filter_file)).strip(os.path.sep)
        out.write(u'    <%s Include="%s">\r\n' % (itemKind, file))
        out.write(u'      <Filter>%s</Filter>\r\n' % filter)
        out.write(u'    </%s>\r\n' % itemKind)
    out.write(u'  </ItemGroup>\r\n')


def main():
    # Get command line arguments
    opts = parser.parse_args()

    # Find the .vcxproj file
    if opts.project and os.path.isfile(opts.project):
        projFile = opts.project
    elif os.path.isfile(u'CBash.vcxproj'):
        # Cheat a little bit for CBash and just search directly for the project
        projFile = u'CBash.vcxproj'
    else:
        candidates = [x for x in os.listdir(getcwd())
                      if x.lower().endswith(u'.vcxproj')
                      and os.path.isfile(x)]
        if len(candidates) != 1:
            print(u'Could not find the project file.  Please specify it with '
                  u'the --project or -p command line argument.')
            return
        projFile = candidates[0]

    # Find the .vcxproj.filters file
    if opts.filter and os.path.isfile(opts.filter):
        filterFile = opts.filter
    else:
        filterFile = projFile+u'.filters'

    # Scan the project directory for files that should be accounted for
    files = scan_directory(getcwd(), opts)

    # Read the project file
    projectFiles = scan_project(projFile)

    # Read the filters file
    filtersFiles = scan_filter(filterFile)

    types = [u'Header File', u'Source File', u'Resource File']
    if opts.scan_only:
        # User specified only to scan, not to update
        for i in range(3):
            proj = set(projectFiles[i])
            filt = set(filtersFiles[i])
            real = set(files[i])
            kind = types[i]
            projMissing = real - proj
            projExtra = proj - real
            filtMissing = real - filt
            filtExtra = filt - real
            if projMissing:
                n = len(projMissing)
                print(u'The following',
                      plural(kind, n),
                      plural(u'is', n),
                      u'missing from your project file:')
                for name in sorted(projMissing):
                    print(u' ', name)
            if projExtra:
                n = len(projExtra)
                print(u'The following',
                      plural(kind, n),
                      plural(u'is', n),
                      u'in your project file, but',
                      plural(u'does', n),
                      u'not exist on disk:')
                for name in sorted(projExtra):
                    print(u' ', name)
            if filtMissing:
                n = len(filtMissing)
                print(u'The following',
                      plural(kind, n),
                      plural(u'is', n),
                      u'missing from your project filter file:')
                for name in sorted(filtMissing):
                    print(u' ', name)
            if filtExtra:
                n = len(filtExtra)
                print(u'The following',
                      plural(kind, n),
                      plural(u'is', n),
                      u'in your project filter file, but',
                      plural(u'does', n),
                      u'not exist on disk:')
                for name in sorted(filtExtra):
                    print(u' ', name)
            if not (projMissing | projExtra | filtMissing | filtExtra):
                print(u'No', plural(kind, 2), u'are missing from your project files.')
        return

    # Update the files as applicable
    write_project(projFile, files)
    if not opts.no_filter:
        write_filter(filterFile, files, opts)

    for i in range(3):
        proj = set(projectFiles[i])
        filt = set(filtersFiles[i])
        real = set(files[i])
        kind = types[i]
        print(u'Removed %i and added %i %s to the project file.' %
              (len(proj-real), len(real-proj), plural(kind, len(real-proj))))
        if not opts.no_filter:
            print(u'Removed %i and added %i %s to the project filter file.' %
                  (len(filt-real), len(real-filt), plural(kind, len(real-filt))))


if __name__ == '__main__':
    main()
