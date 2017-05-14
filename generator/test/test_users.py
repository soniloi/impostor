import unittest

from .. import users

class TestUser(unittest.TestCase):

  def setUp(self):

    nick = "mollusc"

    tuple1 = ("the", "cat")
    follow1 = ["sat"]

    tuple2 = ("cat", "sat")
    follow2 = ["on"]

    tuple3 = ("sat", "on")
    follow3 = ["the"]

    tuple4 = ("on", "the")
    follow4 = ["mat", "doorstep"]

    starters = [tuple1]
    lookbacks = {
      tuple1 : follow1,
      tuple2 : follow2,
      tuple3 : follow3,
      tuple4 : follow4,
    }

    self.user = users.User(nick, starters, lookbacks)


  def test_init_empty(self):

    local_starters = []
    local_lookbacks = {}
    local_nick = "siucra"

    local_user = users.User(local_nick, local_starters, local_lookbacks)

    self.assertEqual(local_user.nick, local_nick)
    self.assertEquals(local_user.production_count, 0)


  def test_init_populated(self):

    self.assertEqual(self.user.nick, "mollusc")
    self.assertEquals(self.user.production_count, 5)


  def test_persisted_statistics(self):

    quotes_requested = 97
    stats_in = users.UserStatsToPersist(quotes_requested)
    self.user.setPersistedStatistics(stats_in)

    self.assertEqual(self.user.quotes_requested, quotes_requested)


if __name__ == "__main__":
  unittest.main()

