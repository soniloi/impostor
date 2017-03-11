#!/usr/bin/env python

# Per-user Markov generator class

import os
import random
import Config

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

      infilename = srcdir + os.sep + source
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


  # Make a shallow (ish) copy of a dictionary of lists
  def copyListDict(self, original):
    result = {}
    for pair, successors in original.iteritems():
      successors_copy = list(successors)
      result[pair] = successors_copy
    return result


  # Merge one dictionary of lists into another
  def mergeIntoDictionary(self, mergeinto, mergefrom):
    for pair, successors in mergefrom.iteritems():
      if pair in mergeinto:
        mergeinto[pair] += successors
      else:
        mergeinto[pair] = successors


  # Return a line generated from a given lookback collection and a given initial pair
  def generateQuote(self, lookbacks, initial):

    current = initial
    line = current[0] + ' ' + current[1]

    if not current in lookbacks:
      return line

    i = 0
    while current in lookbacks and i < Config.MAX_WORDS:
      next = random.choice(lookbacks[current])
      line += ' ' + next
      current = (current[1], next)
      i += 1

    return line


  # Return a line generated from the source of a nick or nicks
  #   if none of those nicks were present, return an empty list and an empty string
  #   if at least some of the nicks were present, return a list of the nicks found and a quote string
  def generate(self, nick_tuples):

    real_nicks = []
    for nick_tuple in nick_tuples:
      real_nick = nick_tuple[1]
      if nick_tuple[0] == True:
        real_nick = random.choice(self.userlookbacks.keys())
      elif real_nick not in self.userlookbacks or real_nick not in self.starters:
        continue
      real_nicks.append(real_nick)

    if not real_nicks:
      return ([], "")

    if len(real_nicks) == 1:
      return (real_nicks, self.generateSingle(real_nicks[0]))
    else:
      return (real_nicks, self.generateMerged(real_nicks))


  # Return a line appropriate to a given single nick that we know to be present
  def generateSingle(self, nick):
    lookbacks = self.userlookbacks[nick]
    initial = random.choice(self.starters[nick]) # Choose a random starting-point

    return self.generateQuote(lookbacks, initial)


  # Return a line generated from the source of multiple nicks that we know to be all present
  def generateMerged(self, nicks):

    lookbacks = self.copyListDict(self.userlookbacks[nicks[0]])
    starterset = list(self.starters[nicks[0]])

    for nick in nicks[1:]:
      self.mergeIntoDictionary(lookbacks, self.userlookbacks[nick]) # Create a merged map of pairs to successors
      starterset += self.starters[nick] # Create a merged list of possible starting points

    initial = random.choice(starterset)

    return self.generateQuote(lookbacks, initial)
