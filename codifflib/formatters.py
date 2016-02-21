#!/usr/bin/env python

import sys

# TODO: requires Bootstrap, leave it as is?
class HtmlFormatter(object):
  def _format_line(self, line):
    if line.fillsize:
      return '<div class="line-filler col-md-12"><br></div>' * line.fillsize

    s = '<div class="line-%s col-md-12">'
    if line.is_all_opcode_line('replace'):
      s = s % 'replace'
    elif line.is_all_opcode_line('delete'):
      s = s % 'delete'
    elif line.is_all_opcode_line('insert'):
      s = s % 'insert'
    else:
      s = s % 'equal'

    for char in line.chars:
      s += self._format_char(char)

    s += '</div>'
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

    for char in codiff.get_from_prog():
      s += self._format_line(char)
    s += '</pre></div><div class="col-md-6"><pre>'

    for char in codiff.get_to_prog():
      s += self._format_line(char)
    s += '</pre></div></div></div>'
    return s

