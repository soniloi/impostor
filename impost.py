#!/usr/bin/env python

import sys
import Margen

QUITCHAR = '#' # The character to break the loop (ideally, one that isn't a valid nick character)
QUANTITY = 24 # How many lines to print each time it is called

def get_input():
  return raw_input('Enter nick, or \'' + QUITCHAR + '\' to exit: ')

def main(srcdir):
  generator = Margen.Margen(srcdir)

  nick = get_input()

  while nick != QUITCHAR:
    for i in range(0, QUANTITY):
      imposting = generator.generate(nick)
      if imposting:
        print '[' + nick + '] ' + imposting
    nick = get_input()

main(sys.argv[1])
