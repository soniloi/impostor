import mock
from mock import patch
import unittest

from .. import config
from .. import generator
from .. import users

class TestGenerator(unittest.TestCase):

  def setUp(self):

    self.rain_nick = "rain"
    self.aliases = {
      self.rain_nick : ["rain_", "fearthainn"],
    }
    self.stats = {
      self.rain_nick : "statistics",
    }

    self.saoi_nick = "saoi"
    self.file_nick = "file"

    self.quotes = {
      self.saoi_nick : "is glas iad na cnoic i bhfad uainn",
      self.file_nick : "marbh le tae agus marbh gan é",
    }

    self.starters = {}
    self.lookbacks = {}

    for (nick, quote) in self.quotes.iteritems():

      self.starters[nick] = []
      self.lookbacks[nick] = {}
      words = quote.split()

      starter = (words[0], words[1])
      self.starters[nick].append(starter)

      for i in range(0, len(words)-2):

        predecessor = (words[i], words[i+1])
        successor = words[i+2]

        if not predecessor in self.lookbacks[nick]:
          self.lookbacks[nick][predecessor] = []

        self.lookbacks[nick][predecessor].append(successor)


  def aliases_side_effect(self, *args):

    nick = args[0]

    if nick in self.aliases:
      return self.aliases[nick]

    return []


  def stats_side_effect(self, *args):

    nick = args[0]

    if nick in self.stats:
      return self.stats[nick]

    return None


  def starters_side_effect(self, *args):

    nick = args[0]

    if nick in self.starters:
      return self.starters[nick]

    return []


  def lookbacks_side_effect(self, *args):

    nick = args[0]

    if nick in self.lookbacks:
      return self.lookbacks[nick]

    return {}


  def test_copy_list_dict(self):

    rain_key = "rain"

    focloir = {
      rain_key : ["fearthainn", "báisteach"],
    }

    copy = generator.GeneratorUtil.copyListDict(focloir)

    self.assertTrue(copy)
    self.assertEqual(copy, focloir)

    # Check that the list is new
    self.assertFalse(copy[rain_key] is focloir[rain_key])

    # Check that the list elements are not new
    for i in range(0, len(copy[rain_key])):
      self.assertTrue(copy[rain_key][i] is focloir[rain_key][i])


  def test_merge_into_dictionary_no_matching_keys(self):

    tree_key = "tree"
    tree_value = ["crann"]

    rain_key = "rain"
    rain_value = ["báisteach"]

    focloir1 = {
      tree_key : tree_value,
    }

    focloir2 = {
      rain_key : rain_value,
    }

    generator.GeneratorUtil.mergeIntoDictionary(focloir1, focloir2)

    # Ensure first dictionary has been mutated correctly
    self.assertEqual(len(focloir1), 2)
    self.assertTrue(tree_key in focloir1)
    self.assertTrue(rain_key in focloir1)
    self.assertEqual(focloir1[tree_key], tree_value)
    self.assertEqual(focloir1[rain_key], rain_value)

    self.assertTrue(focloir1[tree_key] is tree_value)
    self.assertTrue(focloir1[rain_key] is not rain_value)
    self.assertTrue(focloir1[rain_key][0] is rain_value[0])

    # Ensure second dictionary is unchanged
    self.assertEqual(len(focloir2), 1)
    self.assertTrue(rain_key in focloir2)

    self.assertEqual(len(focloir2[rain_key]), 1)
    self.assertTrue(focloir2[rain_key] is rain_value)
    self.assertTrue(focloir2[rain_key][0] is rain_value[0])


  def test_merge_into_dictionary_with_matching_keys(self):

    rain_key = "rain"
    rain_elem1 = "fearthainn"
    rain_elem2 = "báisteach"
    rain_value1 = [rain_elem1]
    rain_value2 = [rain_elem2]

    focloir1 = {
      rain_key : rain_value1,
    }

    focloir2 = {
      rain_key : rain_value2,
    }

    generator.GeneratorUtil.mergeIntoDictionary(focloir1, focloir2)

    # Ensure first dictionary has been mutated correctly
    self.assertEqual(len(focloir1), 1)
    self.assertTrue(rain_key in focloir1)
    self.assertEqual(focloir1[rain_key], [rain_elem1, rain_elem2])

    self.assertTrue(focloir1[rain_key] is rain_value1)
    self.assertTrue(focloir1[rain_key][0] is rain_value1[0])
    self.assertTrue(focloir1[rain_key][1] is rain_value2[0])

    # Ensure second dictionary is unchanged
    self.assertEqual(len(focloir2), 1)
    self.assertTrue(rain_key in focloir2)

    self.assertEqual(len(focloir2[rain_key]), 1)
    self.assertTrue(rain_key in focloir2)
    self.assertTrue(focloir2[rain_key] is rain_value2)
    self.assertTrue(focloir2[rain_key][0] is rain_value2[0])


  def test_init_empty(self):

    local_generator = generator.Generator()

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.empty.return_value = True

      local_generator.init(users_instance, {}, 0)
      self.assertTrue(local_generator.empty())


  def test_get_generic_statistics_empty(self):

    local_generator = generator.Generator()

    meta = {}
    time = 0
    user_count = 0

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.countUsers.return_value = user_count
      users_instance.getBiggestUsers.return_value = None
      users_instance.getMostQuoted.return_value = None

      local_generator.init(users_instance, meta, time)
      stats = local_generator.getGenericStatistics()

      self.assertTrue(generator.GenericStatisticType.USER_COUNT in stats)
      self.assertTrue(generator.GenericStatisticType.DATE_STARTED in stats)
      self.assertTrue(generator.GenericStatisticType.DATE_GENERATED in stats)
      self.assertTrue(generator.GenericStatisticType.SOURCE_CHANNELS in stats)
      self.assertTrue(generator.GenericStatisticType.BIGGEST_USERS in stats)
      self.assertTrue(generator.GenericStatisticType.MOST_QUOTED_USERS in stats)

      self.assertEqual(stats[generator.GenericStatisticType.USER_COUNT], user_count)
      self.assertEqual(stats[generator.GenericStatisticType.DATE_STARTED], time)
      self.assertEqual(stats[generator.GenericStatisticType.DATE_GENERATED], None)

      source_channels = stats[generator.GenericStatisticType.SOURCE_CHANNELS]
      self.assertEqual(source_channels.primary, None)
      self.assertFalse(source_channels.additionals)

      self.assertEqual(stats[generator.GenericStatisticType.BIGGEST_USERS], None)
      self.assertEqual(stats[generator.GenericStatisticType.MOST_QUOTED_USERS], None)


  def test_get_generic_statistics_nonempty(self):

    local_generator = generator.Generator()

    primary = "#ocean"
    additional = ["#pond", "#sea", "#lake"]

    meta = {
      config.META_PRIMARY: [primary],
      config.META_ADDITIONAL: additional,
    }

    time = 97
    user_count = 3

    user_nick_1 = "ailm"
    user_nick_2 = "beith"
    user_nick_3 = "coll"

    big_users = [
      users.NickAndCount(user_nick_1, 79),
      users.NickAndCount(user_nick_1, 23),
      users.NickAndCount(user_nick_1, 11),
    ]

    quoted_users = [
      users.NickAndCount(user_nick_3, 346),
      users.NickAndCount(user_nick_1, 129),
      users.NickAndCount(user_nick_2, 62),
    ]

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.countUsers.return_value = user_count
      users_instance.getBiggestUsers.return_value = big_users
      users_instance.getMostQuoted.return_value = quoted_users

      local_generator.init(users_instance, meta, time)
      stats = local_generator.getGenericStatistics()

      self.assertEqual(stats[generator.GenericStatisticType.USER_COUNT], user_count)
      self.assertEqual(stats[generator.GenericStatisticType.DATE_STARTED], time)
      self.assertEqual(stats[generator.GenericStatisticType.DATE_GENERATED], None)

      source_channels = stats[generator.GenericStatisticType.SOURCE_CHANNELS]
      self.assertEqual(source_channels.primary, primary)
      self.assertEqual(source_channels.additionals, tuple(additional))

      self.assertEqual(stats[generator.GenericStatisticType.BIGGEST_USERS], big_users)
      self.assertEqual(stats[generator.GenericStatisticType.MOST_QUOTED_USERS], quoted_users)


  def test_get_user_aliases(self):

    local_generator = generator.Generator()

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getUserAliases.side_effect = self.aliases_side_effect

      local_generator.init(users_instance, {}, 0)
      aliases = local_generator.getUserAliases(self.rain_nick)

      self.assertEqual(aliases, self.aliases[self.rain_nick])
      self.assertTrue(aliases is self.aliases[self.rain_nick])


  def test_get_user_statistics_unknown(self):

    local_generator = generator.Generator()

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getUserStatistics.side_effect = self.stats_side_effect

      local_generator.init(users_instance, {}, 0)
      stats = local_generator.getUserStatistics("unknown")
      self.assertEqual(stats, None)


  def test_get_user_statistics_known(self):

    local_generator = generator.Generator()

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getUserStatistics.side_effect = self.stats_side_effect

      local_generator.init(users_instance, {}, 0)
      stats = local_generator.getUserStatistics(self.rain_nick)

      self.assertTrue(stats)
      self.assertEqual(stats, self.stats[self.rain_nick])
      self.assertTrue(stats is self.stats[self.rain_nick])


  def test_generate_nonrandom_unknown(self):

    local_generator = generator.Generator()

    meta = {}
    time = 0

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getRealNicks.return_value = []

      local_generator.init(users_instance, meta, time)
      nicks, quote = local_generator.generate([])

      self.assertFalse(nicks)
      self.assertFalse(quote)


  def test_generate_nonrandom_known_single(self):

    local_generator = generator.Generator()

    meta = {}
    time = 0

    nick_tuples = [(users.NickType.NONRANDOM, self.saoi_nick)]

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getRealNicks.return_value = [self.saoi_nick]
      users_instance.getStarters.side_effect = self.starters_side_effect
      users_instance.getLookbacks.side_effect = self.lookbacks_side_effect

      local_generator.init(users_instance, meta, time)
      nicks, quote = local_generator.generate(nick_tuples)

      self.assertEqual(nicks[0], self.saoi_nick)
      self.assertEqual(quote, self.quotes[self.saoi_nick])


  def test_generate_nonrandom_known_multiple(self):

    local_generator = generator.Generator()

    meta = {}
    time = 0

    nick_tuples = [
      (users.NickType.NONRANDOM, self.saoi_nick),
      (users.NickType.NONRANDOM, self.file_nick),
    ]

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.getRealNicks.return_value = [self.saoi_nick, self.file_nick]
      users_instance.getStarters.side_effect = self.starters_side_effect
      users_instance.getLookbacks.side_effect = self.lookbacks_side_effect

      local_generator.init(users_instance, meta, time)
      nicks, quote = local_generator.generate(nick_tuples)

      self.assertTrue(nicks)
      self.assertTrue(self.saoi_nick in nicks)
      self.assertTrue(self.file_nick in nicks)
      self.assertTrue(quote in self.quotes.values())


if __name__ == "__main__":
  unittest.main()

