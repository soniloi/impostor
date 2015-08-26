#!/usr/bin/env python

# For testing the back-end without the bot

import sys
import Margen

QUITCHAR = '#' # The character to break the loop (ideally, one that isn't a valid nick character)
QUANTITY = 24 # How many lines to print each time it is called
RANDNICK = '@random' # String to use to request a random nick
MERGECHAR = '>' # Character to indicate that this line will request a merged line

def get_input():
  return raw_input('Enter <nick> for single user, \'' + RANDNICK + '\' for a random line, \'' + MERGECHAR + ' <nicks, space-separated>\' for a merged line, or \'' + QUITCHAR + '\' to exit: ')

def main(srcdir):
  generator = Margen.Margen(srcdir)

  request = get_input()

  while request != QUITCHAR:

    for i in range(0, QUANTITY):

      if request.startswith(MERGECHAR):
        nicks = request[1:].split()
        usednicks, imposting = generator.generateMerged(nicks)
        if imposting:
          sys.stdout.write('[' + usednicks[0])
          for nick in usednicks[1:]:
            sys.stdout.write(':' + nick.strip())
          print '] ' + imposting

      else:
        if request == RANDNICK:
          nick, imposting = generator.generateRandom()
        else:
          nick = request
          imposting = generator.generateSingle(request)

        if imposting:
          print '[' + nick + '] ' + imposting

    request = get_input()

main(sys.argv[1])
