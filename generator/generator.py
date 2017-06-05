# Per-user Markov generator class

from collections import namedtuple
import os
import random
import time

import config
from users import User
from users import UserCollection

SourceChannelNames = namedtuple("SourceChannelNames", "primary, additionals")


class GenericStatisticType:
  USER_COUNT = 0
  DATE_STARTED = 1
  DATE_GENERATED = 2
  SOURCE_CHANNELS = 3
  BIGGEST_USERS = 4
  MOST_QUOTED_USERS = 5


class GeneratorUtil:

  @staticmethod
  def buildMeta(source_dir):

    meta = {}

    meta_filename = source_dir + config.META_FILE_NAME
    if not os.path.isfile(meta_filename):
      return

    meta_file = open(meta_filename, 'r')

    for meta_line in meta_file:

      meta_words = meta_line.strip().split("=")
      if len(meta_words) != 2:
        continue

      meta_key = meta_words[0]
      meta_values = meta_words[1].split()
      meta[meta_key] = meta_values

    meta_file.close()

    return meta


class Generator:

  def build(self, source_dir, users=UserCollection()):
    users.init(source_dir)
    self.init(users, GeneratorUtil.buildMeta(source_dir))


  def init(self, users, meta, time=int(time.time())):
    self.users = users
    self.meta = meta
    self.date_started = time


  @staticmethod
  def getFirstOrNone(lis):
    if not lis:
      return None
    return lis[0]


  def empty(self):
    return self.users.empty()


  def getUserAliases(self, nick):
    return self.users.getUserAliases(nick)


  # Return a tuple consisting of generic statistics
  def getGenericStatistics(self):

    channel_primary = Generator.getFirstOrNone(self.meta.get(config.META_PRIMARY))
    channel_additionals = tuple()
    if config.META_ADDITIONAL in self.meta:
      channel_additionals = tuple(self.meta[config.META_ADDITIONAL])

    return {
      GenericStatisticType.USER_COUNT: self.users.countUsers(),
      GenericStatisticType.DATE_STARTED: self.date_started,
      GenericStatisticType.DATE_GENERATED: Generator.getFirstOrNone(self.meta.get(config.META_DATE)),
      GenericStatisticType.SOURCE_CHANNELS: SourceChannelNames(channel_primary, channel_additionals),
      GenericStatisticType.BIGGEST_USERS: self.users.getBiggestUsers(),
      GenericStatisticType.MOST_QUOTED_USERS: self.users.getMostQuoted()
    }


  def getUserStatistics(self, nick):
    return self.users.getUserStatistics(nick)


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
    while current in lookbacks and i < config.OUTPUT_WORDS_MAX:
      next = random.choice(lookbacks[current])
      line += ' ' + next
      current = (current[1], next)
      i += 1

    return line


  # Return a line generated from the source of a nick or nicks
  #   if none of those nicks were present, return an empty list and an empty string
  #   if at least some of the nicks were present, return a list of the nicks found and a quote string
  def generate(self, nick_tuples, random_min_starters=0, increment_quote_count=True):

    real_nicks = self.users.getRealNicks(nick_tuples, random_min_starters, increment_quote_count)
    if not real_nicks:
      return ([], "")

    first_nick = real_nicks[0]
    first_user = self.users.getByAlias(first_nick)
    starting_pairs = first_user.starters
    lookbacks = first_user.lookbacks

    # If we have more than one nick, we will be constructing a new lookback map
    #  and starter list, so we will want copies
    if len(real_nicks) > 1:
      starting_pairs = list(starting_pairs)
      lookbacks = self.copyListDict(lookbacks)

    for other_nick in real_nicks[1:]:
      other_user = self.users.getByAlias(other_nick)
      starting_pairs += other_user.starters
      self.mergeIntoDictionary(lookbacks, other_user.lookbacks)

    initial = random.choice(starting_pairs)
    return (real_nicks, self.generateQuote(lookbacks, initial))

