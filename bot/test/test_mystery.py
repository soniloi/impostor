# -*- coding: utf-8 -*-

import unittest

from .. import mystery

class TestMystery(unittest.TestCase):

  def setUp(self):

    ident = 13
    author = "mollusc"
    author_aliases = ["limpet"]
    initial_quote = "Hello"
    hints = []
    self.mystery = mystery.Mystery(ident, author, author_aliases, initial_quote, hints)


  def guess_incorrect():

    author_nick = self.mystery.guess("notmollusc")
    self.assertEqual(author_nick, None)


  def guess_correct_non_alias():

    author_nick = self.mystery.guess("mollusc")
    self.assertEqual(author_nick, "mollusc")


  def guess_correct_alias():

    author_nick = self.mystery.guess("limpet")
    self.assertEqual(author_nick, "mollusc")


if __name__ == "__main__":
  unittest.main()

