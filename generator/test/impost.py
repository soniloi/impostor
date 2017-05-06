#!/usr/bin/env python

# For testing the back-end without the bot

import sys
sys.path.append(".")
from impostor import Margen

QUITCHAR = '#' # The character to break the loop (ideally, one that isn't a valid nick character)
QUANTITY = 24 # How many lines to print each time it is called
RANDNICK = 'random' # String to use to request a random nick

def get_input():
  return raw_input('Enter <nick> to generate, including \'' + RANDNICK + '\' for a random user; enter \'' + QUITCHAR + '\' to exit: ')

def main(src_dir):
  generator = Margen.Margen(src_dir)

  request = get_input().strip()

  while request != QUITCHAR:

    if not request:
      continue

    nicks = request.split()[0].split(':')
    nick_tuples = []
    for nick in nicks:
      nick_tuple = (False, nick)
      if nick == RANDNICK:
        nick_tuple = (True, '')
      nick_tuples.append(nick_tuple)

    for i in range(0, QUANTITY):

      output_nicks, output_quote = generator.generate(nick_tuples)
      if output_quote:
        output_message = '[' + output_nicks[0]
        for output_nick in output_nicks[1:]:
          output_message += ':' + output_nick
        output_message += '] ' + output_quote
        print output_message

    request = get_input()

main(sys.argv[1])
