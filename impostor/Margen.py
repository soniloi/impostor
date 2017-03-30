#!/usr/bin/env python

# Per-user Markov generator class

import os
import random
import Config


class NickType:
  NONRANDOM = 0
  RANDOM = 1


class User:

  def __init__(self, starters, lookbacks):

    self.starters = starters # List of all starting tuples from this user
    self.lookbacks = lookbacks # Map of this user's tuples to follows
    self.quotes_requested = 0 # Number of times this user has been requested for a quote
    self.aliases = []


  def countProductions(self):

    production_count = 0

    for (_, production_list) in self.lookbacks.iteritems():
      production_count += len(production_list)

    return production_count


class Margen:

  SOURCEFILE_EXTLEN = len(Config.SOURCEFILE_EXT) # Length of the source file extension

  def __init__(self, source_dir):

    self.users = {} # Map of nick to User objects
    self.meta = {}
    self.buildSources(source_dir)
    self.buildMeta(source_dir)
    self.buildMergeInfo(source_dir)


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
      self.users[nick] = User(starters, lookbackmap)


  def processSourceFile(self, filepath, nick, starters, lookbackmap):

    infile = open(filepath, 'r')

    for line in infile:
      words = line.split()
      if len(words) >= (Config.LOOKBACK_LEN + 1): # Not interested in lines too short to create productions
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


  def buildMeta(self, source_dir):

    meta_filename = source_dir + Config.META_FILE_NAME
    if not os.path.isfile(meta_filename):
      return

    meta_file = open(meta_filename, 'r')

    for meta_line in meta_file:

      meta_words = meta_line.strip().split("=")
      if len(meta_words) != 2:
        continue

      meta_key = meta_words[0]
      meta_values = meta_words[1].split()
      self.meta[meta_key] = meta_values

    meta_file.close()


  def buildMergeInfo(self, source_dir):

    mergeinfo_filename = source_dir + Config.MERGEINFO_FILE_NAME
    if not os.path.isfile(mergeinfo_filename):
      return

    mergeinfo_file = open(mergeinfo_filename, 'r')

    for mergeinfo_line in mergeinfo_file:

      mergeinfo_words = mergeinfo_line.strip().split()
      if len(mergeinfo_words) < 2:
        continue

      primary = mergeinfo_words[0]
      if not primary in self.users:
        continue

      user = self.users[primary]
      user.aliases = mergeinfo_words[1:]

    mergeinfo_file.close()


  @staticmethod
  def getFirstOrNone(lis):
    if not lis:
      return None
    return lis[0]


  def getSourceGeneratedDate(self):
    return Margen.getFirstOrNone(self.meta.get(Config.META_DATE))


  def getPrimarySourceChannel(self):
    return Margen.getFirstOrNone(self.meta.get(Config.META_PRIMARY))


  def getAdditionalSourceChannels(self):
    return self.meta.get(Config.META_ADDITIONAL)


  def empty(self):
    return not self.users


  def getUserCount(self):
    return len(self.users)


  # Return the number of productions a user has, or -1 if the user does not exist
  def getUserProductionCount(self, nick):

    if not nick in self.users:
      return -1

    return self.users[nick].countProductions()


  # Return the number of times a quote has been requested from a user, or -1 if the user does not exist
  def getUserQuotesRequestedCount(self, nick):

    if not nick in self.users:
      return -1

    return self.users[nick].quotes_requested


  # Return a list of other nicks a user is known by, or None if the user does not exist
  def getUserAliases(self, nick):

    if not nick in self.users:
      return None

    return self.users[nick].aliases


  # Return a nick at random, as long as it has at least a certain number of starter entries,
  #  and is not one of a list of excludes (such as to prevent duplicates from occurring)
  def getRandomNick(self, excludes, min_starters=0):

    possibles = []
    for (nick, user) in self.users.iteritems():
      if not nick in excludes and len(user.starters) > min_starters:
        possibles.append(nick)

    if possibles:
      return random.choice(possibles)

    return None


  # Filter a list of raw nick tuples; random placeholders will be substituted, while
  #  non-random ones will be checked to see if they actually exist
  # Return a list of strings, which may be empty
  def getRealNicks(self, nick_tuples, random_min_starters=0):

    real_nicks = set()

    for nick_tuple in nick_tuples:

      real_nick = nick_tuple[1]

      # Expand any randoms to real nicks
      if nick_tuple[0] == NickType.RANDOM:
        real_nick = self.getRandomNick(real_nicks, random_min_starters)

      # Catch any Nones or empties
      if real_nick and real_nick in self.users:

        # Only increment this if the user was directly requested
        if nick_tuple[0] == NickType.NONRANDOM:
          self.users[real_nick].quotes_requested += 1

        real_nicks.add(real_nick)

    return list(real_nicks)


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
    first_user = self.users[first_nick]
    starting_pairs = first_user.starters
    lookbacks = first_user.lookbacks

    # If we have more than one nick, we will be constructing a new lookback map
    #  and starter list, so we will want copies
    if len(real_nicks) > 1:
      starting_pairs = list(starting_pairs)
      lookbacks = self.copyListDict(lookbacks)

    for other_nick in real_nicks[1:]:
      other_user = self.users[other_nick]
      starting_pairs += other_user.starters
      self.mergeIntoDictionary(lookbacks, other_user.lookbacks)

    initial = random.choice(starting_pairs)
    return (real_nicks, self.generateQuote(lookbacks, initial))

