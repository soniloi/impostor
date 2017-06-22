# -*- coding: utf-8 -*-

import unittest

from .. import players

class TestUser(unittest.TestCase):

  def setUp(self):

    nick = "mollusc"
    self.player = players.Player(nick)


  def test_init(self):

    self.assertEqual(self.player.nick, "mollusc")
    self.assertEqual(self.player.last_played_ident, -1)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GAMES_PLAYED], 0)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GUESSES_INCORRECT], 0)
    self.assertEqual(self.player.scores[players.PlayerScoreType.GUESSES_CORRECT], 0)


if __name__ == "__main__":
  unittest.main()

