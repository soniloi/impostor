#!/usr/bin/env python

# Per-user Markov generator class

import os
import random

MAX_WORDS = 200 # The maximum number of words to generate in a line, just to prevent infinite strings

class Margen:

  srcextlen = 4 # Length of the source file extension
  lookbacklen = 2

  # Initialize generators
  def __init__(self, srcdir):

    self.userlookbacks = {} # Map of each nick to their own markov map
    self.starters = {} # Map of each nick to a list of all tuples they use to start lines

    sources = os.listdir(srcdir)

    for source in sources:
      nick = source[:-Margen.srcextlen]

      if not nick in self.userlookbacks:
        self.userlookbacks[nick] = {}

      if not nick in self.starters:
        self.starters[nick] = []

      lookbackmap = self.userlookbacks[nick]

      infilename = srcdir + source
      infile = open(infilename, 'r')

      for line in infile:
        words = line.split()

        starter = (words[0], words[1])
        self.starters[nick].append(starter)

        bound = len(words) - Margen.lookbacklen
        for i in range(0, bound):
          first = words[i]
          second = words[i+1]
          follow = words[i+2]
          lookback = (first, second)
          if not lookback in lookbackmap:
            lookbackmap[lookback] = []
          lookbackmap[lookback].append(follow)

      infile.close()

  # Return a line appropriate to a given nick; if nick not present, return empty string
  def generate(self, nick):

    if nick not in self.userlookbacks or nick not in self.starters:
      return ''

    current = random.choice(self.starters[nick]) # Choose a random starting-point
    lookbacks = self.userlookbacks[nick]

    line = current[0] + ' ' + current[1]

    if not current in lookbacks:
      return line

    i = 0
    while current in lookbacks and i < MAX_WORDS:
      next = random.choice(lookbacks[current])
      line += ' ' + next
      current = (current[1], next)
      i += 1

    return line
