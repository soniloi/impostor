import mock
import unittest

from .. import generator


class TestGenerator(unittest.TestCase):

  def setUp(self):
    pass

  def test_init_empty(self):

    mock_users = mock.Mock()
    mock_meta = {}
    mock_time = 0

    local_generator = generator.Generator()
    local_generator.init(mock_users, mock_meta, mock_time)

    self.assertTrue(local_generator.empty())
    mock_users.empty.assert_called_once_with()


if __name__ == "__main__":
  unittest.main()

