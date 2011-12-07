#!/usr/bin/env python3
# vim: tabstop=2 expandtab

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

class GlslObfuscator:
  re_identifier    = re.compile (br"(?<!#)[a-zA-Z_][a-zA-Z0-9_]*")
  re_remove        = re.compile (br" *//.*?$|/\*.*?\*/|^ +|(?<=#) +",
                                 re.DOTALL | re.MULTILINE)
  re_extra_space   = re.compile (br" {2,}")
  re_empty_lines   = re.compile (br"\n{2,}")
  name_chars       = br"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

  def __init__ (self, prefix = b"_"):
    self.replacements = {}
    self.prefix       = prefix
    self.name_index   = 1

  def indexToName (self, index):
    out = []
    while index > 0:
      char_index = index % len (self.name_chars)
      out.append (self.name_chars[char_index:char_index + 1])
      index = index // len (self.name_chars)

    out.reverse ()
    return self.prefix + b"".join (out)

  def nextName (self):
    out = self.indexToName (self.name_index)
    self.name_index += 1
    return out

  def obfuscate (self, text):
    text = self.re_remove.sub (b"", text)
    text = self.re_empty_lines.sub (b"\n", text)
    text = self.re_extra_space.sub (b" ", text)

    out = []
    index = 0

    for match in self.re_identifier.finditer (text):
      if match.group (0).startswith (self.prefix) and match.group (0).find (b"__") < 0:
        replacement = self.replacements.get (match.group (0))
        if replacement is None:
          replacement = self.nextName ()
          self.replacements[match.group (0)] = replacement

        if index < match.start ():
          out.append (text[index:match.start ()])

        out.append (replacement)
        index = match.end ()

      elif match.group (0).endswith (self.prefix):
        stderr.write ("*** warning: ")
        stderr.write (match.group (0).decode ())
        stderr.write ("\n")

    if index < len (text):
      out.append (text[index:])

    return b"".join (out)

  def obfuscateFile (self, filename):
    with open (filename, "rb") as f:
      return self.obfuscate (f.read ())
