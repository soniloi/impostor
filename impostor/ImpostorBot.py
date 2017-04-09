import datetime
import random
import re

import Config
import Margen

#
# IRC bot to be used with per-user Markov generator
#

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys


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


class HintType:
  NICK_CHARACTER = 0
  ADDITIONAL_QUOTE = 1


class Mystery:

  def __init__(self, author, initial_quote, hints):
    self.author = author
    self.quotes = [initial_quote]
    self.nick_characters = []
    self.future_hints = hints
    self.already_guessed = set()

  def describe(self):

    description = "The mystery author says: [" + self.quotes[0] + "]"
    for quote in self.quotes[1:]:
      description += " and [" + quote + "]"
    description += ". "

    if self.nick_characters:
      description += "Their nick contains the character(s) ["
      description += ",".join(self.nick_characters)
      description += "]. "

    if self.already_guessed:
      description += "The nick(s) guessed so far are ["
      description += ",".join(self.already_guessed)
      description += "]. "

    return description

  def getHint(self):

    hint_message = ""

    if not self.future_hints:
      hint_message = "I have no further hints to give. "

    else:
      hint_index = random.randint(0, len(self.future_hints) - 1)
      (hint_type, hint) = self.future_hints[hint_index]
      del self.future_hints[hint_index]

      if hint_type == HintType.NICK_CHARACTER:
        self.nick_characters.append(hint)
        hint_message = "The mystery author's name contains the character [" + hint + "]"

      elif hint_type == HintType.ADDITIONAL_QUOTE:
        self.quotes.append(hint)
        hint_message = "The mystery author also says: [" + hint + "]"

    return hint_message

  def guess(self, guess):
    self.already_guessed.add(guess)
    return guess == self.author


class Player:

  def __init__(self, nick):
    self.nick = nick
    self.correct_guesses = 0
    self.incorrect_guesses = 0


class MessageLogger:
  """
  An independent logger class (because separation of application
  and protocol logic is a good thing).
  """
  def __init__(self, file):
    self.file = file

  def log(self, message):
    """Write a message to the file."""
    timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
    self.file.write('%s %s\n' % (timestamp, message))
    self.file.flush()

  def close(self):
    self.file.close()


class ImpostorBot(irc.IRCClient):
  
  BOLD_DEFAULT = Style.BOLD + "%s" + Style.CLEAR

  GENERATE_TRIGGER = Style.BOLD + Style.COLOUR + Colour.YELLOW + Config.GENERATE_TRIGGER
  STATS_TRIGGER = Style.BOLD + Style.COLOUR + Colour.GREEN + Config.META_TRIGGER
  MYSTERY_TRIGGER = Style.BOLD + Style.COLOUR + Colour.RED + Config.META_TRIGGER

  BOT_NICK = BOLD_DEFAULT % Config.BOT_NICK
  GENERATE_SINGLE = GENERATE_TRIGGER + "<nick>" + Style.CLEAR
  GENERATE_RANDOM = GENERATE_TRIGGER + Config.RANDOM_NICK + Style.CLEAR
  GENERATE_MERGED = GENERATE_TRIGGER + "<nick1>" + Config.INPUT_NICKS_SEP + "<nick2>" + Style.CLEAR
  GENERATE_ALL = GENERATE_TRIGGER + Config.ALL_NICK + Style.CLEAR

  META_STATS = STATS_TRIGGER + Config.META_STATS + Style.CLEAR
  META_STATS_USER = STATS_TRIGGER + Config.META_STATS + " <nick>" + Style.CLEAR

  MYSTERY_START = MYSTERY_TRIGGER + Config.MYSTERY_START + Style.CLEAR
  MYSTERY_GUESS = MYSTERY_TRIGGER + Config.MYSTERY_GUESS + " <nick>" + Style.CLEAR
  MYSTERY_HINT = MYSTERY_TRIGGER + Config.MYSTERY_HINT + Style.CLEAR
  MYSTERY_SOLVE = MYSTERY_TRIGGER + Config.MYSTERY_SOLVE + Style.CLEAR

  BOT_DESC_BASIC = BOT_NICK + " is a bot that impersonates people based on their history. Type " \
    + GENERATE_SINGLE + " to see a line generated for a single user, " \
    + GENERATE_RANDOM + " for a line generated for a random user, or " \
    + GENERATE_MERGED + " to see a line generated from two users merged. "
  if Config.ALL_USED:
    BOT_DESC_BASIC += "You may also type '" \
    + GENERATE_ALL + " to see a line generated from all channel users combined. "

  BOT_DESC_MYSTERY = "Type " \
    + MYSTERY_START + " to generate a mystery line. Then type " \
    + MYSTERY_GUESS + " to guess the nick of the mystery line's author, " \
    + MYSTERY_HINT + " for a hint, or " \
    + MYSTERY_SOLVE + " to see the solution. "

  BOT_DESC_ADDITIONAL = "Type " \
    + META_STATS + " for basic generic statistics, or " \
    + META_STATS_USER + " for statistics on a specific user. See " \
    + Config.REPOSITORY + " for (slightly) more information. "

  NO_MYSTERY = "There is currently no unsolved mystery. Type %s to start one. " % MYSTERY_START
  MYSTERY_SOLVE_NO_WINNER = "The mystery author was: %s. No-one guessed correctly. "
  MYSTERY_SOLVE_WITH_WINNER = "The mystery author was: %s. Congratulations, %s! "

  nickname = Config.BOT_NICK

  def __init__(self, source_dir):
    self.generator = Margen.Margen(source_dir)
    self.current_mystery = None
    self.players = {}
    if self.generator.empty():
      print "Warning: generator is empty; is this correct?"

  def connectionMade(self):
    irc.IRCClient.connectionMade(self)
    self.logger = MessageLogger(open(self.factory.filename, "a"))
    self.logger.log("[connected at %s]" % 
            time.asctime(time.localtime(time.time())))

  def connectionLost(self, reason):
    irc.IRCClient.connectionLost(self, reason)
    self.logger.log("[disconnected at %s]" % 
            time.asctime(time.localtime(time.time())))
    self.logger.close()

  # callbacks for events

  def signedOn(self):
    """Called when bot has succesfully signed on to server."""
    self.join(self.factory.channel)

  def joined(self, channel):
    """This will get called when the bot joins the channel."""
    self.logger.log("[I have joined %s]" % channel)

  def privmsg(self, user, channel, input_message_raw):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]
    self.logger.log("<%s> %s" % (user, input_message_raw))

    input_message = input_message_raw.strip().lower()
    output_messages = []
    
    if channel == self.nickname:
      output_messages = self.pmdToMe(user, input_message)

    elif input_message.startswith(self.nickname + ":"):
      output_messages = self.directedAtMe(user, input_message)

    elif input_message.startswith(Config.GENERATE_TRIGGER):
      output_messages = self.triggerGenerateQuote(user, input_message)

    elif input_message.startswith(Config.META_TRIGGER):
      output_messages = self.triggerMysteryQuote(user, input_message)

    for output_message in output_messages:
      self.msg(channel, output_message)

  def action(self, user, channel, input_message):
    """This will get called when the bot sees someone do an action."""
    user = user.split('!', 1)[0]
    self.logger.log("* %s %s" % (user, input_message))

  # irc callbacks

  def irc_NICK(self, prefix, params):

    old_nick = prefix.split('!')[0]
    new_nick = params[0]

    if old_nick in self.players:
      player = self.players[old_nick]
      player.nick = new_nick
      self.players[new_nick] = player
      del self.players[old_nick]

  # For fun, override the method that determines how a nickname is changed on
  # collisions. The default method appends an underscore.
  def alterCollidedNick(self, nickname):
    """
    Generate an altered version of a nickname that caused a collision in an
    effort to create an unused related name for subsequent registration.
    """
    return nickname + '^'

  def makeHelp(self):
    return [ImpostorBot.BOT_DESC_BASIC, ImpostorBot.BOT_DESC_MYSTERY + ImpostorBot.BOT_DESC_ADDITIONAL]

  def pmdToMe(self, user, input_message):
    self.logger.log("[PM] <%s> %s" % (user, input_message))
    return []

  def directedAtMe(self, user, input_message):
    return self.makeHelp()

  def triggerGenerateQuote(self, user, input_message):

      raw_tokens = re.split(' *', input_message)
      raw_nicks = re.split(Config.INPUT_NICKS_SEP, raw_tokens[0][len(Config.GENERATE_TRIGGER):])[:Config.INPUT_NICKS_MAX]

      if Config.ALL_USED and Config.ALL_NICK in raw_nicks:
        raw_nicks = [Config.ALL_NICK] # All subsumes all

      nick_tuples = []
      for raw_nick in raw_nicks:
        nick_tuple = ImpostorBot.makeNickTuple(raw_nick)
        nick_tuples.append(nick_tuple)

      output_nicks, output_quote = self.generator.generate(nick_tuples)

      output_message = ""

      if output_quote:

        output_message = Config.OUTPUT_NICKS_OPEN + output_nicks[0]

        for output_nick in output_nicks[1:]:
          output_message += Config.OUTPUT_NICKS_SEP + output_nick

        output_message += Config.OUTPUT_NICKS_CLOSE + output_quote

      if output_message:
        return [output_message]
      return []

  @staticmethod
  def makeNickTuple(raw_nick):

    nick_type = Margen.NickType.NONRANDOM
    nick_name = raw_nick

    if raw_nick == Config.RANDOM_NICK:
      nick_type = Margen.NickType.RANDOM
      nick_name = ""

    return (nick_type, nick_name)

  def triggerMysteryQuote(self, user, input_message):

    raw_tokens = re.split(' *', input_message)
    raw_commands = re.split(Config.INPUT_NICKS_SEP, raw_tokens[0][len(Config.META_TRIGGER):])

    if not raw_commands:
      return

    command = raw_commands[0]
    output_messages = []

    if command in Config.META_HELP:
      output_messages = self.makeHelp()

    elif command == Config.META_STATS:
      output_messages = self.makeStats(raw_tokens[1:])

    elif command == Config.MYSTERY_START:
      output_messages = self.startMystery()

    elif command == Config.MYSTERY_GUESS:
      output_messages = self.guessMystery(user, raw_tokens)

    elif command == Config.MYSTERY_HINT:
      output_messages = self.hintMystery()

    elif command == Config.MYSTERY_SOLVE:
      output_messages = self.solveMystery()

    elif command == Config.MYSTERY_SCORE:
      output_messages = self.scoreMystery(raw_tokens[1:])

    return output_messages

  def makeStats(self, nicks):

    output_messages = []

    if not nicks:
      output_messages = self.makeGenericStats()

    else:
      output_messages.append(self.makeUserStats(nicks[0]))

    return output_messages

  def makeGenericStats(self):

    stats = self.generator.getGenericStatistics()

    if not stats:
      return []

    count = ImpostorBot.formatUserCountInfo(stats.userCount)
    date = ImpostorBot.formatDateInfo(stats.dateGenerated)
    channels = ImpostorBot.formatChannelInfo(stats.primaryChannel, stats.additionalChannels)
    biggest_users = ImpostorBot.formatBiggestUsersStats(stats.biggestUsers)
    most_quoted = ImpostorBot.formatMostQuotedStats(stats.mostQuoted)

    return [count + date + channels, biggest_users + most_quoted]

  @staticmethod
  def formatUserCountInfo(count_raw):
    return "I have material from %d users. " % count_raw

  @staticmethod
  def formatDateInfo(date_raw):

    date = "[Unknown]"

    if date_raw:
      date = datetime.datetime.fromtimestamp(
      int(date_raw)
      ).strftime("%Y-%m-%d at %H.%M.%S")

    return "My source material was generated on %s. " % date

  @staticmethod
  def formatChannelInfo(primary_raw, additionals_raw):

    primary = "[Unknown]"

    if primary_raw:
      primary = ImpostorBot.formatStatsDisplayBold(primary_raw)

    additionals = ""
    additionals_formatted = []

    if not additionals_raw:
      additionals_formatted.append(ImpostorBot.formatStatsDisplayBold("[Unknown or None]"))

    else:
      for additional_raw in additionals_raw:
        additionals_formatted.append(ImpostorBot.formatStatsDisplayBold(additional_raw))

      if len(additionals_formatted) == 1:
        additionals += additionals_formatted[0]

      else:
        additionals = ", ".join(additionals_formatted[:-1])

        if len(additionals_formatted) > 2:
          additionals += ","

        additionals += " and " + additionals_formatted[-1]

    return "Its primary source channel was %s, and additional material was drawn from %s. " % (primary, additionals)

  @staticmethod
  def formatBiggestUsersStats(biggest_users_raw):

    biggest_user_count = str(len(biggest_users_raw))
    biggest_users = "[Unknown]"
    biggest_users_formatted = []

    for big_user in biggest_users_raw:
      (nick, production_count) = big_user
      big_user_formatted = "%s (%d productions)"  % (ImpostorBot.formatStatsDisplayBold(nick), production_count)
      biggest_users_formatted.append(big_user_formatted)
    biggest_users = ", ".join(biggest_users_formatted[:-1])

    if len(biggest_users_formatted) > 2:
      biggest_users += ","
    biggest_users += " and " + biggest_users_formatted[-1]

    return "The %s users with the most source material are: %s. " % (biggest_user_count, biggest_users)

  @staticmethod
  def formatMostQuotedStats(most_quoted_raw):

    if not most_quoted_raw:
      return ""

    most_quoted = ""
    if most_quoted_raw:

      (nick, quote_count) = most_quoted_raw[0]
      most_quoted = "%s (requested %d times(s))" % (ImpostorBot.formatStatsDisplayBold(nick), quote_count)
      remaining_quoted = most_quoted_raw[1:]

      if remaining_quoted:
        most_quoted += ", followed by "
        most_quoted_formatted = []

        for quoted_user in remaining_quoted:
          (nick, quote_count) = quoted_user
          quoted_user_formatted = "%s (%d)" % (ImpostorBot.formatStatsDisplayBold(nick), quote_count)
          most_quoted_formatted.append(quoted_user_formatted)

        most_quoted += ", ".join(most_quoted_formatted[:-1])

        if len(remaining_quoted) > 2:
          most_quoted += ","

        if len(remaining_quoted) >= 2:
          most_quoted += " and "

        most_quoted += most_quoted_formatted[-1]

    return "Since the last time I was started, the user prompted for quotes most often is: %s. " % most_quoted

  @staticmethod
  def formatStatsDisplayBold(nick):
    return ImpostorBot.BOLD_DEFAULT % nick

  def makeUserStats(self, nick):

    output_message = ""
    stats = self.generator.getUserStatistics(nick)
    nick_formatted = ImpostorBot.formatStatsDisplayBold(nick)

    if not stats:

      output_message += "I know of no such user %s. " % nick_formatted

    else:

      (real_nick, production_count, quotes_requested, aliases) = stats
      real_nick_formatted = ImpostorBot.formatStatsDisplayBold(stats.realNick)
      output_message += "The user %s" % real_nick_formatted

      if aliases:
        output_message += ImpostorBot.formatAliases(stats.aliases)

      output_message += " has %d productions. " % stats.productionCount
      output_message += "%d quote(s) have been requested of them. " % stats.quotesRequested

    return output_message

  @staticmethod
  def getAliasDisplayCount(total_alias_count):
    return min(total_alias_count, Config.MERGEINFO_ALIASES_MAX)

  @staticmethod
  def formatAliases(aliases):

    display_count = ImpostorBot.getAliasDisplayCount(len(aliases))
    additional_alias_count = len(aliases) - display_count

    result = " (AKA "
    sample_aliases = random.sample(aliases, display_count)

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

    result += ")"
    return result

  # Attempt to start a mystery sequence; return response string
  def startMystery(self):

    output_message = ""

    if self.current_mystery:
      output_message += self.current_mystery.describe()
      return [output_message]

    if not output_message:
      nick_tuple = (Margen.NickType.RANDOM, "")
      output_nicks, output_quote = self.generator.generate([nick_tuple], Config.MYSTERY_MIN_STARTERS)

      if output_nicks:
        author = output_nicks[0]
        hints = self.makeHints(author, len(output_quote.split()))
        self.current_mystery = Mystery(author, output_quote, hints)
        output_message += self.current_mystery.describe()

    return [output_message]

  # Return the appropriate number of hints for a nick length
  @staticmethod
  def getHintCount(len_nick):

    if len_nick <= (Config.MYSTERY_CHARACTER_HINTS_MAX + 1):
      return 1

    return Config.MYSTERY_CHARACTER_HINTS_MAX

  def makeHints(self, author, first_hint_len):

    hints = []

    # Create nick character hints
    hint_character_count = ImpostorBot.getHintCount(len(author))
    hint_characters = random.sample(author, hint_character_count)
    for hint_character in hint_characters:
      hint = (HintType.NICK_CHARACTER, hint_character)
      hints.append(hint)

    # Create another quote by the mystery author as an additional hint
    if first_hint_len <= Config.MYSTERY_WORDS_MAX_FOR_SECOND:
      nick_tuple = ImpostorBot.makeNickTuple(author)
      (_, additional_quote) = self.generator.generate([nick_tuple])
      if additional_quote:
        additional_quote_hint = (HintType.ADDITIONAL_QUOTE, additional_quote)
        hints.append(additional_quote_hint)

    return hints

  # Process user guess of author; return response string, which may be empty
  def guessMystery(self, user, tokens):

    output_message = ""

    if not self.current_mystery:
      output_message = ImpostorBot.NO_MYSTERY

    else:

      # FIXME: what if they guess more than two? discard silently?
      if len(tokens) == 2:

        guess = tokens[1]
        success = self.current_mystery.guess(guess)

        if not user in self.players:
          self.players[user] = Player(user)

        if not success:
          self.players[user].incorrect_guesses += 1

        else:
          self.players[user].correct_guesses += 1
          output_message = ImpostorBot.MYSTERY_SOLVE_WITH_WINNER % (guess, user)
          self.current_mystery = None

    return [output_message]

  # Give hint about mystery by printing a random character from the author's nick
  def hintMystery(self):

    output_message = ImpostorBot.NO_MYSTERY

    if self.current_mystery:
      output_message = self.current_mystery.getHint()

    return [output_message]

  # End a mystery sequence, revealing the author; return response string
  def solveMystery(self):

    output_message = ImpostorBot.NO_MYSTERY

    if self.current_mystery:
      output_message = ImpostorBot.MYSTERY_SOLVE_NO_WINNER % self.current_mystery.author
      self.current_mystery = None

    return [output_message]

  # Return information about mystery game scores
  def scoreMystery(self, nicks):

    if not nicks:
      return []

    nick = nicks[0]
    nick_formatted = ImpostorBot.formatStatsDisplayBold(nick)

    output_message = "If there is a player currently called %s, then they have not guessed correctly yet." % nick_formatted

    if nick in self.players:
      correct_guess_count = self.players[nick].correct_guesses
      incorrect_guess_count = self.players[nick].incorrect_guesses
      output_message = "The player %s has guessed incorrectly %d time(s) and correctly %d time(s) ." \
        % (nick_formatted, incorrect_guess_count, correct_guess_count)

    return [output_message]


class ImpostorBotFactory(protocol.ClientFactory):

  def __init__(self, channel, filename, source_dir):
    self.channel = channel
    self.filename = filename
    self.source_dir = source_dir

  def buildProtocol(self, addr):
    p = ImpostorBot(self.source_dir)
    p.factory = self
    return p

  def clientConnectionLost(self, connector, reason):
    connector.connect()

  def clientConnectionFailed(self, connector, reason):
    print "connection failed:", reason
    reactor.stop()


if __name__ == '__main__':
  # initialize logging
  log.startLogging(sys.stdout)
  
  if len(sys.argv) < 5:
    print "Usage: " + sys.argv[0] + " <network> <channel> <logfile> <sourcedir>"

  # create factory protocol and application
  f = ImpostorBotFactory(sys.argv[2], sys.argv[3], sys.argv[4])

  # connect factory to this host and port
  reactor.connectTCP(sys.argv[1], 6667, f)

  # run bot
  reactor.run()
  
