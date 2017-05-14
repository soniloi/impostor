import unittest

from .. import users

class TestUser(unittest.TestCase):

  def test_init(self):

    nick = "mollusc"

    tuple1 = ("the", "cat")
    follow1 = ["sat"]

    starters = [tuple1]
    lookbacks = {
      tuple1 : follow1
    }

    user = users.User(nick, starters, lookbacks)

    self.assertEqual(user.nick, nick)
    self.assertEquals(user.production_count, 1)


  def test_persisted_statistics(self):

    nick = "mollusc"

    tuple1 = ("the", "cat")
    follow1 = ["sat"]

    starters = [tuple1]
    lookbacks = {
      tuple1 : follow1
    }

    user = users.User(nick, starters, lookbacks)

    quotes_requested = 97
    stats_in = users.UserStatsToPersist(quotes_requested)
    user.setPersistedStatistics(stats_in)

    self.assertEqual(user.quotes_requested, quotes_requested)


if __name__ == "__main__":
  unittest.main()

