# -*- coding: utf-8 -*-

import unittest

from .. import mystery

class TestMystery(unittest.TestCase):

  def setUp(self):

    ident = 13
    author = "mollusc"
    author_aliases = ["limpet"]
    initial_quote = "Hello"
    hints = [
      (mystery.HintType.NICK_CHARACTER, "o"),
      (mystery.HintType.ADDITIONAL_QUOTE, "Carpe diem"),
      (mystery.HintType.NICK_CHARACTER, "s"),
      (mystery.HintType.NICK_CHARACTER, "l"),
    ]
    self.mystery = mystery.Mystery(ident, author, author_aliases, initial_quote, hints)


  def test_get_hint(self):

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], mystery.HintType.NICK_CHARACTER)
    self.assertEqual(hint[1], "o")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], mystery.HintType.ADDITIONAL_QUOTE)
    self.assertEqual(hint[1], "Carpe diem")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], mystery.HintType.NICK_CHARACTER)
    self.assertEqual(hint[1], "s")

    hint = self.mystery.getHint()
    self.assertEqual(hint[0], mystery.HintType.NICK_CHARACTER)
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

