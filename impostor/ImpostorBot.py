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

BOT_NICK = "\x02" + Config.BOT_NICK + "\x0f"
GENERATE_SINGLE = "\x02\x038" + Config.GENERATE_TRIGGER + "<nick>\x0f"
GENERATE_RANDOM = "\x02\x038" + Config.GENERATE_TRIGGER + Config.RANDOM_NICK + "\x0f"
GENERATE_MERGED = "\x02\x038" + Config.GENERATE_TRIGGER + "<nick1>" + Config.INPUT_NICKS_SEP + "<nick2>\x0f"
GENERATE_ALL = "\x02\x038" + Config.GENERATE_TRIGGER + Config.ALL_NICK + "\x0f"
MYSTERY_START = "\x02\x034" + Config.MYSTERY_TRIGGER + Config.MYSTERY_START + "\x0f"
MYSTERY_SOLVE = "\x02\x034" + Config.MYSTERY_TRIGGER + Config.MYSTERY_SOLVE + "\x0f"

BOT_DESC_BASIC = BOT_NICK + " is a bot that impersonates people based on their history. Type " \
  + GENERATE_SINGLE + " to see a line generated for a single user, " \
  + GENERATE_RANDOM + " for a line generated for a random user, or " \
  + GENERATE_MERGED + " to see a line generated from two users merged. "
if Config.ALL_USED:
  BOT_DESC_BASIC += "You may also type '" \
  + GENERATE_ALL + " to see a line generated from all channel users combined. "

BOT_DESC_MYSTERY = "Type " \
  + MYSTERY_START + " to generate a mystery line, or " \
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
    
    if channel == self.nickname:
      self.pmdToMe(user, channel, input_message)

    elif input_message.startswith(self.nickname + ":"):
      self.directedAtMe(user, channel, input_message)

    elif input_message.startswith(Config.GENERATE_TRIGGER):
      self.triggerGenerateQuote(user, channel, input_message)

    elif input_message.startswith(Config.MYSTERY_TRIGGER):
      self.triggerMysteryQuote(user, channel, input_message)

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

  def pmdToMe(self, user, channel, input_message):
    self.logger.log("[PM] <%s> %s" % (user, input_message))

  def directedAtMe(self, user, channel, input_message):
    self.msg(channel, BOT_DESC_BASIC)
    self.msg(channel, BOT_DESC_MYSTERY)
    self.logger.log("[directed#%s] <%s> %s" % (channel, user, input_message))

  def triggerGenerateQuote(self, user, channel, input_message):

      raw_tokens = re.split(' *', input_message)
      raw_nicks = re.split(Config.INPUT_NICKS_SEP, raw_tokens[0][len(Config.GENERATE_TRIGGER):])[:Config.INPUT_NICKS_MAX]

      if Config.ALL_USED and Config.ALL_NICK in raw_nicks:
        raw_nicks = [Config.ALL_NICK] # All subsumes all

      nick_tuples = []
      for raw_nick in raw_nicks:

        nick_type = Margen.NickType.NONRANDOM
        nick_name = raw_nick

        if raw_nick == Config.RANDOM_NICK:
          nick_type = Margen.NickType.RANDOM
          nick_name = ""

        nick_tuple = (nick_type, nick_name)
        nick_tuples.append(nick_tuple)

      output_nicks, output_quote = self.generator.generate(nick_tuples)

      if output_quote:

        output_message = Config.OUTPUT_NICKS_OPEN + output_nicks[0]

        for output_nick in output_nicks[1:]:
          output_message += Config.OUTPUT_NICKS_SEP + output_nick

        output_message += Config.OUTPUT_NICKS_CLOSE + output_quote
        self.msg(channel, output_message)

  def triggerMysteryQuote(self, user, channel, input_message):

    raw_tokens = re.split(' *', input_message)
    raw_commands = re.split(Config.INPUT_NICKS_SEP, raw_tokens[0][len(Config.MYSTERY_TRIGGER):])

    if not raw_commands:
      return

    command = raw_commands[0]
    output_message = ""

    if command == Config.MYSTERY_START:
      if self.current_author is None:
        nick_tuple = (Margen.NickType.RANDOM, "")
        output_nicks, output_quote = self.generator.generate([nick_tuple], Config.MYSTERY_MIN_STARTERS)
        output_message = ImpostorBot.MYSTERY_NAME_FULL + output_quote
        self.current_author = output_nicks[0]
      else:
        output_message = "There is already an unsolved mystery"

    elif command == Config.MYSTERY_SOLVE:
      if self.current_author:
        output_message = "The mystery author was: " + self.current_author
        self.current_author = None
      else:
        output_message = "There is currently no unsolved mystery"

    if output_message:
      self.msg(channel, output_message)


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
  
