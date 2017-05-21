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

    self.user_collection = users.UserCollection()


  def test_init_empty(self):

    local_starters = []
    local_lookbacks = {}
    local_nick = "siucra"

    local_user = users.User(local_nick, local_starters, local_lookbacks)

    self.assertEqual(local_user.nick, local_nick)
    self.assertEquals(local_user.production_count, 0)
    self.assertEquals(len(local_user.aliases), 0)
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


  def test_get_statistics_alias(self):

    stats = self.user.getStatistics("limpet")

    alias_info = stats[users.UserStatisticType.ALIASES]
    self.assertEqual(alias_info.requested_nick, "limpet")


  def test_init_user_collection_empty(self):

    self.assertEqual(len(self.user_collection.usermap), 0)
    self.assertEqual(self.user_collection.count, 0)
    self.assertEqual(self.user_collection.biggest_users, None)
    self.assertEqual(self.user_collection.userset, None)
    self.assertEqual(self.user_collection.changes, 0)


  def test_build_source_empty(self):

    source_filename = "ash.src"
    source_material = []

    self.user_collection.buildSource(source_filename, source_material)

    self.assertEqual(len(self.user_collection.usermap), 0)


  def test_build_source_nonempty(self):

    nick = "birch"
    source_filename = nick + ".src"
    source_material = [
      "a b c d",
      "a b c e f g",
      "h i j k"
    ]
    starters = []
    lookbackmap = {}

    self.user_collection.buildSource(source_filename, source_material)

    self.assertEqual(len(self.user_collection.usermap), 1)
    self.assertTrue(self.user_collection.containsByAlias(nick))

    birch = self.user_collection.getByAlias(nick)
    self.assertEqual(birch.nick, nick)
    self.assertEqual(len(birch.starters), 3)
    self.assertTrue(("a", "b") in birch.starters)
    self.assertTrue(("h", "i") in birch.starters)
    self.assertEqual(birch.production_count, 8)
    self.assertEqual(len(birch.lookbacks[("a", "b")]), 2)
    self.assertEqual(len(birch.lookbacks[("b", "c")]), 2)
    self.assertFalse(("c", "d") in birch.lookbacks)
    self.assertEqual(len(birch.lookbacks[("c", "e")]), 1)


  def test_build_static_stats(self):

    coll_nick = "coll"
    coll_source_filename = coll_nick + ".src"
    coll_source_material = ["a b c"]

    dair_nick = "dair"
    dair_source_filename = dair_nick + ".src"
    dair_source_material = ["d e f g"]

    self.user_collection.buildSource(coll_source_filename, coll_source_material)
    self.user_collection.buildSource(dair_source_filename, dair_source_material)
    self.user_collection.initUserset()
    self.user_collection.buildStaticStats()

    self.assertTrue(self.user_collection.containsByAlias(coll_nick))
    self.assertTrue(self.user_collection.containsByAlias(dair_nick))

    biggest_users = self.user_collection.getBiggestUsers()
    self.assertEqual(self.user_collection.countUsers(), 2)
    self.assertNotEqual(biggest_users, None)
    self.assertEqual(len(biggest_users), 2)

    self.assertEqual(biggest_users[0].nick, dair_nick)
    self.assertEqual(biggest_users[0].count, 2)
    self.assertEqual(biggest_users[1].nick, coll_nick)
    self.assertEqual(biggest_users[1].count, 1)


  def test_build_merge_info(self):

    nick = "elm"
    source_filename = nick + ".src"
    source_material = ["a b c d e"]
    merge_info = [
      "elm\telm_\tleamhán",
      "fir\tfiralias",
    ]

    self.user_collection.buildSource(source_filename, source_material)
    self.user_collection.buildMergeInfo(merge_info)

    elm = self.user_collection.getByAlias(nick)
    self.assertTrue(len(elm.aliases), 2)
    self.assertTrue("elm_" in elm.aliases)
    self.assertTrue("leamhán" in elm.aliases)

    self.assertFalse(self.user_collection.containsByAlias("fir"))


if __name__ == "__main__":
  unittest.main()

