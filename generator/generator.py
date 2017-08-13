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


class SpecialToken:
  TERMINATE = 0
  URL = 1


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
  def appendNonTerminalWithCreate(dictionary, key, value):

    if not key in dictionary:
      dictionary[key] = []

    dictionary[key].append(value)


  @staticmethod
  def appendTerminalWithCreate(dictionary, key):

    if not SpecialToken.TERMINATE in dictionary:

      if not key in dictionary:
        dictionary[key] = []

      dictionary[key].append(SpecialToken.TERMINATE)


  @staticmethod
  def isUrl(word):

    # FIXME: get a proper regex
    return word.startswith("http") or word.startswith("www")


  @staticmethod
  # Note: this is not a proper balance checker, since we are not interested in unmatched openers
  def areParenthesesBalanced(word):

    closers = []

    for char in word:

      if closers and char == closers[-1]:
        closers.pop()

      elif char in config.CLOSERS_TO_OPENERS:
        return False

      if char in config.OPENERS_TO_CLOSERS:
        closers.append(config.OPENERS_TO_CLOSERS[char])

    return True


  @staticmethod
  def isParenthesisException(word):

    if word in config.PARENTHESIS_EXCEPTIONS:
      return True

    if not GeneratorUtil.isUrl(word):
      return False

    return GeneratorUtil.areParenthesesBalanced(word)


class Generator:

  SEP = "/"
  SOURCEFILE_EXTLEN = len(config.SOURCEFILE_EXT) # Length of the source file extension

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
        (nick, starters, all_lookbacks, closing_lookbacks, urls) = self.processSource(source_filename, infile)
        infile.close()

        # Only add new user to sources if any material actually found in file
        if all_lookbacks:
          users.addUser(
            nick=nick,
            starters=starters,
            all_lookbacks=all_lookbacks,
            closing_lookbacks=closing_lookbacks,
            urls=urls
          )


  def processSource(self, source_filename, source_data):

    nick = source_filename[:-Generator.SOURCEFILE_EXTLEN]
    starters = []
    all_lookbacks = {}
    closing_lookbacks = {}
    urls = []
    for opener in config.OPENERS_TO_CLOSERS:
      closing_lookbacks[opener] = {}

    for line in source_data:
      words = line.split()
      if len(words) >= self.lookback_count: # Not interested in lines too short to create productions
        self.processLineWords(words, starters, all_lookbacks, closing_lookbacks, urls)

    return (nick, starters, all_lookbacks, closing_lookbacks, urls)


  def processLineWords(self, words, starters, all_lookbacks, closing_lookbacks, urls):

    starter_words = []
    for word in (words[0:self.lookback_count]):
      if GeneratorUtil.isUrl(word):
        urls.append(word)
        starter_words.append(SpecialToken.URL)
      else:
        starter_words.append(word)

    starter = tuple(starter_words)
    starters.append(starter)

    bound = len(words) - self.lookback_count
    for i in range(0, bound):

      follow_index = i + self.lookback_count
      lookback = tuple(words[i:follow_index])
      follow = words[follow_index]

      last_index = Generator.getLastIndexBeforeEndingPunctuation(follow)
      last = follow[last_index]

      # Add some tuples to specific closing pools
      if not GeneratorUtil.isParenthesisException(follow) and last in config.CLOSERS_TO_OPENERS:
        opener = config.CLOSERS_TO_OPENERS[last]
        GeneratorUtil.appendNonTerminalWithCreate(closing_lookbacks[opener], lookback, follow)

      if GeneratorUtil.isUrl(follow):
        urls.append(follow)
        follow = SpecialToken.URL

      # Add all tuples to the generic pool
      GeneratorUtil.appendNonTerminalWithCreate(all_lookbacks, lookback, follow)

    last_lookback = tuple(words[bound:])
    GeneratorUtil.appendTerminalWithCreate(all_lookbacks, last_lookback)


  @staticmethod
  def getLastIndexBeforeEndingPunctuation(word):

    i = len(word) - 1
    while i >= 0 and word[i] in config.WORD_ENDING_PUNCTUATION:
      i -= 1

    return i


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


  @staticmethod
  def substituteIfUrl(token, urls):

    if token != SpecialToken.URL:
      return token

    return random.choice(urls)


  # Return a line generated from a given lookback collection and a given initial pair
  def generateFromInitial(self, all_lookbacks, closing_lookbacks, initial, urls):

    openers = []

    first_word = Generator.substituteIfUrl(initial[0], urls)
    line = Generator.getCleanedWord(first_word, openers)

    for word in initial[1:]:
      word = Generator.substituteIfUrl(word, urls)
      line += ' ' + Generator.getCleanedWord(word, openers)

    # FIXME: this should not be possible; maybe do something else here?
    if not initial in all_lookbacks:
      return line

    line += self.createLine(all_lookbacks, closing_lookbacks, initial, urls, openers)

    # Close any remaining open parentheses
    while openers:
      line += config.OPENERS_TO_CLOSERS[openers.pop()]

    return line


  def createLine(self, all_lookbacks, closing_lookbacks, initial, urls, openers):

    line = ""
    i = self.lookback_count
    follow = ""
    current_tuple = initial

    while current_tuple in all_lookbacks and i < config.OUTPUT_WORDS_MAX and follow != SpecialToken.TERMINATE:

      follow_token = Generator.getFollow(all_lookbacks, closing_lookbacks, current_tuple, openers)
      follow = Generator.substituteIfUrl(follow_token, urls)

      if follow_token != SpecialToken.TERMINATE:
        line += ' ' + Generator.getCleanedWord(follow, openers)

        current_list = list(current_tuple[1:self.lookback_count])
        current_list.append(follow_token)
        current_tuple = tuple(current_list)
        i += 1

    return line


  @staticmethod
  def getFollow(all_lookbacks, closing_lookbacks, current_tuple, openers):

    lookbacks = all_lookbacks

    current_opener = None
    if openers:
      current_opener = openers[-1]

    if current_opener and current_tuple in closing_lookbacks[current_opener]:
        lookbacks = closing_lookbacks[current_opener]

    next_follow = random.choice(lookbacks[current_tuple])

    return next_follow


  @staticmethod
  def getCleanedWord(word, openers):

    Generator.addNewOpeners(word, openers)
    matched_end_index = Generator.removeMatchedOpeners(word, openers)
    cleaned_word = Generator.removeUnmatchedClosers(word, matched_end_index)

    return cleaned_word


  @staticmethod
  def addNewOpeners(word, openers):

    if not word in config.PARENTHESIS_EXCEPTIONS:

      i = 0
      while i < len(word) and word[i] in config.OPENERS_TO_CLOSERS:

        openers.append(word[i])
        i += 1


  @staticmethod
  def removeMatchedOpeners(word, openers):

    i = Generator.getLastIndexBeforeEndingPunctuation(word)
    while i >= 0 and len(openers) > 0 and word[i] == config.OPENERS_TO_CLOSERS[openers[-1]]:

      openers.pop()
      i -= 1

    return i + 1


  @staticmethod
  def removeUnmatchedClosers(word, matched_end_index):

    core_end_index = matched_end_index - 1
    if not word[:matched_end_index] in config.PARENTHESIS_EXCEPTIONS:
      while core_end_index in xrange(0, len(word)) and word[core_end_index] in config.CLOSERS_TO_OPENERS:
        core_end_index -= 1

    return word[:core_end_index+1] + word[matched_end_index:]


  def getTuplesForUser(self, nick):

    starting_pairs = self.users.getStarters(nick)
    all_lookbacks = self.users.getAllLookbacks(nick)
    closing_lookbacks = self.users.getClosingLookbacks(nick)
    urls = self.users.getUrls(nick)

    return (starting_pairs, all_lookbacks, closing_lookbacks, urls)


  @staticmethod
  def copyTuples(starting_pairs, all_lookbacks, closing_lookbacks, urls):

    new_starting_pairs = list(starting_pairs)
    new_all_lookbacks = GeneratorUtil.copyListDict(all_lookbacks)
    new_closing_lookbacks = {}
    for opener in config.OPENERS_TO_CLOSERS:
      new_closing_lookbacks[opener] = GeneratorUtil.copyListDict(closing_lookbacks[opener])
    new_urls = list(urls)

    return (new_starting_pairs, new_all_lookbacks, new_closing_lookbacks, new_urls)


  def mergeAdditionalUserData(self, further_nicks, all_lookbacks, closing_lookbacks, starting_pairs, urls):

    for other_nick in further_nicks:

      (other_starting_pairs, other_all_lookbacks, other_closing_lookbacks, other_urls) = self.getTuplesForUser(other_nick)

      starting_pairs += list(other_starting_pairs)

      GeneratorUtil.mergeIntoDictionary(all_lookbacks, other_all_lookbacks)

      for opener in config.OPENERS_TO_CLOSERS:
        GeneratorUtil.mergeIntoDictionary(closing_lookbacks[opener], other_closing_lookbacks[opener])

      urls += list(other_urls)


  # Get lookback and starting tuples for users known to exist
  def getTuples(self, nicks):

    # Take lookbacks from first user initially
    first_nick = nicks[0]
    (starting_pairs, all_lookbacks, closing_lookbacks, urls) = self.getTuplesForUser(first_nick)

    # If we have more than one nick, we will be constructing new lookback maps
    #  and starter list, so we will want copies
    if len(nicks) > 1:
      (starting_pairs, all_lookbacks, closing_lookbacks, urls) = \
        Generator.copyTuples(starting_pairs, all_lookbacks, closing_lookbacks, urls)
      self.mergeAdditionalUserData(nicks[1:], all_lookbacks, closing_lookbacks, starting_pairs, urls)

    return (all_lookbacks, closing_lookbacks, starting_pairs, urls)


  # Return tuples whose first element matches a given one
  @staticmethod
  def findMatchingTuples(first, tuples):

    matches = []

    for tup in tuples:
      if tup[0] == first:
        matches.append(tup)

    return matches


  def makeInitial(self, lookbacks, starters, given_initial):

    if given_initial:

      if len(given_initial) < self.lookback_count:
        matching_tuples = Generator.findMatchingTuples(given_initial[0], lookbacks)
        if matching_tuples:
          given_initial = random.choice(matching_tuples)

      # If the given given_initial is not present, then a quote cannot be formed from it
      if not given_initial in lookbacks:
        return None

    else:
      given_initial = random.choice(starters)

    return given_initial


  def generate(self, nick_tuples, initial=None, random_min_starters=0, increment_quote_count=True):

    real_nicks = self.users.getRealNicks(nick_tuples, random_min_starters, increment_quote_count)
    if not real_nicks:
      return ([], "")

    (all_lookbacks, closing_lookbacks, starting_pairs, urls) = self.getTuples(real_nicks)

    initial = self.makeInitial(all_lookbacks, starting_pairs, initial)
    if not initial:
      return ([], "")

    quote = self.generateFromInitial(all_lookbacks, closing_lookbacks, initial, urls)

    return (real_nicks, quote)

