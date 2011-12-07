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

class GlslObfuscator:
  re_identifier    = re.compile (br"(?<!#)[a-zA-Z_][a-zA-Z0-9_]*")
  re_comment       = re.compile (br"//.*?$|/\*.*?\*/", re.DOTALL | re.MULTILINE)
  re_leading_space = re.compile (br"^ +", re.MULTILINE)
  re_extra_space   = re.compile (br" {2,}")
  re_empty_lines   = re.compile (br"\n{2,}")
  name_chars       = br"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

  def __init__ (self, prefix = b"_"):
#    self.identifiers  = set ()
    self.replacements = {}
    self.prefix       = prefix
    self.name_index   = 0

#  def preprocess (self, text):
#    for match in self.re_identifier.finditer (text):
#      self.identifiers.add (match.group (0))
#
#  def preprocessFile (self, filename):
#    with open (filename, "rb") as f:
#      self.preprocess (f.read ())

  def indexToName (self, index):
    out = []
    if index == 0:
      out.append (self.name_chars[0:1])
    else:
      while index > 0:
        char_index = index % len (self.name_chars)
        out.append (self.name_chars[char_index:char_index + 1])
        index = index // len (self.name_chars)

    out.reverse ()
    return self.prefix + b"".join (out)

  def nextName (self):
    out = self.indexToName (self.name_index)
    self.name_index += 1
#    while out in self.identifiers:
#      out = self.indexToName (self.name_index)
#      self.name_index += 1
    return out

  def obfuscate (self, text):
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

    if index < len (text):
      out.append (text[index:])

    out = self.re_comment.sub (b"", b"".join (out))
    out = self.re_leading_space.sub (b"", out)
    out = self.re_empty_lines.sub (b"\n", out)
    return self.re_extra_space.sub (b" ", out)

  def obfuscateFile (self, filename):
    with open (filename, "rb") as f:
      return self.obfuscate (f.read ())