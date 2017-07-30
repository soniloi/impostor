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

  CLOSERS_TO_OPENERS = {
    ")" : "(",
    "]" : "[",
    "{" : "}",
    "\"" : "\"",
  }

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


  # Make a shallow (ish) copy of a dictionary of lists
  @staticmethod
  def copyListDict(original):

    result = {}

    for pair, successors in original.iteritems():
      successors_copy = list(successors)
      result[pair] = successors_copy

    return result


  # Merge one dictionary of lists into another
  @staticmethod
  def mergeIntoDictionary(mergeinto, mergefrom):

    for key, value_list in mergefrom.iteritems():

      if not key in mergeinto:
        mergeinto[key] = []

      mergeinto[key] += value_list


  @staticmethod
  def appendWithCreate(dictionary, key, value):

    if not key in dictionary:
      dictionary[key] = []

    dictionary[key].append(value)


class Generator:

  SEP = "/"
  SOURCEFILE_EXTLEN = len(config.SOURCEFILE_EXT) # Length of the source file extension
  TERMINATE = None

  def __init__(self, lookback_count=config.LOOKBACK_LEN):
    self.lookback_count = lookback_count


  def build(self, source_dir):
    users = UserCollection()
    self.readSources(source_dir, users)
    users.init(source_dir)
    self.init(users, GeneratorUtil.buildMeta(source_dir))


  def init(self, users, meta, time=int(time.time())):
    self.users = users
    self.meta = meta
    self.date_started = time


  def readSources(self, source_dir, users):

    source_filenames = os.listdir(source_dir)

    for source_filename in source_filenames:

      if source_filename.endswith(config.SOURCEFILE_EXT):

        source_filepath = source_dir + Generator.SEP + source_filename
        infile = open(source_filepath, 'r')
        (nick, starters, generic_lookbacks, closing_lookbacks) = self.processSource(source_filename, infile)
        infile.close()

        # Only add new user to sources if any material actually found in file
        if generic_lookbacks or closing_lookbacks:
          users.addUser(nick, starters, generic_lookbacks, closing_lookbacks)


  def processSource(self, source_filename, source_data):

    nick = source_filename[:-Generator.SOURCEFILE_EXTLEN]
    starters = []
    generic_lookbacks = {}
    closing_lookbacks = {}

    for line in source_data:
      words = line.split()
      if len(words) >= self.lookback_count: # Not interested in lines too short to create productions
        self.processLineWords(words, starters, generic_lookbacks, closing_lookbacks)

    return (nick, starters, generic_lookbacks, closing_lookbacks)


  def processLineWords(self, words, starters, generic_lookbacks, closing_lookbacks):

    starter = tuple(words[0:self.lookback_count])
    starters.append(starter)

    bound = len(words) - self.lookback_count
    for i in range(0, bound):

      follow_index = i + self.lookback_count
      lookback = tuple(words[i:follow_index])
      follow = words[follow_index]

      last = follow[-1]

      if last in GeneratorUtil.CLOSERS_TO_OPENERS:
        opener = GeneratorUtil.CLOSERS_TO_OPENERS[last]

        if not opener in closing_lookbacks:
          closing_lookbacks[opener] = {}

        GeneratorUtil.appendWithCreate(closing_lookbacks[opener], lookback, follow)

      GeneratorUtil.appendWithCreate(generic_lookbacks, lookback, follow)

    last_lookback = tuple(words[bound:])
    last_last = last_lookback[-1]

    if last_last in GeneratorUtil.CLOSERS_TO_OPENERS:
      last_opener = GeneratorUtil.CLOSERS_TO_OPENERS[last_last]

      if not last_opener in closing_lookbacks:
        closing_lookbacks[last_opener] = {}

      if not last_lookback in closing_lookbacks[last_opener]:
        closing_lookbacks[last_opener][last_lookback] = []

      if not Generator.TERMINATE in closing_lookbacks[last_opener][last_lookback]:
        closing_lookbacks[last_opener][last_lookback].append(Generator.TERMINATE)

    if not last_lookback in generic_lookbacks:
        generic_lookbacks[last_lookback] = []

    if not Generator.TERMINATE in generic_lookbacks[last_lookback]:
        generic_lookbacks[last_lookback].append(Generator.TERMINATE)


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


  # Return a line generated from a given lookback collection and a given initial pair
  def generateQuote(self, lookbacks, initial):

    current = initial
    line = ' '.join(current[0:self.lookback_count])

    # FIXME: this should not be possible; maybe do something else here?
    if not current in lookbacks:
      return line

    i = 0
    follow = random.choice(lookbacks[current])
    while current in lookbacks and i < config.OUTPUT_WORDS_MAX and follow != Generator.TERMINATE:
      line += ' ' + follow

      current_list = list(current[1:self.lookback_count])
      current_list.append(follow)
      current = tuple(current_list)
      i += 1
      follow = random.choice(lookbacks[current])

    return line


  # Return a line generated from the source of a nick or nicks
  #   if none of those nicks were present, return an empty list and an empty string
  #   if at least some of the nicks were present, return a list of the nicks found and a quote string
  def generate(self, nick_tuples, random_min_starters=0, increment_quote_count=True):

    real_nicks = self.users.getRealNicks(nick_tuples, random_min_starters, increment_quote_count)
    if not real_nicks:
      return ([], "")

    first_nick = real_nicks[0]
    starting_pairs = self.users.getStarters(first_nick)
    lookbacks = self.users.getGenericLookbacks(first_nick)

    # If we have more than one nick, we will be constructing a new lookback map
    #  and starter list, so we will want copies
    if len(real_nicks) > 1:
      starting_pairs = list(starting_pairs)
      lookbacks = GeneratorUtil.copyListDict(lookbacks)

    for other_nick in real_nicks[1:]:
      starting_pairs += list(self.users.getStarters(other_nick))
      GeneratorUtil.mergeIntoDictionary(lookbacks, self.users.getGenericLookbacks(other_nick))

    initial = random.choice(starting_pairs)
    quote = self.generateQuote(lookbacks, initial)
    return (real_nicks, quote)

