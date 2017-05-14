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


if __name__ == "__main__":
  unittest.main()

