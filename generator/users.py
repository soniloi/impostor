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
    self.aliases = set()


  def countProductions(self):

    production_count = 0

    for (_, production_list) in self.lookbacks.iteritems():
      production_count += len(production_list)

    return production_count


  def setPersistedStatistics(self, stats):
    self.quotes_requested = stats.quotes_requested


  def initAliases(self, aliases):
    self.aliases = set(aliases)


  def getStarters(self):
    return tuple(self.starters)


  def getLookbacks(self):
    return self.lookbacks # FIXME: maybe return this immutable somehow


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

    self.readSources(source_dir)
    self.initUserset()
    self.buildStaticStats()
    self.readMergeInfo(source_dir)
    self.readUserStats()


  def readSources(self, source_dir):

    source_filenames = os.listdir(source_dir)

    for source_filename in source_filenames:

      if source_filename.endswith(config.SOURCEFILE_EXT):

        source_filepath = source_dir + UserCollection.SEP + source_filename
        infile = open(source_filepath, 'r')
        self.buildSource(source_filename, infile)
        infile.close()


  def buildSource(self, source_filename, source_data):

    nick = source_filename[:-UserCollection.SOURCEFILE_EXTLEN]
    starters = []
    lookbackmap = {}

    for line in source_data:
      words = line.split()
      if len(words) >= (config.LOOKBACK_LEN + 1): # Not interested in lines too short to create productions
        self.processLineWords(words, starters, lookbackmap)

    # Only add nick to sources if any material actually found in file
    if lookbackmap:
      self.usermap[nick] = User(nick, starters, lookbackmap)


  def processLineWords(self, words, starters, lookbackmap):

    lookback_count = config.LOOKBACK_LEN

    starter = tuple(words[0:lookback_count])
    starters.append(starter)

    bound = len(words) - lookback_count
    for i in range(0, bound):

      follow_index = i + lookback_count
      lookback = tuple(words[i:follow_index])
      follow = words[follow_index]

      if not lookback in lookbackmap:
        lookbackmap[lookback] = []

      lookbackmap[lookback].append(follow)


  def initUserset(self):
    self.userset = set(self.usermap.values())


  # Assemble any counts etc. that will not change after startup
  def buildStaticStats(self):

    self.count = len(self.userset)

    users_ordered = sorted(self.userset, key=lambda x:x.production_count, reverse=True)
    biggest_users = []
    for user in users_ordered[:config.BIGGEST_USERS_COUNT]:
      big_user = NickAndCount(user.nick, user.production_count)
      biggest_users.append(big_user)
    self.biggest_users = tuple(biggest_users)


  def readMergeInfo(self, source_dir):

    mergeinfo_filename = source_dir + config.MERGEINFO_FILE_NAME
    if not os.path.isfile(mergeinfo_filename):
      return

    mergeinfo_file = open(mergeinfo_filename, 'r')
    self.buildMergeInfo(mergeinfo_file)
    mergeinfo_file.close()


  def buildMergeInfo(self, mergeinfo_data):

    for mergeinfo_line in mergeinfo_data:

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


  def readUserStats(self):

    filename = config.STATS_FILE_NAME

    if not os.path.isfile(filename):
      return

    user_stats_file = open(filename, "rb")

    try:

      data = pickle.load(user_stats_file)
      self.buildUserStats(data)

    except:
      print "Error reading or parsing user stats file %s. Generator will start, but previous stats may not be correctly loaded. " \
             % filename

    user_stats_file.close()


  def buildUserStats(self, data):

    for (nick, stats) in data.iteritems():
      if nick in self.usermap:
        self.usermap[nick].setPersistedStatistics(stats)


  def empty(self):
    return not self.usermap


  def containsByAlias(self, nick):
    return nick in self.usermap


  # Get user object from alias or real nick, when known to be in the set
  def getByAlias(self, nick):
    return self.usermap[nick]


  # Get starters for a nick we know to be in the map
  def getStarters(self, nick):
    return self.usermap[nick].getStarters()


  # Get lookbacks for a nick we know to be in the map
  def getLookbacks(self, nick):
    return self.usermap[nick].getLookbacks()


  def countUsers(self):
    return self.count # For now, users cannot be reloaded, so this number is cached


  def getBiggestUsers(self):
    return self.biggest_users # Again, this is cached as it will not change after initialization


  def getMostQuoted(self):

    if not self.userset:
      return tuple()

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
      if not user.nick in excludes and len(user.starters) >= min_starters:
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

