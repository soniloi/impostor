# -*- coding: utf-8 -*-

import unittest

from .. import players

class TestUser(unittest.TestCase):

  def setUp(self):

    nick = "mollusc"
    self.player = players.Player(nick)

    self.players = players.PlayerCollection()


  def test_create_player(self):

    self.assertEqual(self.player.nick, "mollusc")
    self.assertEqual(self.player.last_played_ident, -1)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GAMES_PLAYED], 0)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GUESSES_INCORRECT], 0)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GUESSES_CORRECT], 0)


  def test_record_game_already_played(self):

    self.player.recordGame(-1)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GAMES_PLAYED], 0)


  def test_record_game_not_already_played(self):

    self.player.recordGame(0)
    self.player.recordGame(1)
    self.player.recordGame(53)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GAMES_PLAYED], 3)


  def test_create_players_empty(self):

    self.assertFalse(self.players.playermap)
    self.assertEqual(self.players.changes, 0)


if __name__ == "__main__":
  unittest.main()

