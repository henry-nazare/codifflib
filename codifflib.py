import sys

from difflib import SequenceMatcher

from pygments import lex
from pygments.lexers.c_cpp import CLexer
from pygments.styles import get_style_by_name

class CodeDiff:
  opcode_style = {
    'insert': {'bgcolor': 'eaffea'}, 'replace': {'bgcolor': 'fff68f'},
    'delete': {'bgcolor': 'ffaaaa'}, 'equal': {'bgcolor': None},
  }

  def __init__(self, from_str, to_str):
    self.from_str = from_str
    self.to_str = to_str

    # difflib stuff.
    self.sm = SequenceMatcher(None, from_str, to_str)

    # Pygments stuff.
    # TODO: allow chosing of style.
    self.style = get_style_by_name('colorful')

    self.style_map = {}
    for token_type, style in self.style:
      self.style_map[token_type] = style

    self.descs = []
    pdesc = self.get_pygmentation_desc()
    ddesc = self.get_difflib_desc()
    while pdesc or ddesc:
      # The diff may be larger than the program itself.
      if not pdesc:
        desc = ddesc.pop(0)

        # Update the starting position of the diff fragment to the last
        # character descriptor in descriptor list.
        desc[1] = self.descs[-1][2]
        self.descs.append(desc)
        break

      # We have an opcode from dstart to dend.
      dstyle, dstart, dend = ddesc[0]

      # We have an token dstart to dend.
      pstyle, pstart, pend = pdesc[0]

      # TODO: update() overwrites values for common keys, is this correct?
      style = pstyle.copy()
      style.update(dstyle)

      # If the token fits within the opcode region, merge the two styles.
      if dstart <= pstart and pend <= dend:
        self.descs.append([style, pstart, pend])

        # Next token & remove the diff opcode if necessary.
        pdesc.pop(0)
        if (pend == dend): ddesc.pop(0)

      # If the token doesn't fit within the opcode region, seperate it into two.
      elif dstart <= pstart and pend >= dend:
        self.descs.append([style, pstart, dend])

        # Second part of the token stays in the array.
        pdesc[0] = [style, dend, pend]
        ddesc.pop(0)
      else:
        # TODO: missing some cases?
        assert False

    # Both arrays should be empty when the above loop finishes.
    assert (not pdesc) and (not ddesc)

  def get_pygmentation_desc(self):
    desc = []
    token_start = token_end = 0
    for token_type, token in lex(self.from_str, CLexer()):
      token_start = token_end
      token_end += len(token)
      desc.append([self.style_map[token_type], token_start, token_end])
    return desc

  def get_difflib_desc(self):
    desc = []
    for s in self.sm.get_opcodes():
      opcode, from_start, from_end, to_start, to_end = s
      desc.append([CodeDiff.opcode_style[opcode], from_start, from_end])
    return desc

  def to_html(self):
    # TODO: don't hardcode output formatting.
    html = ""
    for style, start, end in self.descs:
      span = '<span style="'
      if style['bgcolor']:
        span += 'background: #' + style['bgcolor'] + ';'

      # TODO: maps always containing 'bgcolor' and not necessarily 'color' may
      # by a bit confusing.
      if ('color' in style) and style['color']:
        span += 'color: #' + style['color'] + ';'
      span += '">'
      fragment = self.from_str[start:end]
      fragment = fragment.replace('\n', '<br>')
      fragment = fragment.replace(' ', '&nbsp;')
      span += fragment + '</span>'
      html += span
    return html

  @staticmethod
  def from_files(from_file, to_file):
    with open(from_file) as f:
      from_str = f.read()
    with open(to_file) as f:
      to_str = f.read()
    return CodeDiff(from_str, to_str)

