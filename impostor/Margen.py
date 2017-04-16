#!/usr/bin/env python

# Per-user Markov generator class

from collections import namedtuple
import os
import random
import time

import GeneratorConfig


AliasInfo = namedtuple("AliasInfo", "aliases, requested_nick")
NickAndCount = namedtuple("NickAndCount", "nick, count")
SourceChannelNames = namedtuple("SourceChannelNames", "primary, additionals")


class NickType:
  NONRANDOM = 0
  RANDOM = 1


class UserStatisticType:
  REAL_NICK = 0
  ALIASES = 1
  PRODUCTION_COUNT = 2
  QUOTES_REQUESTED = 3


class User:

  def __init__(self, nick, starters, lookbacks):

    self.nick = nick
    self.starters = starters # List of all starting tuples from this user
    self.lookbacks = lookbacks # Map of this user's tuples to follows
    self.production_count = self.countProductions() # This is not going to change after initialization

    self.quotes_requested = 0 # Number of times this user has been requested for a quote
    self.aliases = []


  def countProductions(self):

    production_count = 0

    for (_, production_list) in self.lookbacks.iteritems():
      production_count += len(production_list)

    return production_count


  def getStatistics(self, requested_nick):

    aliases = None
    if self.aliases:
      repeated_nick = None
      if requested_nick != self.nick:
        repeated_nick = requested_nick
      aliases = AliasInfo(tuple(self.aliases), repeated_nick)

    return {
      UserStatisticType.REAL_NICK: self.nick,
      UserStatisticType.ALIASES: aliases,
      UserStatisticType.PRODUCTION_COUNT: self.production_count,
      UserStatisticType.QUOTES_REQUESTED: self.quotes_requested,
    }


class GenericStatisticType:
  USER_COUNT = 0
  DATE_STARTED = 1
  DATE_GENERATED = 2
  SOURCE_CHANNELS = 3
  BIGGEST_USERS = 4
  MOST_QUOTED_USERS = 5


class Margen:

  SOURCEFILE_EXTLEN = len(GeneratorConfig.SOURCEFILE_EXT) # Length of the source file extension

  def __init__(self, source_dir):

    self.usermap = {} # Map of nick to User objects
    self.meta = {}
    self.user_count = 0
    self.biggest_users = None
    self.date_started = int(time.time())

    self.buildSources(source_dir)
    self.userset = set(self.usermap.values())

    self.buildMeta(source_dir)
    self.buildStaticStats() # Need to record these before aliasing is done
    self.buildMergeInfo(source_dir)


  def buildSources(self, source_dir):

    source_filenames = os.listdir(source_dir)
    for source_filename in source_filenames:
      if source_filename.endswith(GeneratorConfig.SOURCEFILE_EXT):
        self.buildSource(source_dir, source_filename)


  def buildSource(self, source_dir, source_filename):

    nick = source_filename[:-Margen.SOURCEFILE_EXTLEN]
    starters = []
    lookbackmap = {}

    source_filepath = source_dir + os.sep + source_filename
    self.processSourceFile(source_filepath, nick, starters, lookbackmap)

    # Only add nick to sources if any material actually found in file
    if lookbackmap:
      self.usermap[nick] = User(nick, starters, lookbackmap)


  def processSourceFile(self, filepath, nick, starters, lookbackmap):

    infile = open(filepath, 'r')

    for line in infile:
      words = line.split()
      if len(words) >= (GeneratorConfig.LOOKBACK_LEN + 1): # Not interested in lines too short to create productions
        self.processLineWords(words, nick, starters, lookbackmap)

    infile.close()


  def processLineWords(self, words, nick, starters, lookbackmap):

    starter = (words[0], words[1])
    starters.append(starter)

    bound = len(words) - GeneratorConfig.LOOKBACK_LEN
    for i in range(0, bound):

      first = words[i]
      second = words[i+1]
      follow = words[i+2]
      lookback = (first, second)

      if not lookback in lookbackmap:
        lookbackmap[lookback] = []

      lookbackmap[lookback].append(follow)


  def buildMeta(self, source_dir):

    meta_filename = source_dir + GeneratorConfig.META_FILE_NAME
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


  # Assemble any counts etc. that will not change after startup
  def buildStaticStats(self):

    self.user_count = len(self.usermap)

    users_ordered = sorted(self.userset, key=lambda x:x.production_count, reverse=True)
    biggest_users = []
    for user in users_ordered[:GeneratorConfig.BIGGEST_USERS_COUNT]:
      big_user = NickAndCount(user.nick, user.production_count)
      biggest_users.append(big_user)
    self.biggest_users = tuple(biggest_users)


  def buildMergeInfo(self, source_dir):

    mergeinfo_filename = source_dir + GeneratorConfig.MERGEINFO_FILE_NAME
    if not os.path.isfile(mergeinfo_filename):
      return

    mergeinfo_file = open(mergeinfo_filename, 'r')

    for mergeinfo_line in mergeinfo_file:

      mergeinfo_words = mergeinfo_line.strip().split()
      if len(mergeinfo_words) < 2:
        continue

      primary = mergeinfo_words[0]
      if not primary in self.usermap:
        continue

      secondaries = mergeinfo_words[1:]

      user = self.usermap[primary]
      user.aliases = secondaries

      for alias in secondaries:
        self.usermap[alias] = user

    mergeinfo_file.close()


  @staticmethod
  def getFirstOrNone(lis):
    if not lis:
      return None
    return lis[0]


  def empty(self):
    return not self.usermap


  # Return a tuple consisting of a user's aliases, or None if the user does not exist
  def getUserAliases(self, nick):
    if nick in self.usermap:
      return tuple(self.usermap[nick].aliases)
    return tuple()


  # Return a tuple consisting of generic statistics
  def getGenericStatistics(self):

    channel_primary = Margen.getFirstOrNone(self.meta.get(GeneratorConfig.META_PRIMARY))
    channel_additionals = tuple()
    if GeneratorConfig.META_ADDITIONAL in self.meta:
      channel_additionals = tuple(self.meta[GeneratorConfig.META_ADDITIONAL])

    return {
      GenericStatisticType.USER_COUNT: self.user_count,
      GenericStatisticType.DATE_STARTED: self.date_started,
      GenericStatisticType.DATE_GENERATED: Margen.getFirstOrNone(self.meta.get(GeneratorConfig.META_DATE)),
      GenericStatisticType.SOURCE_CHANNELS: SourceChannelNames(channel_primary, channel_additionals),
      GenericStatisticType.BIGGEST_USERS: self.biggest_users,
      GenericStatisticType.MOST_QUOTED_USERS: self.getMostQuoted()
    }


  def getMostQuoted(self):

    most_quoted_list = sorted(self.userset, key=lambda x:x.quotes_requested, reverse=True)[:GeneratorConfig.MOST_QUOTED_COUNT]
    most_quoted_tuples = []

    for user in most_quoted_list:
      quoted_user = NickAndCount(user.nick, user.quotes_requested)
      if user.quotes_requested > 0:
        most_quoted_tuples.append(quoted_user)

    return tuple(most_quoted_tuples)


  # Return a tuple consisting of a user's statistics, or None if the user does not exist
  def getUserStatistics(self, nick):
    if not nick in self.usermap:
      return None
    return self.usermap[nick].getStatistics(nick)


  # Return a nick at random, as long as it has at least a certain number of starter entries,
  #  and is not one of a list of excludes (such as to prevent duplicates from occurring)
  def getRandomNick(self, excludes, min_starters=0):

    possibles = []
    for user in self.userset:
      if not user.nick in excludes and len(user.starters) > min_starters:
        possibles.append(user.nick)

    if possibles:
      return random.choice(possibles)

    return None


  # Filter a list of raw nick tuples; random placeholders will be substituted, while
  #  non-random ones will be checked to see if they actually exist
  # Return a list of strings, which may be empty
  def getRealNicks(self, nick_tuples, random_min_starters=0):

    real_nicks = set()

    for nick_tuple in nick_tuples:

      real_alias = nick_tuple[1]

      # Expand any randoms to real nicks
      if nick_tuple[0] == NickType.RANDOM:
        real_alias = self.getRandomNick(real_nicks, random_min_starters)

      # Catch any Nones or empties
      if real_alias and real_alias in self.usermap:

        # Only increment this if the user was directly requested
        if nick_tuple[0] == NickType.NONRANDOM:
          self.usermap[real_alias].quotes_requested += 1

        real_nick = self.usermap[real_alias].nick
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
    while current in lookbacks and i < GeneratorConfig.OUTPUT_WORDS_MAX:
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
    first_user = self.usermap[first_nick]
    starting_pairs = first_user.starters
    lookbacks = first_user.lookbacks

    # If we have more than one nick, we will be constructing a new lookback map
    #  and starter list, so we will want copies
    if len(real_nicks) > 1:
      starting_pairs = list(starting_pairs)
      lookbacks = self.copyListDict(lookbacks)

    for other_nick in real_nicks[1:]:
      other_user = self.usermap[other_nick]
      starting_pairs += other_user.starters
      self.mergeIntoDictionary(lookbacks, other_user.lookbacks)

    initial = random.choice(starting_pairs)
    return (real_nicks, self.generateQuote(lookbacks, initial))

