from collections import namedtuple
import os
import pickle
import random

import config


AliasInfo = namedtuple("AliasInfo", "aliases, requested_nick")
NickAndCount = namedtuple("NickAndCount", "nick, count")
UserStatsToPersist = namedtuple("UserStatsToPersist", "quotes_requested");


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
    self.aliases = None


  def countProductions(self):

    production_count = 0

    for (_, production_list) in self.lookbacks.iteritems():
      production_count += len(production_list)

    return production_count


  def setPersistedStatistics(self, stats):
    self.quotes_requested = stats.quotes_requested


  def initAliases(self, aliases):
    self.aliases = set(aliases)


  def incrementQuotesRequested(self):
    self.quotes_requested += 1


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


  def getStatisticsToPersist(self):
    return UserStatsToPersist(self.quotes_requested)


class UserCollection:

  SEP = "/"
  SOURCEFILE_EXTLEN = len(config.SOURCEFILE_EXT) # Length of the source file extension

  def __init__(self):

    self.usermap = {} # Map of nick to User objects
    self.count = 0
    self.biggest_users = None
    self.userset = None
    self.changes = 0


  def init(self, source_dir):

    self.buildSources(source_dir)
    self.userset = set(self.usermap.values())
    self.buildStaticStats()
    self.buildMergeInfo(source_dir)
    self.loadUserStats()


  def buildSources(self, source_dir):

    source_filenames = os.listdir(source_dir)
    for source_filename in source_filenames:
      if source_filename.endswith(config.SOURCEFILE_EXT):
        self.buildSource(source_dir, source_filename)


  def buildSource(self, base_dir, source_filename):

    nick = source_filename[:-UserCollection.SOURCEFILE_EXTLEN]
    starters = []
    lookbackmap = {}

    source_filepath = base_dir + UserCollection.SEP + source_filename
    infile = open(source_filepath, 'r')
    self.processSourceMaterial(infile, nick, starters, lookbackmap)
    infile.close()


  def processSourceMaterial(self, source_material, nick, starters, lookbackmap):

    for line in source_material:
      words = line.split()
      if len(words) >= (config.LOOKBACK_LEN + 1): # Not interested in lines too short to create productions
        self.processLineWords(words, nick, starters, lookbackmap)

    # Only add nick to sources if any material actually found in file
    if lookbackmap:
      self.usermap[nick] = User(nick, starters, lookbackmap)


  def processLineWords(self, words, nick, starters, lookbackmap):

    starter = (words[0], words[1])
    starters.append(starter)

    bound = len(words) - config.LOOKBACK_LEN
    for i in range(0, bound):

      first = words[i]
      second = words[i+1]
      follow = words[i+2]
      lookback = (first, second)

      if not lookback in lookbackmap:
        lookbackmap[lookback] = []

      lookbackmap[lookback].append(follow)


  # Assemble any counts etc. that will not change after startup
  def buildStaticStats(self):

    self.count = len(self.usermap)

    users_ordered = sorted(self.userset, key=lambda x:x.production_count, reverse=True)
    biggest_users = []
    for user in users_ordered[:config.BIGGEST_USERS_COUNT]:
      big_user = NickAndCount(user.nick, user.production_count)
      biggest_users.append(big_user)
    self.biggest_users = tuple(biggest_users)


  def buildMergeInfo(self, source_dir):

    mergeinfo_filename = source_dir + config.MERGEINFO_FILE_NAME
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
      user.initAliases(secondaries)

      for alias in secondaries:
        self.usermap[alias] = user

    mergeinfo_file.close()


  def loadUserStats(self):

    filename = config.STATS_FILE_NAME

    if not os.path.isfile(filename):
      return

    try:
      data = pickle.load(open(filename, "rb"))

      for (nick, stats) in data.iteritems():
        if nick in self.usermap:
          self.usermap[nick].setPersistedStatistics(stats)

    except:
      print "Error reading or parsing user stats file %s. Generator will start, but previous stats may not be correctly loaded. " \
             % filename


  def empty(self):
    return not self.usermap


  # Get user object from alias or real nick, when known to be in the set
  def getByAlias(self, nick):
    return self.usermap[nick]


  def countUsers(self):
    return self.count # For now, users cannot be reloaded, so this number is cached


  def getBiggestUsers(self):
    return self.biggest_users # Again, this is cached as it will not change after initialization


  def getMostQuoted(self):

    most_quoted_list = sorted(self.userset, key=lambda x:x.quotes_requested, reverse=True)[:config.MOST_QUOTED_COUNT]
    most_quoted_tuples = []

    for user in most_quoted_list:
      quoted_user = NickAndCount(user.nick, user.quotes_requested)
      if user.quotes_requested > 0:
        most_quoted_tuples.append(quoted_user)

    return tuple(most_quoted_tuples)


  # Return a tuple consisting of a user's aliases, or an empty tuple if the user does not exist
  def getUserAliases(self, nick):
    if nick in self.usermap:
      return tuple(self.usermap[nick].aliases)
    return tuple()


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
  def getRealNicks(self, nick_tuples, random_min_starters=0, increment_quote_count=True):

    real_nicks = set()

    for nick_tuple in nick_tuples:

      real_alias = nick_tuple[1]

      # Expand any randoms to real nicks
      if nick_tuple[0] == NickType.RANDOM:
        real_alias = self.getRandomNick(real_nicks, random_min_starters)

      # Catch any Nones or empties
      if real_alias and real_alias in self.usermap:

        # Only increment this if the user was directly requested
        if increment_quote_count and nick_tuple[0] != NickType.RANDOM:
          self.usermap[real_alias].incrementQuotesRequested()
          self.updateChanges()

        real_nick = self.usermap[real_alias].nick
        real_nicks.add(real_nick)

    return list(real_nicks)


  # Return a tuple consisting of a user's statistics, or None if the user does not exist
  def getUserStatistics(self, nick):
    if not nick in self.usermap:
      return None
    return self.usermap[nick].getStatistics(nick)


  def updateChanges(self):
    self.changes += 1
    if self.changes >= config.CHANGES_BETWEEN_STATS_PERSISTENCE:
      self.writeOut()
      self.changes = 0


  def writeOut(self):
    data = {}
    for user in self.userset:
      data[user.nick] = user.getStatisticsToPersist()
    pickle.dump(data, open(config.STATS_FILE_NAME, "wb"))

