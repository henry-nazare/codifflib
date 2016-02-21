#!/usr/bin/env bash

import os
import sys

from codifflib import Codiff
from codifflib.formatters import HtmlFormatter

from pygments.styles import get_style_by_name

def build_html():
  if len(sys.argv) != 4:
    sys.stderr.write('Error: requires two files and one style\n')
    sys.exit(1)

  from_file, to_file, style_name = sys.argv[1:]

  # Fetch the template HTML file.
  dir = os.path.dirname(os.path.abspath(__file__))
  template_file = os.path.join(dir, 'diff2html_template.html')
  with open(template_file) as file:
    template = file.read()

  codiff = Codiff.from_files(from_file, to_file)
  body = HtmlFormatter().format(codiff)

  # Color the tokens based on a given Pygments style.
  # TODO: maybe generate separate CSS files?
  style = get_style_by_name(style_name)
  if not style:
    sys.stdout.write('Error: invalid style: ' + style_name)
    sys.exit(1)

  css = ''
  for ttype, tstyle in style:
    color = tstyle['color']
    css += '    .token-' + '-'.join(ttype).lower() + ' { '

    color = tstyle['color']
    if color:
      css += 'color: #' + color + '; '

    bold = tstyle['bold']
    if bold:
      css += 'font-weight: bold; '

    css += '}\n'

  return template % (css, body)

if __name__ == '__main__':
  print build_html()

