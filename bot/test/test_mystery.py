# -*- coding: utf-8 -*-

import unittest

from bot.mystery import HintType
from bot.mystery import Mystery


class TestMystery(unittest.TestCase):

  def setUp(self):

    ident = 13
    author = "mollusc"
    author_aliases = ["limpet"]
    initial_quote = "Hello"
    hints = [
      (HintType.NICK_CHARACTER, "o"),
      (HintType.ADDITIONAL_QUOTE, "Carpe diem"),
      (HintType.NICK_CHARACTER, "s"),
      (HintType.NICK_CHARACTER, "l"),
    ]
    self.mystery = Mystery(ident, author, author_aliases, initial_quote, hints)


  def test_get_hint(self):

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], HintType.NICK_CHARACTER)
    self.assertEqual(hint[1], "o")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], HintType.ADDITIONAL_QUOTE)
    self.assertEqual(hint[1], "Carpe diem")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], HintType.NICK_CHARACTER)
    self.assertEqual(hint[1], "s")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], HintType.NICK_CHARACTER)
    self.assertEqual(hint[1], "l")

    hint = self.mystery.getHint()
    self.assertIsNone(hint)


  def test_guess_incorrect(self):

    author_nick = self.mystery.guess("notmollusc")
    self.assertEqual(author_nick, None)


  def test_guess_correct_non_alias(self):

    author_nick = self.mystery.guess("mollusc")
    self.assertEqual(author_nick, "mollusc")


  def test_guess_correct_alias(self):

    author_nick = self.mystery.guess("limpet")
    self.assertEqual(author_nick, "mollusc")


if __name__ == "__main__":
  unittest.main()

