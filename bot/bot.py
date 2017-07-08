from collections import namedtuple
import logging
import sys
import time

import config
from processor import RequestProcessor

#
# IRC bot to be used with per-user Markov generator
#

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log


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

  nickname = config.BOT_NICK


  def __init__(self, source_dir):
    logging.basicConfig(filename="impostorbot.log", level=logging.INFO)
    self.processor = RequestProcessor(source_dir)


  def connectionMade(self):
    irc.IRCClient.connectionMade(self)
    self.logger = MessageLogger(open(self.factory.filename, "a"))
    self.logger.log("[connected at %s]" % time.asctime(time.localtime(time.time())))


  def connectionLost(self, reason):
    irc.IRCClient.connectionLost(self, reason)
    self.logger.log("[disconnected at %s]" % time.asctime(time.localtime(time.time())))
    self.logger.close()


  # callbacks for events

  def signedOn(self):
    """Called when bot has succesfully signed on to server."""
    self.join(self.factory.channel)


  def joined(self, channel):
    """This will get called when the bot joins the channel."""
    self.logger.log("[I have joined %s]" % channel)
    logging.info("Joined %s" % channel)


  def privmsg(self, user, channel, input_message_raw):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]
    self.logger.log("<%s> %s" % (user, input_message_raw))
    logging.info("Message received from %s: [%s] %s" % (channel, user, input_message_raw))

    input_message = input_message_raw.strip().lower()
    output_messages = []

    if channel == self.nickname:
      output_messages = self.processor.pmdToMe(user, input_message)

    elif input_message.startswith(self.nickname + ":"):
      output_messages = self.processor.directedAtMe(user, input_message)

    elif input_message.startswith(config.GENERATE_TRIGGER):
      output_messages = self.processor.triggerGenerateQuote(user, input_message)

    elif input_message.startswith(config.META_TRIGGER):
      output_messages = self.processor.triggerMeta(user, input_message)

    for output_message in output_messages:
      self.msg(channel, output_message)


  def action(self, user, channel, input_message):
    """This will get called when the bot sees someone do an action."""
    user = user.split('!', 1)[0]
    self.logger.log("* %s %s" % (user, input_message))
    logging.info("Action received from %s: [%s] %s" % (channel, user, input_message))


  # irc callbacks

  def irc_NICK(self, prefix, params):

    old_nick = prefix.split('!')[0]
    new_nick = params[0]

    logging.info("Nick change detected: [%s] -> [%s]" % (old_nick, new_nick))

    self.players.updateNick(old_nick, new_nick)


  # For fun, override the method that determines how a nickname is changed on
  # collisions. The default method appends an underscore.
  def alterCollidedNick(self, nickname):
    """
    Generate an altered version of a nickname that caused a collision in an
    effort to create an unused related name for subsequent registration.
    """
    alternative_nickname = nickname + '^'
    logging.warning("Nickname %s collided, using %s instead" % (nickname, alternative_nickname))
    return alternative_nickname


class ImpostorBotFactory(protocol.ClientFactory):

  USAGE = "Usage: %s <network> <channel> <logfile> <sourcedir>"
  CONNECTION_FAILED = "Connection failed: %s"

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
    print ImpostorBotFactory.CONNECTION_FAILED % reason
    reactor.stop()


if __name__ == '__main__':

  # Initialize logging
  log.startLogging(sys.stdout)

  if len(sys.argv) < 5:
    print ImpostorBotFactory.USAGE % sys.argv[0]

  host = sys.argv[1]
  port = 6667
  channel = sys.argv[2]
  log_filename = sys.argv[3]
  source_dir = sys.argv[4]

  # Create factory protocol and application
  factory = ImpostorBotFactory(channel, log_filename, source_dir)

  # Connect factory to this host and port
  reactor.connectTCP(host, port, factory)

  # Run bot
  reactor.run()

