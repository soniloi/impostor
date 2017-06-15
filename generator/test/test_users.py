# -*- coding: utf-8 -*-

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

    self.captured_nick = "whoever"


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

    nick = "ash"
    source_filename = TestUser.mkSourceFilename(nick)
    source_material = []

    self.user_collection.buildSource(source_filename, source_material)

    self.assertTrue(self.user_collection.empty())


  def test_build_source_nonempty(self):

    nick = "birch"
    source_filename = TestUser.mkSourceFilename(nick)
    source_material = [
      "a b c d",
      "a b c e f g",
      "h i j k"
    ]

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
    self.createAndAddUser(coll_nick, ["a b c"])
    dair_nick = "dair"
    self.createAndAddUser(dair_nick, ["d e f g"])

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

    elm_nick = "elm"
    self.createAndAddUser(elm_nick)
    fir_nick = "fir"
    self.createAndAddUser(fir_nick)

    merge_info = [
      "elm\telm_\tleamhán",
      "fir",
      "grape\tgrapealias",
    ]

    self.user_collection.buildMergeInfo(merge_info)

    elm = self.user_collection.getByAlias(elm_nick)
    self.assertEqual(len(elm.aliases), 2)
    self.assertTrue("elm_" in elm.aliases)
    self.assertTrue("leamhán" in elm.aliases)

    fir = self.user_collection.getByAlias(fir_nick)
    self.assertEqual(len(fir.aliases), 0)

    self.assertFalse(self.user_collection.containsByAlias("grape"))


  def test_build_user_stats_unknown(self):

    grape_nick = "grape"
    grape_quotes_requested = 117

    stats_data = {
      grape_nick : users.UserStatsToPersist(grape_quotes_requested),
    }

    self.user_collection.buildUserStats(stats_data)
    self.assertTrue(self.user_collection.empty())


  def test_build_user_stats_known(self):

    grape_nick = "grape"
    grape_quotes_requested = 119

    hazel_nick = "hazel"
    self.createAndAddUser(hazel_nick)
    hazel_quotes_requested = 711

    stats_data = {
      grape_nick : users.UserStatsToPersist(grape_quotes_requested),
      hazel_nick : users.UserStatsToPersist(hazel_quotes_requested),
    }

    self.user_collection.buildUserStats(stats_data)
    self.assertFalse(self.user_collection.containsByAlias(grape_nick))
    self.assertTrue(self.user_collection.containsByAlias(hazel_nick))

    hazel = self.user_collection.getByAlias(hazel_nick)
    hazel_stats = hazel.getStatistics(hazel_nick)
    hazel_quotes_requested = hazel_stats[users.UserStatisticType.QUOTES_REQUESTED]
    self.assertEqual(hazel_quotes_requested, hazel_quotes_requested)


  def test_get_most_quoted_empty(self):

    most_quoted = self.user_collection.getMostQuoted()
    self.assertFalse(most_quoted)


  def test_get_most_quoted_nonempty(self):

    iris_nick = "iris"
    self.createAndAddUser(iris_nick)
    iris_quotes_requested = 784

    juniper_nick = "juniper"
    self.createAndAddUser(juniper_nick)
    juniper_quotes_requested = 2991

    kale_nick = "kale"
    self.createAndAddUser(kale_nick)
    kale_quotes_requested = 0

    stats_data = {
        iris_nick : users.UserStatsToPersist(iris_quotes_requested),
        juniper_nick : users.UserStatsToPersist(juniper_quotes_requested),
        kale_nick : users.UserStatsToPersist(kale_quotes_requested),
    }

    self.user_collection.buildUserStats(stats_data)
    self.user_collection.initUserset()

    most_quoted = self.user_collection.getMostQuoted()
    self.assertEqual(len(most_quoted), 2)
    self.assertEqual(most_quoted[0].nick, juniper_nick)
    self.assertEqual(most_quoted[0].count, juniper_quotes_requested)
    self.assertEqual(most_quoted[1].nick, iris_nick)
    self.assertEqual(most_quoted[1].count, iris_quotes_requested)


  def test_get_user_aliases_unknown(self):

    aliases = self.user_collection.getUserAliases("unknown")
    self.assertFalse(aliases)


  def test_get_user_aliases_no_aliases(self):

    self.createAndAddUser(self.captured_nick)

    aliases = self.user_collection.getUserAliases(self.captured_nick)
    self.assertFalse(aliases)


  def test_get_user_aliases_with_aliases(self):

    self.createAndAddUser(self.captured_nick)
    merge_info = [self.captured_nick + "\tmaple_\tmaple-\tmailp"]
    self.user_collection.buildMergeInfo(merge_info)

    aliases = self.user_collection.getUserAliases(self.captured_nick)
    self.assertTrue(len(aliases), 3)
    self.assertTrue("maple_" in aliases)
    self.assertTrue("maple-" in aliases)
    self.assertTrue("mailp" in aliases)


  def test_get_random_nick_no_minimum_starters(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    random_nick = self.user_collection.getRandomNick([])
    self.assertEqual(random_nick, self.captured_nick)


  def test_get_random_nick_equal_minimum_starters(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    random_nick = self.user_collection.getRandomNick([], 1)
    self.assertEqual(random_nick, self.captured_nick)


  def test_get_random_nick_insufficient_minimum_starters(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    random_nick = self.user_collection.getRandomNick([], 2)
    self.assertEqual(random_nick, None)


  def test_get_random_nick_with_exclude(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    random_nick = self.user_collection.getRandomNick([self.captured_nick])
    self.assertEqual(random_nick, None)


  def test_get_real_nicks_no_minimum_starters(self):

    nonexistent_nick = "nonexistent"
    known_existent_nick = "known"
    unknown_existent_nick = "unknown"

    self.createAndAddUser(known_existent_nick)
    self.createAndAddUser(unknown_existent_nick)
    self.user_collection.initUserset()

    nonexistent_nick_tuple = (users.NickType.NONRANDOM, nonexistent_nick)
    known_existent_nick_tuple = (users.NickType.NONRANDOM, known_existent_nick)
    unknown_existent_nick_tuple = (users.NickType.RANDOM, "")
    nick_tuples = [
      nonexistent_nick_tuple,
      known_existent_nick_tuple,
      unknown_existent_nick_tuple,
    ]

    real_nicks = self.user_collection.getRealNicks(nick_tuples)

    self.assertEqual(len(real_nicks), 2)
    self.assertFalse(nonexistent_nick in real_nicks)
    self.assertTrue(known_existent_nick in real_nicks)
    self.assertTrue(unknown_existent_nick in real_nicks)

    known_user = self.user_collection.getByAlias(known_existent_nick)
    unknown_user = self.user_collection.getByAlias(unknown_existent_nick)

    self.assertEqual(known_user.quotes_requested, 1)
    self.assertEqual(unknown_user.quotes_requested, 0)


  def test_get_real_nicks_no_known_duplication(self):

    known_existent_nick = "known"

    self.createAndAddUser(known_existent_nick)
    self.user_collection.initUserset()

    known_existent_nick_tuple = (users.NickType.NONRANDOM, known_existent_nick)
    unknown_existent_nick_tuple = (users.NickType.RANDOM, "")
    nick_tuples = [
      known_existent_nick_tuple,
      unknown_existent_nick_tuple,
    ]

    real_nicks = self.user_collection.getRealNicks(nick_tuples)

    self.assertEqual(len(real_nicks), 1)
    self.assertTrue(known_existent_nick in real_nicks)


  def test_get_real_nicks_no_unknown_duplication(self):

    unknown_existent_nick = "unknown"

    self.createAndAddUser(unknown_existent_nick)
    self.user_collection.initUserset()

    unknown_existent_nick_tuple_1 = (users.NickType.RANDOM, "")
    unknown_existent_nick_tuple_2 = (users.NickType.RANDOM, "")
    nick_tuples = [
      unknown_existent_nick_tuple_1,
      unknown_existent_nick_tuple_2,
    ]

    real_nicks = self.user_collection.getRealNicks(nick_tuples)

    self.assertEqual(len(real_nicks), 1)
    self.assertTrue(unknown_existent_nick in real_nicks)


  def test_get_real_nicks_insufficient_minimum_starters(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    nick_tuple = (users.NickType.RANDOM, "")
    nick_tuples = [nick_tuple]

    real_nicks = self.user_collection.getRealNicks(nick_tuples, 2)

    self.assertFalse(real_nicks)


  def test_get_real_nicks_no_increment(self):

    known_existent_nick = "known"
    self.createAndAddUser(known_existent_nick)
    self.user_collection.initUserset()

    nick_tuple = (users.NickType.NONRANDOM, known_existent_nick)
    nick_tuples = [nick_tuple]

    real_nicks = self.user_collection.getRealNicks(nick_tuples, 0, False)

    self.assertTrue(real_nicks)
    self.assertEqual(len(real_nicks), 1)
    self.assertTrue(known_existent_nick in real_nicks)

    known_user = self.user_collection.getByAlias(known_existent_nick)
    self.assertEqual(known_user.quotes_requested, 0)


  def test_get_user_statistics_user_absent(self):

    self.user_collection.initUserset()

    stats = self.user_collection.getUserStatistics("no-one")

    self.assertEqual(stats, None)


  def test_get_user_statistics_user_present(self):

    self.createAndAddUser(self.captured_nick)
    self.user_collection.initUserset()

    stats = self.user_collection.getUserStatistics(self.captured_nick)

    self.assertTrue(stats)
    self.assertEqual(stats[users.UserStatisticType.REAL_NICK], self.captured_nick)
    self.assertEqual(stats[users.UserStatisticType.ALIASES], None)
    self.assertEqual(stats[users.UserStatisticType.PRODUCTION_COUNT], 3)
    self.assertEqual(stats[users.UserStatisticType.QUOTES_REQUESTED], 0)


  def createAndAddUser(self, nick, source_material=["a b c d e"]):

    source_filename = TestUser.mkSourceFilename(nick)
    self.user_collection.buildSource(source_filename, source_material)


  @staticmethod
  def mkSourceFilename(nick):
    return nick + ".src"


if __name__ == "__main__":
  unittest.main()

