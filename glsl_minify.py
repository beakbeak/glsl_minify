#!/usr/bin/env python3
# vim: tabstop=4 expandtab

# Copyright (c) 2011, Philip Lafleur
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
from sys import stderr

class GlslMinifier:
    re_tab                = re.compile(br"\t")
    re_identifier         = re.compile(br"(?<!#)[a-zA-Z_][a-zA-Z0-9_]*")
    re_remove             = re.compile(br"\r| *//.*?$|/\*.*?\*/|^ +", re.DOTALL | re.MULTILINE)
    re_define             = re.compile(br" *# *define")
    re_define_pre_padding = re.compile(br" *(#+|[+*-/=<>!]=?|[.,);?:{}]|[|&]{2})")
    re_pre_padding        = re.compile(br" *(#+|[+*-/=<>!]=?|[.,();?:{}]|[|&]{2})")
    re_post_padding       = re.compile(br"(#+|[+*-/=<>!]=?|[.,(;?:{}]|[|&]{2}) *")
    re_multispace         = re.compile(br"( |\n){2,}")
    name_chars            = br"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    def __init__(self, in_prefix=None, out_prefix=None):
        if not in_prefix:
            in_prefix = b"_"
        if not out_prefix:
            out_prefix = b"_"

        self.replacements = {}
        self.in_prefix    = in_prefix
        self.out_prefix   = out_prefix
        self.name_index   = 1

    def _indexToName(self, index):
        out = []
        while index > 0:
            char_index = index % len(self.name_chars)
            out.append(self.name_chars[char_index:char_index + 1])
            index = index // len(self.name_chars)

        out.reverse()
        return self.out_prefix + b"".join(out)

    def _nextName(self):
        out = self._indexToName(self.name_index)
        self.name_index += 1
        return out

    def minifyBytes(self, text):
        text = self.re_tab.sub(b" ", text)
        text = self.re_remove.sub(b"", text)

        text = text.splitlines()
        for index, line in enumerate(text):
            if self.re_define.match(line):
                text[index] = self.re_define_pre_padding.sub(br"\1", line)
            else:
                text[index] = self.re_pre_padding.sub(br"\1", line)
        text.append(b"")
        text = b"\n".join(text)

        text = self.re_post_padding.sub(br"\1", text)
        text = self.re_multispace.sub(br"\1", text)

        out = []
        index = 0

        for match in self.re_identifier.finditer(text):
            if(match.group(0).startswith(self.in_prefix)
                    and match.group(0).find(b"__") < 0):
                replacement = self.replacements.get(match.group(0))
                if replacement is None:
                    replacement = self._nextName()
                    self.replacements[match.group(0)] = replacement

                if index < match.start():
                    out.append(text[index:match.start()])

                out.append(replacement)
                index = match.end()

        if index < len(text):
            out.append(text[index:])

        return b"".join(out)

    def minifyFile(self, filename):
        with open(filename, "rb") as f:
            return self.minifyBytes(f.read())

if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c", "--copy", action = "store_true", help = "copy files without minifying")
    arg_parser.add_argument("in_path", nargs = 1, help = "path containing source glsl files")
    arg_parser.add_argument("out_path", nargs = 1, help = "where to store output files")
    arg_parser.add_argument(
        "filenames", nargs = '*',
        help = "optional list of file paths relative to current directory")
    args = arg_parser.parse_args()

    import os, errno

    minifier = GlslMinifier()
    in_path = args.in_path[0]
    out_path = args.out_path[0]

    def minifyFile(filename):
        out_dirname   = os.path.join(out_path, os.path.relpath(os.path.dirname(filename), in_path))
        out_filename  = os.path.join(out_dirname, os.path.basename(filename))

        if args.copy:
            print("copying " + out_filename)
            with open(filename, "rb") as f:
                out_text = f.read()
        else:
            print("minifying " + out_filename)
            out_text = minifier.minifyFile(filename)

        try:
            os.makedirs(out_dirname)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(out_dirname):
                pass
            else:
                raise

        with open(out_filename, "wb") as f:
            f.write(out_text)

    if args.filenames:
        for filename in args.filenames:
            minifyFile(filename)
    else:
        for dirpath, dirnames, filenames in os.walk(in_path, onerror = lambda e: stderr.write(str(e))):
            for filename in filenames:
                if filename.lower().endswith(".glsl"):
                    minifyFile(os.path.join(dirpath, filename))
