#!/usr/bin/env python

# Per-user Markov generator class

import os
import random
import Config


class NickType:
  NONRANDOM = 0
  RANDOM = 1


class Margen:

  SOURCEFILE_EXTLEN = len(Config.SOURCEFILE_EXT) # Length of the source file extension

  def __init__(self, source_dir):

    self.userlookbacks = {} # Map of each nick to their own markov map
    self.starters = {} # Map of each nick to a list of all tuples they use to start lines
    self.buildSources(source_dir)


  def buildSources(self, source_dir):

    source_filenames = os.listdir(source_dir)
    for source_filename in source_filenames:
      if source_filename.endswith(Config.SOURCEFILE_EXT):
        self.buildSource(source_dir, source_filename)


  def buildSource(self, source_dir, source_filename):

    nick = source_filename[:-Margen.SOURCEFILE_EXTLEN]
    starters = []
    lookbackmap = {}

    source_filepath = source_dir + os.sep + source_filename
    self.processSourceFile(source_filepath, nick, starters, lookbackmap)

    # Only add nick to sources if any material actually found in file
    if lookbackmap:
      self.starters[nick] = starters
      self.userlookbacks[nick] = lookbackmap


  def processSourceFile(self, filepath, nick, starters, lookbackmap):

    infile = open(filepath, 'r')

    for line in infile:
      words = line.split()
      self.processLineWords(words, nick, starters, lookbackmap)

    infile.close()


  def processLineWords(self, words, nick, starters, lookbackmap):

    starter = (words[0], words[1])
    starters.append(starter)

    bound = len(words) - Config.LOOKBACK_LEN
    for i in range(0, bound):

      first = words[i]
      second = words[i+1]
      follow = words[i+2]
      lookback = (first, second)

      if not lookback in lookbackmap:
        lookbackmap[lookback] = []

      lookbackmap[lookback].append(follow)


  # Return a nick at random, as long as it has at least a certain number of starter entries,
  #  and is not one of a list of excludes (such as to prevent duplicates from occurring)
  def getRandomNick(self, excludes, min_starters=0):

    possibles = []
    for (nick, starters) in self.starters.iteritems():
      if not nick in excludes and len(starters) > min_starters:
        possibles.append(nick)

    if possibles:
      return random.choice(possibles)

    return None


  # Filter a list of raw nick tuples; random placeholders will be substituted, while
  #  non-random ones will be checked to see if they actually exist
  # Return a list of strings, which may be empty
  def getRealNicks(self, nick_tuples, random_min_starters=0):

    real_nicks = []

    for nick_tuple in nick_tuples:

      real_nick = nick_tuple[1]

      # Expand any randoms to real nicks
      if nick_tuple[0] == NickType.RANDOM:
        real_nick = self.getRandomNick(real_nicks, random_min_starters)

      # Catch any Nones or empties
      if real_nick and real_nick in self.starters:
        real_nicks.append(real_nick)

    return real_nicks


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
    while current in lookbacks and i < Config.OUTPUT_WORDS_MAX:
      next = random.choice(lookbacks[current])
      line += ' ' + next
      current = (current[1], next)
      i += 1

    return line


  # Return a line generated from the source of a nick or nicks
  #   if none of those nicks were present, return an empty list and an empty string
  #   if at least some of the nicks were present, return a list of the nicks found and a quote string
  def generate(self, nick_tuples, random_min_starters=0):

    real_nicks = self.getRealNicks(nick_tuples, random_min_starters)
    if not real_nicks:
      return ([], "")

    first_nick = real_nicks[0]
    starting_pairs = self.starters[first_nick]
    lookbacks = self.userlookbacks[first_nick]

    # If we have more than one nick, we will be constructing a new lookback map
    #  and starter list, so we will want copies
    if len(real_nicks) > 1:
      starting_pairs = list(starting_pairs)
      lookbacks = self.copyListDict(lookbacks)

    for other_nick in real_nicks[1:]:
      starting_pairs += self.starters[other_nick]
      self.mergeIntoDictionary(lookbacks, self.userlookbacks[other_nick])

    initial = random.choice(starting_pairs)
    return (real_nicks, self.generateQuote(lookbacks, initial))

