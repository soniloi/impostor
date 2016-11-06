import re
from Config import Config
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

TRIGGER = '!' # Character that must appear at the start of a message in order to trigger the bot
BOTNICK = 'impostor'
RANDNICK = 'random' # Word that will trigger a random user to be 'quoted'
ALLNICK = 'all' # Request for a line generated from all users merged
NOPEN = '[' # Character(s) before a nick(s)
NSEP = ':' # Character(s) between output nicks
NCLOSE = '] ' # Character(s) after nick(s)
NICK_SPLIT = ':' # Character(s) used to split input nicks
BOTDESC = " is a bot that impersonates people based on their history. Type '" + TRIGGER + "<nick>' to see a line generated for a single user, '" + TRIGGER + "random' for a line generated for a random user, or '" + TRIGGER + "<nick1>" + NICK_SPLIT + "<nick2>' to see a line generated from two users merged."

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
  
  nickname = BOTNICK
  
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

  def privmsg(self, user, channel, msg):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]
    self.logger.log("<%s> %s" % (user, msg))
    
    # Ignore anything sent in private message
    if channel == self.nickname:
      return

    elif msg.startswith(TRIGGER):
      rawtokens = re.split(' *', msg.strip())
      tokens = re.split(NICK_SPLIT, rawtokens[0][len(TRIGGER):])

      nick = tokens[0].lower()

      if ALLNICK in tokens:
        nick = ALLNICK # All subsumes all

      elif nick == RANDNICK:
        nick = self.factory.generator.getRandomNick()

      if nick == BOTNICK:
        msg = BOTNICK + BOTDESC
        self.msg(channel, msg)

      elif len(tokens) > 1 and nick != ALLNICK:
        secondnick = tokens[1].lower()

        if secondnick == RANDNICK:
          secondnick = self.factory.generator.getRandomNick()

        nickset = list(set([nick, secondnick]))

        nicks, imposting = self.factory.generator.generateMerged(nickset)
        if imposting:
          msg = NOPEN + nicks[0]
          for n in nicks[1:]:
            msg += NSEP + n
          msg += NCLOSE + imposting
          self.msg(channel, msg)

      else:
        imposting = self.factory.generator.generateSingle(nick)
        if imposting:
          msg = NOPEN + nick + NCLOSE + imposting
          self.msg(channel, msg)

    # Otherwise check to see if it is a message directed at me
    if msg.startswith(self.nickname + ":"):
      self.logger.log("<%s> %s" % (self.nickname, msg))

  def action(self, user, channel, msg):
    """This will get called when the bot sees someone do an action."""
    user = user.split('!', 1)[0]
    self.logger.log("* %s %s" % (user, msg))

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
  
