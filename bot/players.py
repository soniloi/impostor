from collections import namedtuple
import os
import pickle

import config


PlayerScoresToPersist = namedtuple("PlayerScoresToPersist", "games_played, guesses_incorrect, guesses_correct")


class PlayerScoreType:
  GAMES_PLAYED = 0
  GUESSES_CORRECT = 1
  GUESSES_INCORRECT = 2
  ALL_TYPES = [GAMES_PLAYED, GUESSES_CORRECT, GUESSES_INCORRECT]


class Player:

  def __init__(self, nick):

    self.nick = nick
    self.last_played_ident = -1
    self.scores = {}

    for score_type in PlayerScoreType.ALL_TYPES:
      self.scores[score_type] = 0


  def incrementScore(self, score_type):
    self.scores[score_type] += 1


  def recordGame(self, ident):
    if ident != self.last_played_ident:
      self.scores[PlayerScoreType.GAMES_PLAYED] += 1
      self.last_played_ident = ident


  def getScore(self):
    return( \
       self.scores[PlayerScoreType.GAMES_PLAYED], \
       self.scores[PlayerScoreType.GUESSES_INCORRECT], \
       self.scores[PlayerScoreType.GUESSES_CORRECT]
    )


  def getStatisticsToPersist(self):
    return PlayerScoresToPersist( \
      self.scores[PlayerScoreType.GAMES_PLAYED], \
      self.scores[PlayerScoreType.GUESSES_INCORRECT], \
      self.scores[PlayerScoreType.GUESSES_CORRECT])


  def setScores(self, scores):
    self.scores[PlayerScoreType.GAMES_PLAYED] = scores.games_played
    self.scores[PlayerScoreType.GUESSES_INCORRECT] = scores.guesses_incorrect
    self.scores[PlayerScoreType.GUESSES_CORRECT] = scores.guesses_correct


class PlayerCollection:

  def __init__(self):
    self.playermap = {} # Map of nick to Player objects
    self.changes = 0


  def init(self):
    self.loadPlayerScores()


  def loadPlayerScores(self):

    filename = config.STATS_FILE_NAME

    if not os.path.isfile(filename):
      return

    data = pickle.load(open(filename, "rb"))

    try:

      data = pickle.load(open(filename, "rb"))

      for (nick, scores) in data.iteritems():
        self.playermap[nick] = Player(nick)
        self.playermap[nick].setScores(scores)

    except:

      print "Error reading or parsing player scores file %s. Bot will start, but previous scores may not be correctly loaded. " \
             % filename


  def updateNick(self, old_nick, new_nick):

    if old_nick in self.playermap:
      player = self.playermap[old_nick]
      player.nick = new_nick
      self.playermap[new_nick] = player
      del self.playermap[old_nick]


  def getOrCreatePlayer(self, nick):

    if not nick in self.playermap:
      self.playermap[nick] = Player(nick)

    return self.playermap[nick]


  def updateChanges(self):

    self.changes += 1

    if self.changes >= config.CHANGES_BETWEEN_STATS_PERSISTENCE:
      self.savePlayerScores()
      self.changes = 0


  def savePlayerScores(self):

    data = {}

    for (nick, player) in self.playermap.iteritems():
      data[nick] = player.getStatisticsToPersist()

    pickle.dump(data, open(config.STATS_FILE_NAME, "wb"))


  def getGenericScore(self):

    if not self.playermap.values():
      return None

    top_players = {}
    all_players = self.playermap.values()

    for score_type in PlayerScoreType.ALL_TYPES:
      top_players[score_type] = all_players[0]

    for player in all_players[1:]:
      for score_type in PlayerScoreType.ALL_TYPES:
        if player.scores[score_type] > top_players[score_type].scores[score_type]:
          top_players[score_type] = player

    most_games_player = top_players[PlayerScoreType.GAMES_PLAYED]
    most_incorrect_player = top_players[PlayerScoreType.GUESSES_INCORRECT];
    most_correct_player = top_players[PlayerScoreType.GUESSES_CORRECT];

    return (most_games_player.nick, \
            most_games_player.scores[PlayerScoreType.GAMES_PLAYED], \
            most_incorrect_player.nick, \
            most_incorrect_player.scores[PlayerScoreType.GUESSES_INCORRECT], \
            most_correct_player.nick, \
            most_correct_player.scores[PlayerScoreType.GUESSES_CORRECT])


  def getPlayerScore(self, nick):

    if not nick in self.playermap:
      return None

    return self.playermap[nick].getScore()

