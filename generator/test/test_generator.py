import mock
from mock import patch
import unittest

from .. import generator
from .. import users

class TestGenerator(unittest.TestCase):

  def setUp(self):
    pass


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

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.countUsers.return_value = 0
      users_instance.getBiggestUsers.return_value = None
      users_instance.getMostQuoted.return_value = None

      local_generator.init(users_mock, meta, time)
      stats = local_generator.getGenericStatistics()

      self.assertTrue(generator.GenericStatisticType.USER_COUNT in stats)
      self.assertTrue(generator.GenericStatisticType.DATE_STARTED in stats)
      self.assertTrue(generator.GenericStatisticType.DATE_GENERATED in stats)
      self.assertTrue(generator.GenericStatisticType.SOURCE_CHANNELS in stats)
      self.assertTrue(generator.GenericStatisticType.BIGGEST_USERS in stats)
      self.assertTrue(generator.GenericStatisticType.MOST_QUOTED_USERS in stats)

      self.assertEqual(stats[generator.GenericStatisticType.DATE_STARTED], time)
      self.assertEqual(stats[generator.GenericStatisticType.DATE_GENERATED], None)

      source_channels = stats[generator.GenericStatisticType.SOURCE_CHANNELS]
      self.assertFalse(source_channels.primary)
      self.assertFalse(source_channels.additionals)


if __name__ == "__main__":
  unittest.main()

