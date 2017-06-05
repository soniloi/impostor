import mock
from mock import patch
import unittest

from .. import generator
from .. import users

class TestGenerator(unittest.TestCase):

  def setUp(self):
    pass


  def test_init_empty(self):

    with patch(users.__name__ + ".UserCollection") as users_mock:

      users_instance = users_mock.return_value
      users_instance.empty.return_value = True

      mock_meta = {}
      mock_time = 0

      local_generator = generator.Generator()
      local_generator.init(users_instance, mock_meta, mock_time)
      self.assertTrue(local_generator.empty())


if __name__ == "__main__":
  unittest.main()

