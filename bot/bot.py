from collections import namedtuple
import logging
import sys
import time

import config
from processor import RequestProcessor

from generator import generator
from players import PlayerCollection

#
# IRC bot to be used with per-user Markov generator
#

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log


class ImpostorBot(irc.IRCClient):

  nickname = config.BOT_NICK


  def __init__(self, source_dir, log_filename, channel):
    self.channel = channel
    self.processor = RequestProcessor(source_dir, generator.Generator(), PlayerCollection())
    logging.basicConfig(filename=log_filename, level=logging.INFO)


  def connectionMade(self):
    irc.IRCClient.connectionMade(self)
    logging.info("Connection made at: %s", time.asctime(time.localtime(time.time())))


  def connectionLost(self, reason):
    irc.IRCClient.connectionLost(self, reason)
    logging.info("Connection lost at: %s", time.asctime(time.localtime(time.time())))


  # callbacks for events

  def signedOn(self):
    """Called when bot has succesfully signed on to server."""
    self.join(self.channel)
    logging.info("Signed on at: %s", time.asctime(time.localtime(time.time())))


  def joined(self, channel):
    """This will get called when the bot joins the channel."""
    logging.info("Joined %s", channel)


  def privmsg(self, user, channel, input_message_raw):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]
    logging.info("Message received from %s: [%s] %s" % (channel, user, input_message_raw))

    output_messages = self.processor.process(channel, self.nickname, user, input_message_raw)

    for output_message in output_messages:
      self.msg(channel, output_message)


  def action(self, user, channel, input_message):
    """This will get called when the bot sees someone do an action."""
    user = user.split('!', 1)[0]
    logging.info("Action received from %s: [%s] %s", channel, user, input_message)


  # irc callbacks

  def irc_NICK(self, prefix, params):

    old_nick = prefix.split('!')[0]
    new_nick = params[0]
    self.processor.updateNick(old_nick, new_nick)



  # For fun, override the method that determines how a nickname is changed on
  # collisions. The default method appends an underscore.
  def alterCollidedNick(self, nickname):
    """
    Generate an altered version of a nickname that caused a collision in an
    effort to create an unused related name for subsequent registration.
    """
    alternative_nickname = nickname + '^'
    logging.warning("Nickname %s collided, using %s instead", nickname, alternative_nickname)
    return alternative_nickname


class ImpostorBotFactory(protocol.ClientFactory):

  USAGE = "Usage: %s <network> <channel> <logfile> <sourcedir>"
  CONNECTION_FAILED = "Connection failed: %s"

  def __init__(self, channel, log_filename, source_dir):
    self.channel = channel
    self.log_filename = log_filename
    self.source_dir = source_dir


  def buildProtocol(self, addr):
    p = ImpostorBot(self.source_dir, self.log_filename, self.channel)
    return p


  def clientConnectionLost(self, connector, reason):
    connector.connect()


  def clientConnectionFailed(self, connector, reason):
    print ImpostorBotFactory.CONNECTION_FAILED % reason
    reactor.stop()


if __name__ == '__main__':

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

