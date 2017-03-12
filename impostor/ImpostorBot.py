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

BOTDESC = " is a bot that impersonates people based on their history. Type '" + Config.GENERATE_TRIGGER + "<nick>' to see a line generated for a single user, '" + Config.GENERATE_TRIGGER + "random' for a line generated for a random user, or '" + Config.GENERATE_TRIGGER + "<nick1>" + Config.INPUT_NICKS_SEP + "<nick2>' to see a line generated from two users merged."

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
    self.logger.log("[directed#%s] <%s> %s" % (channel, user, input_message))

  def triggerGenerateQuote(self, user, channel, input_message):

      raw_tokens = re.split(' *', input_message)
      raw_nicks = re.split(Config.INPUT_NICKS_SEP, raw_tokens[0][len(Config.GENERATE_TRIGGER):])[:Config.INPUT_NICKS_MAX]

      if Config.ALL_USED and Config.ALL_NICK in raw_nicks:
        raw_nicks = [Config.ALL_NICK] # All subsumes all

      nick_tuples = []
      for raw_nick in raw_nicks:

        is_random = False
        nick_name = raw_nick

        if raw_nick == Config.RANDOM_NICK:
          is_random = True
          nick_name = ""

        nick_tuple = (is_random, nick_name)
        nick_tuples.append(nick_tuple)

      output_nicks, output_quote = self.factory.generator.generate(nick_tuples)

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

    if command == "mystery":
      nick_tuple = (True, "")
      output_nicks, output_quote = self.factory.generator.generate([nick_tuple])
      output_message = Config.OUTPUT_NICKS_OPEN + "???" + Config.OUTPUT_NICKS_CLOSE + " " + output_quote
      self.msg(channel, output_message)


class ImpostorBotFactory(protocol.ClientFactory):

  def __init__(self, channel, filename, srcdir):
    self.channel = channel
    self.filename = filename
    self.generator = Margen.Margen(srcdir)

  def buildProtocol(self, addr):
    p = ImpostorBot()
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
  
