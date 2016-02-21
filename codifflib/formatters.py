#!/usr/bin/env python

import sys

# TODO: requires Bootstrap, leave it as is?
class HtmlFormatter(object):
  class Config:
    def __init__(self):
      self.lineno = 1

  def _format_line(self, line, cfg):
    if line.fillsize:
      s = '<div><div class="idx col-md-1"> </div><div class="line-filler col-md-11"><br></div></div>'
      return s * line.fillsize

    s = '<div><div class="idx col-md-1">{0}</div><div class="line-{1} col-md-11">'
    if line.is_all_opcode_line('replace'):
      s = s.format(cfg.lineno, 'replace')
    elif line.is_all_opcode_line('delete'):
      s = s.format(cfg.lineno, 'delete')
    elif line.is_all_opcode_line('insert'):
      s = s.format(cfg.lineno, 'insert')
    else:
      s = s.format(cfg.lineno, 'equal')
    cfg.lineno += 1

    for char in line.chars:
      s += self._format_char(char)

    s += '</div></div>'
    return s

  def _format_char(self, char):
    assert char.diff.opcode != 'fill'

    classes = ["opcode-" + char.diff.opcode]
    if char.pyg:
      classes.append('token-' + '-'.join(char.pyg.token_type).lower())
    html_char = char.diff.data
    if html_char == '\n':
      html_char = '<br>'
    elif html_char == ' ':
      html_char = '&nbsp;'
    return '<span class="%s">%s</span>' % (' '.join(classes), html_char)

  def format(self, codiff):
    s = '<div class="container"><div class="row"><div class="col-md-6"><pre>'

    from_cfg = self.Config()
    for char in codiff.get_from_prog():
      s += self._format_line(char, from_cfg)
    s += '</pre></div><div class="col-md-6"><pre>'

    to_cfg = self.Config()
    for char in codiff.get_to_prog():
      s += self._format_line(char, to_cfg)
    s += '</pre></div></div></div>'
    return s

