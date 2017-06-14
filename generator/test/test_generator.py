import mock
from mock import patch
import unittest

from .. import config
from .. import generator
from .. import users

class TestGenerator(unittest.TestCase):

  def setUp(self):

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

