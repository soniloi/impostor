#!/usr/bin/env python

import sys
import Margen

QUITCHAR = '#' # The character to break the loop (ideally, one that isn't a valid nick character)
QUANTITY = 24 # How many lines to print each time it is called
RANDNICK = '@random' # String to use to request a random nick

def get_input():
  return raw_input('Enter nick, or \'' + QUITCHAR + '\' to exit: ')

def main(srcdir):
  generator = Margen.Margen(srcdir)

  request = get_input()

  while request != QUITCHAR:

    for i in range(0, QUANTITY):

      if request == RANDNICK:
        nick, imposting = generator.generateRandom()
      else:
        nick = request
        imposting = generator.generateSingle(request)

      if imposting:
        print '[' + nick + '] ' + imposting

    request = get_input()

main(sys.argv[1])
