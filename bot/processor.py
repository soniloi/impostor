from collections import namedtuple
import datetime
import logging
import random
import re

import config
from mystery import HintType
from mystery import Mystery
from players import PlayerCollection
from players import PlayerScoreType

from generator import generator
from generator.generator import GenericStatisticType
from generator.users import UserNickType
from generator.users import UserStatisticType


StatisticFormat = namedtuple("StatisticFormat", "function, container")


class Style:
  CLEAR = "\x0f"
  BOLD = "\x02"
  COLOUR = "\x03"


class Colour:
  WHITE = "0"
  BLACK = "1"
  BLUE = "2"
  GREEN = "3"
  RED = "4"
  BROWN = "5"
  PURPLE = "6"
  ORANGE = "7"
  YELLOW = "8"
  LIGHT_GREEN = "9"
  CYAN = "10"
  LIGHT_CYAN = "11"
  LIGHT_BLUE = "12"
  PINK = "13"
  GREY = "14"
  LIGHT_GREY = "15"


class RequestProcessor():

  GENERIC_DATE_FORMAT_STR = "%Y-%m-%d at %H.%M.%S"
  UNKNOWN_START = "[Unknown"
  UNKNOWN_STR = UNKNOWN_START + "]"
  UNKNOWN_OR_NONE_STR = UNKNOWN_START + " or none]"

  BOLD_DEFAULT = Style.BOLD + "%s" + Style.CLEAR

  GENERATE_TRIGGER = Style.BOLD + Style.COLOUR + Colour.YELLOW + config.GENERATE_TRIGGER
  STATS_TRIGGER = Style.BOLD + Style.COLOUR + Colour.GREEN + config.META_TRIGGER
  MYSTERY_TRIGGER = Style.BOLD + Style.COLOUR + Colour.RED + config.META_TRIGGER

  BOT_NICK = BOLD_DEFAULT % config.BOT_NICK
  GENERATE_SINGLE = GENERATE_TRIGGER + "<nick>" + Style.CLEAR
  GENERATE_RANDOM = GENERATE_TRIGGER + config.RANDOM_NICK + Style.CLEAR
  GENERATE_MERGED = GENERATE_TRIGGER + "<nick1>" + config.INPUT_NICKS_SEP + "<nick2>" + Style.CLEAR
  GENERATE_ALL = GENERATE_TRIGGER + config.ALL_NICK + Style.CLEAR

  META_STATS = STATS_TRIGGER + config.META_STATS + Style.CLEAR
  META_STATS_USER = STATS_TRIGGER + config.META_STATS + " <nick>" + Style.CLEAR

  HELP_ABBR_GENERATOR = MYSTERY_TRIGGER + config.META_HELP_PRIMARY + " " + config.META_HELP_GENERATOR + Style.CLEAR
  HELP_ABBR_MYSTERY = MYSTERY_TRIGGER + config.META_HELP_PRIMARY + " " + config.MYSTERY_START + Style.CLEAR
  HELP_ABBR_STATS = MYSTERY_TRIGGER + config.META_HELP_PRIMARY + " " + config.META_STATS + Style.CLEAR
  HELP_ABBR_SCORE = MYSTERY_TRIGGER + config.META_HELP_PRIMARY + " " + config.MYSTERY_SCORE + Style.CLEAR
  HELP_ABBRS = [HELP_ABBR_GENERATOR, HELP_ABBR_MYSTERY, HELP_ABBR_STATS, HELP_ABBR_SCORE]

  MYSTERY_START = MYSTERY_TRIGGER + config.MYSTERY_START + Style.CLEAR
  MYSTERY_GUESS = MYSTERY_TRIGGER + config.MYSTERY_GUESS + " <nick>" + Style.CLEAR
  MYSTERY_HINT = MYSTERY_TRIGGER + config.MYSTERY_HINT + Style.CLEAR
  MYSTERY_SOLVE = MYSTERY_TRIGGER + config.MYSTERY_SOLVE + Style.CLEAR
  MYSTERY_SCORE = MYSTERY_TRIGGER + config.MYSTERY_SCORE + Style.CLEAR
  MYSTERY_SCORE_NICK = MYSTERY_TRIGGER + config.MYSTERY_SCORE + " <player-nick>" + Style.CLEAR

  BOT_DESC_BASIC = BOT_NICK + " is a bot that impersonates people based on their history. Type " \
    + GENERATE_SINGLE + " to see a line generated for a someone. Type " \
    + ", ".join(HELP_ABBRS[:-1]) + ", or " + HELP_ABBRS[-1] \
    + " for help with other commands. See " \
    + config.REPOSITORY + " for (slightly) more information. "

  HELP_GENERATOR = "Type " \
    + GENERATE_SINGLE + " to see a line generated for a single user, " \
    + GENERATE_RANDOM + " for a line generated for a random user, or " \
    + GENERATE_MERGED + " to see a line generated from two users merged. "

  HELP_MYSTERY = "Type " \
    + MYSTERY_START + " to generate a line from a mystery author. Then type " \
    + MYSTERY_GUESS + " to guess the nick of the mystery line's author, " \
    + MYSTERY_HINT + " for a hint, or " \
    + MYSTERY_SOLVE + " to see the solution. "

  HELP_STATS = "Type " \
    + META_STATS + " for basic generic statistics, or " \
    + META_STATS_USER + " for statistics on a specific user. "

  HELP_SCORE = "Type " \
    + MYSTERY_SCORE + " to see some high scores, or " \
    + MYSTERY_SCORE_NICK + " to see the score of a specific player. "

  HELP_SPECIFIC = {
    config.META_HELP_GENERATOR : HELP_GENERATOR,
    config.MYSTERY_START : HELP_MYSTERY,
    config.META_STATS : HELP_STATS,
    config.MYSTERY_SCORE : HELP_SCORE,
  }

  NO_MYSTERY = "There is currently no unsolved mystery. Type %s to start one. " % MYSTERY_START
  MYSTERY_SOLVE_NO_WINNER = "The mystery author was: %s. No-one guessed correctly. "
  MYSTERY_SOLVE_WITH_WINNER = "The mystery author was: %s%s. Congratulations, %s! "

  MYSTERY_HINT_NONE = "I have no further hints to give. "
  MYSTERY_HINT_NICK_CHARACTER = "The mystery author's name contains the character [%s]"
  MYSTERY_HINT_ADDITIONAL_QUOTE = "The mystery author also says: [%s]"

  MYSTERY_DESCRIPTION_QUOTES = "The mystery author says: [%s]. "
  MYSTERY_DESCRIPTION_CHARACTERS = "Their nick contains the character(s) [%s]. "
  MYSTERY_DESCRIPTION_GUESSED = "Nick(s) guessed so far: [%s]. "

  GENERIC_SCORE_MESSAGE_UNKNOWN = "No-one has participated in any games since I started keeping records."
  GENERIC_SCORE_MESSAGE_KNOWN = "The player who has played the most games is %s with %d game(s). " \
                       "The player with the most incorrect guesses is %s with %d. " \
                       "The player with the most correct guesses is %s with %d. "

  PLAYER_SCORE_MESSAGE_KNOWN = "The player %s has participated in %d mystery game(s). The have guessed incorrectly %d time(s) and correctly %d time(s). "
  PLAYER_SCORE_MESSAGE_UNKNOWN = "If there is someone currently called %s, then they have not played since I started keeping records. "

  USER_UNKNOWN = "I know of no such user %s. "

  def __init__(self, source_dir, generator, players):

    self.current_mystery = None
    self.next_mystery_ident = 0

    self.initCommandMap()
    self.initStatisticFormatters()

    self.generator = generator
    self.generator.build(source_dir)
    if self.generator.empty():
      print "Warning: generator is empty; is this correct?"

    self.players = players
    self.players.init()


  def initCommandMap(self):

    self.commands = {
      config.META_STATS: RequestProcessor.makeStats,
      config.MYSTERY_START: RequestProcessor.startMystery,
      config.MYSTERY_GUESS: RequestProcessor.guessMystery,
      config.MYSTERY_HINT: RequestProcessor.hintMystery,
      config.MYSTERY_SOLVE: RequestProcessor.solveMystery,
      config.MYSTERY_SCORE: RequestProcessor.scoreMystery,
    }

    for help_string in config.META_HELP_ALL:
      self.commands[help_string] = RequestProcessor.makeHelp


  def initStatisticFormatters(self):

    self.generic_statistic_formatters = {
      GenericStatisticType.USER_COUNT: StatisticFormat(RequestProcessor.formatGenericUserCount, "I have material from %d users. "),
      GenericStatisticType.DATE_STARTED: StatisticFormat(RequestProcessor.formatGenericDate, "I have been running since %s. "),
      GenericStatisticType.DATE_GENERATED: StatisticFormat(RequestProcessor.formatGenericDate, "My source material was generated on %s. "),
      GenericStatisticType.SOURCE_CHANNELS: StatisticFormat(RequestProcessor.formatGenericChannels, "Its primary source channel was %s, and additional material was drawn from %s. "),
      GenericStatisticType.BIGGEST_USERS: StatisticFormat(RequestProcessor.formatGenericBiggestUsers, "The %d users with the most source material are: %s. "),
      GenericStatisticType.MOST_QUOTED_USERS: StatisticFormat(RequestProcessor.formatGenericMostQuotedUsers, "Since I started keeping records, the user prompted for quotes most often is: %s. "),
    }

    self.user_statistic_formatters = {
      UserStatisticType.REAL_NICK: StatisticFormat(RequestProcessor.formatUserRealNick, "The user %s "),
      UserStatisticType.ALIASES: StatisticFormat(RequestProcessor.formatUserAliases, "(AKA %s) "),
      UserStatisticType.PRODUCTION_COUNT: StatisticFormat(RequestProcessor.formatUserSimpleCount, "has %d production(s). "),
      UserStatisticType.QUOTES_REQUESTED: StatisticFormat(RequestProcessor.formatUserSimpleCount, "%d quote(s) have been requested of them. "),
    }


  def updateNick(self, old_nick, new_nick):
    logging.info("Nick change detected: [%s] -> [%s]", old_nick, new_nick)
    self.players.updateNick(old_nick, new_nick)


  def makeHelp(self, user, raw_tokens):

    specifics = raw_tokens[1:]
    output_messages = []

    if not specifics:
      output_messages.append(self.makeGenericHelp())

    else:
      specific_help = self.makeSpecificHelp(specifics[0])
      if specific_help:
        output_messages.append(specific_help)

    return output_messages


  def makeGenericHelp(self):
    return RequestProcessor.BOT_DESC_BASIC


  def makeSpecificHelp(self, query):
    return RequestProcessor.HELP_SPECIFIC.get(query)


  @staticmethod
  def mkCasedMessage(message_raw):

    message_words = message_raw.strip().split(" ", 1)

    non_cased_part = message_words[0].lower()

    cased_part = ""
    if len(message_words) > 1:
      cased_part = " " + message_words[1]

    return non_cased_part + cased_part


  def process(self, channel, bot_nickname, user, input_message_raw):

    input_message = RequestProcessor.mkCasedMessage(input_message_raw)
    output_messages = []

    if channel == bot_nickname:
      output_messages = self.pmdToMe(user, input_message)

    elif input_message.startswith(bot_nickname + ":"):
      output_messages = self.directedAtMe(user, input_message)

    elif input_message.startswith(config.GENERATE_TRIGGER):
      output_messages = self.triggerGenerateQuote(user, input_message)

    elif input_message.startswith(config.META_TRIGGER):
      output_messages = self.triggerMeta(user, input_message)

    return output_messages


  def pmdToMe(self, user, input_message):
    logging.warning("Message received by PM: [%s] %s", user, input_message)
    return []


  def directedAtMe(self, user, input_message):
    return [self.makeGenericHelp()]


  def makeStats(self, user, raw_tokens):

    nicks = raw_tokens[1:]
    output_messages = []

    if not nicks:
      output_messages = self.makeGenericStats()

    else:
      output_messages = self.makeUserStats(nicks[0])

    return output_messages


  # Attempt to start a mystery sequence; return response string
  def startMystery(self, user, raw_tokens):

    if not self.current_mystery:
      nick_tuple = (UserNickType.RANDOM, "")
      output_nicks, output_quote = self.generator.generate([nick_tuple], None, config.MYSTERY_MIN_STARTERS, False)

      if output_nicks:

        author = output_nicks[0]
        hints = self.makeHints(author, len(output_quote.split()))

        author_aliases = self.generator.getUserAliases(author)
        self.current_mystery = Mystery(self.next_mystery_ident, author, author_aliases, output_quote, hints)
        self.next_mystery_ident += 1

    output_message = RequestProcessor.formatMysteryDescription(self.current_mystery.getInfo())

    return [output_message]


  # Return the appropriate number of hints for a nick length
  @staticmethod
  def getHintCount(len_nick):

    if len_nick <= (config.MYSTERY_CHARACTER_HINTS_MAX + 1):
      return 1

    return config.MYSTERY_CHARACTER_HINTS_MAX


  # Process user guess of author; return response string, which may be empty
  def guessMystery(self, user, tokens):

    output_message = ""

    if not self.current_mystery:
      output_message = RequestProcessor.NO_MYSTERY

    else:

      # FIXME: what if they guess more than two? discard silently?
      if len(tokens) == 2:

        # Find or create player, and record that they took part in this game
        player = self.players.getOrCreatePlayer(user)
        player.recordGame(self.current_mystery.ident)

        # Evaluate player's guess
        guess = tokens[1]
        real_author = self.current_mystery.guess(guess)

        if not real_author:
          player.incrementScore(PlayerScoreType.GUESSES_INCORRECT)

        else:
          player.incrementScore(PlayerScoreType.GUESSES_CORRECT)
          aka = ""
          if guess != real_author:
            aka = " (AKA %s)" % guess
          output_message = RequestProcessor.MYSTERY_SOLVE_WITH_WINNER % (real_author, aka, user)
          self.current_mystery = None

      self.players.updateChanges()

    return [output_message]


  # Give hint about mystery by printing a random character from the author's nick
  def hintMystery(self, user, raw_tokens):

    output_message = RequestProcessor.NO_MYSTERY

    if self.current_mystery:

      hint = self.current_mystery.getHint()

      if not hint:
        output_message = RequestProcessor.MYSTERY_HINT_NONE

      else:
        if hint[0] == HintType.NICK_CHARACTER:
          output_message = RequestProcessor.MYSTERY_HINT_NICK_CHARACTER % hint[1]

        elif hint[0] == HintType.ADDITIONAL_QUOTE:
          output_message = RequestProcessor.MYSTERY_HINT_ADDITIONAL_QUOTE % hint[1]

    return [output_message]


  # End a mystery sequence, revealing the author; return response string
  def solveMystery(self, user, raw_tokens):

    output_message = RequestProcessor.NO_MYSTERY

    if self.current_mystery:
      output_message = RequestProcessor.MYSTERY_SOLVE_NO_WINNER % self.current_mystery.author
      self.current_mystery = None

    return [output_message]


  # Return information about mystery game scores
  def scoreMystery(self, user, raw_tokens):

    nicks = raw_tokens[1:]
    output_messages = []

    if not nicks:
      output_messages = self.makeGenericScore()

    else:
      output_messages = self.makePlayerScore(nicks[0])

    return output_messages


  def triggerGenerateQuote(self, user, input_message):

      raw_tokens = re.split(' *', input_message)
      raw_nicks = re.split(config.INPUT_NICKS_SEP, raw_tokens[0][len(config.GENERATE_TRIGGER):])[:config.INPUT_NICKS_MAX]

      if config.ALL_USED and config.ALL_NICK in raw_nicks:
        raw_nicks = [config.ALL_NICK] # All subsumes all

      nick_tuples = []
      for raw_nick in raw_nicks:
        nick_tuple = RequestProcessor.makeNickTuple(raw_nick)
        nick_tuples.append(nick_tuple)

      seed_words = tuple(raw_tokens[1:])

      output_nicks, output_quote = self.generator.generate(nick_tuples, seed_words)

      output_message = ""

      if output_quote:

        output_message = config.OUTPUT_NICKS_OPEN + output_nicks[0]

        for output_nick in output_nicks[1:]:
          output_message += config.OUTPUT_NICKS_SEP + output_nick

        output_message += config.OUTPUT_NICKS_CLOSE + output_quote

      if output_message:
        return [output_message]

      return []


  @staticmethod
  def makeNickTuple(raw_nick):

    nick_type = UserNickType.NONRANDOM
    nick_name = raw_nick

    if raw_nick == config.RANDOM_NICK:
      nick_type = UserNickType.RANDOM
      nick_name = ""

    return (nick_type, nick_name)


  def triggerMeta(self, user, input_message):

    raw_tokens = re.split(' *', input_message)
    raw_commands = re.split(config.INPUT_NICKS_SEP, raw_tokens[0][len(config.META_TRIGGER):])

    if not raw_commands:
      return

    command = raw_commands[0]
    output_messages = []

    if command in self.commands:
      output_messages = self.commands[command](self, user, raw_tokens)

    return output_messages


  @staticmethod
  def formatStats(stats, statistic_formatters, default):

    if not stats:
      return default

    stats_formatted = []
    for (stat_type, stat_value) in stats.iteritems():
      if stat_value:
        stat_format = statistic_formatters[stat_type]
        stats_formatted.append(stat_format.container % stat_format.function(stat_value))

    return ["".join(stats_formatted)]


  def makeGenericStats(self):
    stats = self.generator.getGenericStatistics()
    return RequestProcessor.formatStats(stats, self.generic_statistic_formatters, [])


  @staticmethod
  def formatGenericUserCount(count_raw):
    return count_raw


  @staticmethod
  def formatGenericDate(date_raw):

    date = RequestProcessor.formatStatsDisplayBold(RequestProcessor.UNKNOWN_STR)

    if date_raw:
      date = datetime.datetime.fromtimestamp(
      int(date_raw)
      ).strftime(RequestProcessor.GENERIC_DATE_FORMAT_STR)

    return date


  @staticmethod
  def formatGenericChannels(channels_raw):

    primary_raw = channels_raw.primary
    additionals_raw = channels_raw.additionals

    primary = RequestProcessor.formatStatsDisplayBold(RequestProcessor.UNKNOWN_STR)

    if primary_raw:
      primary = RequestProcessor.formatStatsDisplayBold(primary_raw)

    additionals = RequestProcessor.formatStatsDisplayBold(RequestProcessor.UNKNOWN_OR_NONE_STR)
    additionals_formatted = []

    if additionals_raw:
      for additional_raw in additionals_raw:
        additionals_formatted.append(RequestProcessor.formatStatsDisplayBold(additional_raw))

      if len(additionals_formatted) == 1:
        additionals += additionals_formatted[0]

      else:
        additionals = ", ".join(additionals_formatted[:-1])

        if len(additionals_formatted) > 2:
          additionals += ","

        additionals += " and " + additionals_formatted[-1]

    return (primary, additionals)


  @staticmethod
  def formatGenericBiggestUsers(biggest_users_raw):

    biggest_user_count = len(biggest_users_raw)
    biggest_users = RequestProcessor.formatStatsDisplayBold(RequestProcessor.UNKNOWN_STR)
    biggest_users_formatted = []

    for big_user in biggest_users_raw:
      big_user_formatted = "%s (%d productions)"  % (RequestProcessor.formatStatsDisplayBold(big_user.nick), big_user.count)
      biggest_users_formatted.append(big_user_formatted)
    biggest_users = ", ".join(biggest_users_formatted[:-1])

    if len(biggest_users_formatted) > 2:
      biggest_users += ","
    biggest_users += " and " + biggest_users_formatted[-1]

    return (biggest_user_count, biggest_users)


  @staticmethod
  def formatGenericMostQuotedUsers(most_quoted_raw):

    if not most_quoted_raw:
      return ""

    most_quoted = ""
    if most_quoted_raw:

      quoted = most_quoted_raw[0]
      most_quoted = "%s (requested %d times(s))" % (RequestProcessor.formatStatsDisplayBold(quoted.nick), quoted.count)
      remaining_quoted = most_quoted_raw[1:]

      if remaining_quoted:
        most_quoted += ", followed by "
        most_quoted_formatted = []

        for quoted in remaining_quoted:
          quoted_user_formatted = "%s (%d)" % (RequestProcessor.formatStatsDisplayBold(quoted.nick), quoted.count)
          most_quoted_formatted.append(quoted_user_formatted)

        most_quoted += ", ".join(most_quoted_formatted[:-1])

        if len(remaining_quoted) > 2:
          most_quoted += ","

        if len(remaining_quoted) >= 2:
          most_quoted += " and "

        most_quoted += most_quoted_formatted[-1]

    return most_quoted


  @staticmethod
  def formatStatsDisplayBold(nick):
    return RequestProcessor.BOLD_DEFAULT % nick


  def makeUserStats(self, nick):
    stats = self.generator.getUserStatistics(nick)
    no_such = RequestProcessor.USER_UNKNOWN % RequestProcessor.formatStatsDisplayBold(nick)
    return RequestProcessor.formatStats(stats, self.user_statistic_formatters, [no_such])


  @staticmethod
  def formatUserRealNick(nick_raw):
    return RequestProcessor.formatStatsDisplayBold(nick_raw)


  @staticmethod
  def getAliasDisplayCount(total_alias_count):
    return min(total_alias_count, config.MERGEINFO_ALIASES_MAX)


  @staticmethod
  def formatUserAliases(aliases_raw):

    (aliases, requested_nick) = aliases_raw

    display_count = RequestProcessor.getAliasDisplayCount(len(aliases))
    additional_alias_count = len(aliases) - display_count

    result = ""
    sample_aliases = random.sample(aliases, display_count)

    # Always display the nick that was originally prompted, if it was an alias (if None, it was the real one)
    if requested_nick is not None and requested_nick not in sample_aliases:
      sample_aliases[0] = requested_nick

    if display_count == 1:
      result += sample_aliases[0]

    elif display_count == 2:
      form = "%s and %s"
      if additional_alias_count > 0:
        form = "%s, %s,"
      result += form % tuple(sample_aliases[:2])

    else:
      result += ", ".join(sample_aliases[:-1])
      form = ", and %s"
      if additional_alias_count > 0:
        form = ", %s,"
      result += form % sample_aliases[-1]

    if additional_alias_count > 0:
      form = " and %d other nick"
      if additional_alias_count >= 2:
        form += "s"
      result += form % additional_alias_count

    return result


  @staticmethod
  def formatUserSimpleCount(count_raw):
    return count_raw


  @staticmethod
  def formatMysteryDescription(mystery_info):

    quotes = mystery_info.known_quotes
    characters = mystery_info.known_nick_characters
    guessed = mystery_info.already_guessed

    description = ""

    if quotes:
      description += RequestProcessor.MYSTERY_DESCRIPTION_QUOTES % "] and [".join(quotes)

    if characters:
      description += RequestProcessor.MYSTERY_DESCRIPTION_CHARACTERS % ",".join(characters)

    if guessed:
      description += RequestProcessor.MYSTERY_DESCRIPTION_GUESSED % ",".join(guessed)

    return description


  def makeHints(self, author, first_hint_len):

    hints = []

    # Create nick character hints
    hint_character_count = RequestProcessor.getHintCount(len(author))
    hint_characters = random.sample(author, hint_character_count)
    for hint_character in hint_characters:
      hint = (HintType.NICK_CHARACTER, hint_character)
      hints.append(hint)

    # Create another quote by the mystery author as an additional hint
    if first_hint_len <= config.MYSTERY_WORDS_MAX_FOR_SECOND:
      nick_tuple = RequestProcessor.makeNickTuple(author)
      (_, additional_quote) = self.generator.generate([nick_tuple], None, 0, False)
      if additional_quote:
        additional_quote_hint = (HintType.ADDITIONAL_QUOTE, additional_quote)
        hints.append(additional_quote_hint)

    random.shuffle(hints)
    return hints


  def makeGenericScore(self):

    output_message = RequestProcessor.GENERIC_SCORE_MESSAGE_UNKNOWN

    scores = self.players.getGenericScore()
    if scores:
      output_message = RequestProcessor.GENERIC_SCORE_MESSAGE_KNOWN % scores

    return [output_message]


  def makePlayerScore(self, nick):

    nick_formatted = RequestProcessor.formatStatsDisplayBold(nick)

    output_message = RequestProcessor.PLAYER_SCORE_MESSAGE_UNKNOWN % nick_formatted
    scores = self.players.getPlayerScore(nick)

    if scores:
      score_args = (nick_formatted,) + scores
      output_message = RequestProcessor.PLAYER_SCORE_MESSAGE_KNOWN % score_args

    return [output_message]

