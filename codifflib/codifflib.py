#!/usr/bin/env python

import sys

from difflib import SequenceMatcher, IS_CHARACTER_JUNK

from operator import attrgetter

from pygments import lex
from pygments.lexers.c_cpp import CLexer

class Opcode(object):
  def __init__(self, opcode, data):
    self.opcode = opcode
    self.data = data

  @staticmethod
  def from_lines(opcode, lines):
    if opcode == 'fill':
      return [Opcode(opcode, len(lines))]
    return [Opcode(opcode, char) for line in lines for char in line]

  @staticmethod
  def from_string(opcode, string):
    return [Opcode(opcode, char) for char in string]

  def __repr__(self):
    if self.opcode == 'fill':
      data = '\\n' * self.data
    elif self.data == '\n':
      data = '\\n'
    else:
      data = self.data
    return '<%s %s>' % (self.opcode, data)

class Pygment(object):
  def __init__(self, token_type, token):
    self.token_type = token_type
    self.token = token

  def __repr__(self):
    if self.token == '\n':
      token = '\\n'
    else:
      token = self.token
    return '<%s %s>' % (self.token_type, token)

class Char(object):
  def __init__(self, diff, pyg):
    self.diff = diff
    self.pyg = pyg

  def __repr__(self):
    return '{%s %s}' % (str(self.diff), str(self.pyg))

class Line(object):
  def __init__(self, fillsize=None):
    self.chars = []
    self.fillsize = fillsize

  def is_all_opcode_line(self, opcode):
    return all(map(lambda char: char.diff.opcode == opcode, self.chars))

# difflib-based code used for ndiff.
class Differ:
  def __init__(self, linejunk=None, charjunk=None):
    self.linejunk = linejunk
    self.charjunk = charjunk

  def compare(self, a, b):
    cruncher = SequenceMatcher(self.linejunk, a, b)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
      if tag == 'replace':
        for diff in self._replace(a, alo, ahi, b, blo, bhi):
          yield diff
      elif tag == 'delete':
        lines = a[alo:ahi]
        yield (Opcode.from_lines(tag, lines), Opcode.from_lines('fill', lines))
      elif tag == 'insert':
        lines = b[blo:bhi]
        yield (Opcode.from_lines('fill', lines), Opcode.from_lines(tag, lines))
      elif tag == 'equal':
        lines = a[alo:ahi]
        opcode = Opcode.from_lines(tag, lines)
        yield (opcode, opcode)
      else:
        raise ValueError, 'unknown tag %r' % (tag,)

  def _replace(self, a, alo, ahi, b, blo, bhi):
    best_ratio, cutoff = 0.74, 0.75
    cruncher = SequenceMatcher(self.charjunk)
    eqi, eqj = None, None # First indices of equal lines (if any).

    # Search for the pair that matches best without being identical
    # (identical lines must be junk lines, & we don't want to sync up
    # on junk -- unless we have to).
    for j in xrange(blo, bhi):
      bj = b[j]
      cruncher.set_seq2(bj)
      for i in xrange(alo, ahi):
        ai = a[i]
        if ai == bj:
          if eqi is None:
            eqi, eqj = i, j
          continue
        cruncher.set_seq1(ai)
        if cruncher.real_quick_ratio() > best_ratio and \
            cruncher.quick_ratio() > best_ratio and \
            cruncher.ratio() > best_ratio:
          best_ratio, best_i, best_j = cruncher.ratio(), i, j

    if best_ratio < cutoff:
      # No non-identical "pretty close" pair.
      if eqi is None:
        # No identical pair either -- treat it as a straight replace.
        yield (Opcode.from_lines('replace', a[alo:ahi]), Opcode.from_lines('replace', b[blo:bhi]))
        return
      # No close pair, but an identical pair -- sync up on that.
      best_i, best_j, best_ratio = eqi, eqj, 1.0
    else:
      # There's a close pair, so forget the identical pair (if any).
      eqi = None

    # a[best_i] very similar to b[best_j]; eqi is None iff they're not
    # identical.
    # Pump out diffs from before the sync point.
    yield (Opcode.from_lines('delete', a[alo:best_i]), Opcode.from_lines('insert', b[blo:best_j]))

    aelt, belt = a[best_i], b[best_j]
    if eqi is None:
      cruncher.set_seqs(aelt, belt)
      for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
        la, lb = ai2 - ai1, bj2 - bj1
        if tag == 'replace':
          yield (Opcode.from_string(tag, aelt[ai1:ai2]), Opcode.from_string(tag, belt[bj1:bj2]))
        elif tag == 'delete':
          chars = aelt[ai1:ai2]
          yield (Opcode.from_string(tag, chars), [])
        elif tag == 'insert':
          chars = belt[bj1:bj2]
          yield ([], Opcode.from_string(tag, chars))
        elif tag == 'equal':
          chars = aelt[ai1:ai2]
          opcode = Opcode.from_string(tag, chars)
          yield (opcode, opcode)
        else:
          raise ValueError, 'unknown tag %r' % (tag,)
    else:
      # The sync pair is identical.
      opcode = Opcode.from_chars(tag, aelt)
      yield (opcode, opcode)

    # Pump out diffs from after the sync point.
    opcode = Opcode.from_lines(tag, a[best_i + 1:ahi])
    for diff in self._helper(a, best_i + 1, ahi, b, best_j + 1, bhi):
      yield diff

  def _helper(self, a, alo, ahi, b, blo, bhi):
    if alo < ahi:
      if blo < bhi:
        for diff in self._replace(a, alo, ahi, b, blo, bhi):
          yield diff
        else:
          yield (Opcode.from_string('delete', a[alo:ahi]), [])
    elif blo < bhi:
      yield ([], Opcode.from_string('insert', b[blo:bhi]))

class Pygmenter:
  def get(self, p):
    # TODO: don't hardcode lexer.
    for token_type , token in lex(p, CLexer()):
      for c in token:
        yield Pygment(token_type, c)

class Codiff:
  def __init__(self, from_str, to_str):
    diffs = Differ(charjunk=IS_CHARACTER_JUNK).compare(from_str, to_str)
    from_diffs = []
    to_diffs = []
    for from_diff, to_diff in diffs:
      from_diffs.append(from_diff)
      to_diffs.append(to_diff)

    self.from_diffs = sum(from_diffs, [])
    self.to_diffs = sum(to_diffs, [])

    self.from_pyg = Pygmenter().get(''.join(from_str))
    self.to_pyg = Pygmenter().get(''.join(to_str))

  def _gen_lines(self, diffs, pygs):
    def gen_chars():
      for char in diffs:
        if char == None or char.opcode == 'fill':
          yield Char(char, None)
        else:
          pyg = pygs.next()
          assert char.data == pyg.token
          yield Char(char, pyg)

    line = Line()
    for char in gen_chars():
      if char.diff.opcode == 'fill':
        yield Line(fillsize=char.diff.data)
        continue

      line.chars.append(char)
      if char.diff.data == '\n':
        yield line
        line = Line()
    yield line

  def get_from_prog(self):
    return self._gen_lines(self.from_diffs, self.from_pyg)

  def get_to_prog(self):
    return self._gen_lines(self.to_diffs, self.to_pyg)

  @staticmethod
  def from_files(from_file, to_file):
    with open(from_file) as f:
      from_str = f.readlines()
    with open(to_file) as f:
      to_str = f.readlines()

    return Codiff(from_str, to_str)

