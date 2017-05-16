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

    self.user.initAliases(["squid", "limpet"])

    requested = 7
    for i in range(0, requested):
      self.user.incrementQuotesRequested()


  def test_init_empty(self):

    local_starters = []
    local_lookbacks = {}
    local_nick = "siucra"

    local_user = users.User(local_nick, local_starters, local_lookbacks)

    self.assertEqual(local_user.nick, local_nick)
    self.assertEquals(local_user.production_count, 0)
    self.assertEquals(local_user.aliases, None)
    self.assertEqual(local_user.production_count, 0)
    self.assertEqual(local_user.quotes_requested, 0)


  def test_init_populated(self):

    self.assertEqual(self.user.nick, "mollusc")
    self.assertEquals(self.user.production_count, 5)
    self.assertEquals(len(self.user.aliases), 2)
    self.assertTrue("limpet" in self.user.aliases)
    self.assertTrue("squid" in self.user.aliases)
    self.assertEqual(self.user.production_count, 5)
    self.assertEqual(self.user.quotes_requested, 7)


  def test_persisted_statistics(self):

    quotes_requested = 97
    stats_in = users.UserStatsToPersist(quotes_requested)
    self.user.setPersistedStatistics(stats_in)

    self.assertEqual(self.user.quotes_requested, quotes_requested)


  def test_get_statistics_canonical_nick(self):

    stats = self.user.getStatistics("mollusc")
    real_nick = stats[users.UserStatisticType.REAL_NICK]
    alias_info = stats[users.UserStatisticType.ALIASES]
    production_count = stats[users.UserStatisticType.PRODUCTION_COUNT]
    quotes_requested = stats[users.UserStatisticType.QUOTES_REQUESTED]
    aliases = alias_info.aliases
    requested_nick = alias_info.requested_nick

    self.assertEqual(real_nick, "mollusc")
    self.assertEqual(len(aliases), 2)
    self.assertTrue("limpet" in aliases)
    self.assertTrue("squid" in aliases)
    self.assertEqual(requested_nick, None)
    self.assertEqual(production_count, 5)
    self.assertEqual(quotes_requested, 7)


if __name__ == "__main__":
  unittest.main()

