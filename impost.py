#!/usr/bin/env python

import sys
import Margen

QUITCHAR = '#'

def get_input():
  return raw_input('Enter nick, or ' + QUITCHAR + ' to exit: ')

def main(srcdir):
  generator = Margen.Margen(srcdir)

  nick = get_input()

  while nick != QUITCHAR:
    for i in range(0, 24):
      imposting = generator.generate(nick)
      print '[' + nick + '] ' + imposting
    nick = get_input()

main(sys.argv[1])
