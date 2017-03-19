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

GENERATE_TRIGGER = Style.BOLD + Style.COLOUR + Colour.YELLOW + Config.GENERATE_TRIGGER
META_TRIGGER = Style.BOLD + Style.COLOUR + Colour.RED + Config.META_TRIGGER

BOT_NICK = Style.BOLD + Config.BOT_NICK + Style.CLEAR
GENERATE_SINGLE = GENERATE_TRIGGER + "<nick>" + Style.CLEAR
GENERATE_RANDOM = GENERATE_TRIGGER + Config.RANDOM_NICK + Style.CLEAR
GENERATE_MERGED = GENERATE_TRIGGER + "<nick1>" + Config.INPUT_NICKS_SEP + "<nick2>" + Style.CLEAR
GENERATE_ALL = GENERATE_TRIGGER + Config.ALL_NICK + Style.CLEAR
MYSTERY_START = META_TRIGGER + Config.MYSTERY_START + Style.CLEAR
MYSTERY_GUESS = META_TRIGGER + Config.MYSTERY_GUESS + " <nick>" + Style.CLEAR
MYSTERY_SOLVE = META_TRIGGER + Config.MYSTERY_SOLVE + Style.CLEAR

BOT_DESC_BASIC = BOT_NICK + " is a bot that impersonates people based on their history. Type " \
  + GENERATE_SINGLE + " to see a line generated for a single user, " \
  + GENERATE_RANDOM + " for a line generated for a random user, or " \
  + GENERATE_MERGED + " to see a line generated from two users merged. "
if Config.ALL_USED:
  BOT_DESC_BASIC += "You may also type '" \
  + GENERATE_ALL + " to see a line generated from all channel users combined. "

BOT_DESC_MYSTERY = "Type " \
  + MYSTERY_START + " to generate a mystery line. Then type " \
  + MYSTERY_GUESS + " to guess the nick of the mystery line's author, or " \
  + MYSTERY_SOLVE + " to see the solution."

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
  
  nickname = Config.BOT_NICK
  MYSTERY_NAME_FULL = Config.OUTPUT_NICKS_OPEN + Config.MYSTERY_NAME + Config.OUTPUT_NICKS_CLOSE

  def __init__(self, source_dir):
    self.generator = Margen.Margen(source_dir)
    self.current_author = None
    self.current_mystery = None
    self.current_hints = None
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
    """Called when an IRC user changes their nickname."""
    old_nick = prefix.split('!')[0]
    new_nick = params[0]
    self.logger.log("%s is now known as %s" % (old_nick, new_nick))


  # For fun, override the method that determines how a nickname is changed on
  # collisions. The default method appends an underscore.
  def alterCollidedNick(self, nickname):
    """
    Generate an altered version of a nickname that caused a collision in an
    effort to create an unused related name for subsequent registration.
    """
    return nickname + '^'

  def pmdToMe(self, user, input_message):
    self.logger.log("[PM] <%s> %s" % (user, input_message))
    return []

  def directedAtMe(self, user, input_message):
    return [BOT_DESC_BASIC, BOT_DESC_MYSTERY]

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
    output_message = ""

    if command == Config.META_STATS:
      output_message = self.makeStats(raw_tokens[1:])

    elif command == Config.MYSTERY_START:
      output_message = self.startMystery()

    elif command == Config.MYSTERY_GUESS:
      output_message = self.guessMystery(user, raw_tokens)

    elif command == Config.MYSTERY_HINT:
      output_message = self.hintMystery()

    elif command == Config.MYSTERY_SOLVE:
      output_message = self.solveMystery()

    if output_message:
      return [output_message]
    return []

  def makeStats(self, nicks):

    if not nicks:
      return "I have material from " + str(self.generator.getUserCount()) + " users."

    output_message = ""
    for nick in nicks:
      production_count = self.generator.getUserProductionCount(nick)
      if production_count < 1:
        output_message = "I know of no such user " + nick + ". "
      else:
        output_message += "The user " + nick + " has " + str(production_count) + " productions. "

    return output_message

  # Attempt to start a mystery sequence; return response string
  def startMystery(self):

    if self.current_mystery:
      return self.current_mystery

    output_message = ""

    nick_tuple = (Margen.NickType.RANDOM, "")
    output_nicks, output_quote = self.generator.generate([nick_tuple], Config.MYSTERY_MIN_STARTERS)

    if output_nicks:
      self.current_author = output_nicks[0]
      hint_count = ImpostorBot.getHintCount(len(self.current_author))
      self.current_hints = random.sample(self.current_author, hint_count)
      output_message = ImpostorBot.MYSTERY_NAME_FULL + output_quote
      self.current_mystery = output_message

    return output_message

  # Return the appropriate number of hints for a nick length
  @staticmethod
  def getHintCount(len_nick):

    if len_nick <= Config.MYSTERY_HINTS_MAX:
      return 1

    return Config.MYSTERY_HINTS_MAX

  # Process user guess of author; return response string, which may be empty
  def guessMystery(self, user, tokens):

    if not self.current_mystery:
      return "There is currently no unsolved mystery. "

    output_message = ""

    # FIXME: what if they guess more than two? discard silently?
    if len(tokens) == 2:
      guess = tokens[1]
      if guess == self.current_author:
        output_message = "The mystery author was: " + self.current_author + ". Congratulations, " + user + "! "
        self.endMystery()

    return output_message

  # Give hint about mystery by printing a random character from the user's nick
  def hintMystery(self):

    if not self.current_mystery:
      return "There is currently no unsolved mystery. "

    if not self.current_hints:
      return "I have no further hints to give. "

    hint_index = random.randint(0, len(self.current_hints) - 1)
    hint = self.current_hints[hint_index]
    del self.current_hints[hint_index]
    return "The mystery author's name contains the character [" + hint + "]"

  # End a mystery sequence, revealing the author; return respons string
  def solveMystery(self):

    if not self.current_mystery:
      return "There is currently no unsolved mystery. "

    output_message = "The mystery author was: " + self.current_author + ". No-one guessed correctly. "
    self.endMystery()

    return output_message

  def endMystery(self):
    self.current_author = None
    self.current_mystery = None
    self.current_hints = None


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
  
