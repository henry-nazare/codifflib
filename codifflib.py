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

  def get_desc(self, for_from_str):
    descs = []
    pdesc = self.get_pygmentation_desc(for_from_str)
    ddesc = self.get_difflib_desc(for_from_str)
    while pdesc or ddesc:
      # The diff may be larger than the program itself.
      if not pdesc:
        desc = ddesc.pop(0)

        # Update the starting position of the diff fragment to the last
        # character descriptor in descriptor list.
        desc[1] = descs[-1][2]
        descs.append(desc)
        break

      # We have an opcode from dstart to dend.
      dstyle, dstart, dend = ddesc[0]

      # We have an token dstart to dend.
      pstyle, pstart, pend = pdesc[0]

      # TODO: update() overwrites values for common keys, is this correct?
      style = pstyle + dstyle

      # If the token fits within the opcode region, merge the two styles.
      if dstart <= pstart and pend <= dend:
        descs.append([style, pstart, pend])

        # Next token & remove the diff opcode if necessary.
        pdesc.pop(0)
        if (pend == dend): ddesc.pop(0)

      # If the token doesn't fit within the opcode region, seperate it into two.
      elif dstart <= pstart and pend >= dend:
        descs.append([style, pstart, dend])

        # Second part of the token stays in the array.
        pdesc[0] = [style, dend, pend]
        ddesc.pop(0)
      else:
        # TODO: missing some cases?
        assert False

    # Both arrays should be empty when the above loop finishes.
    assert (not pdesc) and (not ddesc)
    return descs

  def get_pygmentation_desc(self, for_from_str):
    desc = []
    s = self.from_str if for_from_str else self.to_str
    token_start = token_end = 0
    for token_type, token in lex(s, CLexer()):
      token_start = token_end
      token_end += len(token)
      token_class = 'token-' + '-'.join(token_type).lower()
      desc.append([[token_class], token_start, token_end])
    return desc

  def get_difflib_desc(self, for_from_str):
    desc = []
    for s in self.sm.get_opcodes():
      opcode, from_start, from_end, to_start, to_end = s
      if for_from_str:
        desc.append([['opcode-' + opcode], from_start, from_end])
      else:
        desc.append([['opcode-' + opcode], to_start, to_end])
    return desc

  def to_html(self, for_from_str):
    # TODO: don't hardcode output formatting.
    html = ""
    descs = self.get_desc(for_from_str)
    for style, start, end in descs:
      span = '<span class="' + ' '.join(style) + '">'
      fragment = (self.from_str if for_from_str else self.to_str)[start:end]
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

