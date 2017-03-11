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

BOTDESC = " is a bot that impersonates people based on their history. Type '" + Config.TRIGGER + "<nick>' to see a line generated for a single user, '" + Config.TRIGGER + "random' for a line generated for a random user, or '" + Config.TRIGGER + "<nick1>" + Config.INPUT_NICKS_SEP + "<nick2>' to see a line generated from two users merged."

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

  def privmsg(self, user, channel, msg_in_raw):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]
    self.logger.log("<%s> %s" % (user, msg_in_raw))

    msg_in = msg_in_raw.strip().lower()
    
    # Ignore anything sent in private message
    if channel == self.nickname:
      return

    elif msg_in.startswith(Config.TRIGGER):
      rawtokens = re.split(' *', msg_in)
      tokens = re.split(Config.INPUT_NICKS_SEP, rawtokens[0][len(Config.TRIGGER):])

      nick = tokens[0]

      if Config.ALL_USED and Config.ALL_NICK in tokens:
        nick = Config.ALL_NICK # All subsumes all

      if nick == Config.RANDOM_NICK:
        nick = self.factory.generator.getRandomNick()

      notall = True
      if Config.ALL_USED:
        notall = nick != Config.ALL_NICK

      if nick == Config.BOT_NICK:
        msg_out = Config.BOT_NICK + BOTDESC
        self.msg(channel, msg_out)

      elif len(tokens) > 1 and notall:
        secondnick = tokens[1]

        if secondnick == Config.RANDOM_NICK:
          secondnick = self.factory.generator.getRandomNick()

        nickset = list(set([nick, secondnick]))

        nicks, imposting = self.factory.generator.generateMerged(nickset)
        if imposting:
          msg_out = Config.OUTPUT_NICKS_OPEN + nicks[0]
          for n in nicks[1:]:
            msg_out += Config.OUTPUT_NICKS_SEP + n
          msg_out += Config.OUTPUT_NICKS_CLOSE + imposting
          self.msg(channel, msg_out)

      else:
        imposting = self.factory.generator.generateSingle(nick)
        if imposting:
          msg_out = Config.OUTPUT_NICKS_OPEN + nick + Config.OUTPUT_NICKS_CLOSE + imposting
          self.msg(channel, msg_out)

    # Otherwise check to see if it is a message directed at me
    if msg_in.startswith(self.nickname + ":"):
      self.logger.log("<%s> %s" % (self.nickname, msg_in))

  def action(self, user, channel, msg_in):
    """This will get called when the bot sees someone do an action."""
    user = user.split('!', 1)[0]
    self.logger.log("* %s %s" % (user, msg_in))

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
  
